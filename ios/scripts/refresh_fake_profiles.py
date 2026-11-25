#!/usr/bin/env python3
"""Extend ExpirationDate on Telegram-iOS fake-codesigning profiles and re-sign them."""

from __future__ import annotations

import argparse
import base64
import datetime as dt
import os
import plistlib
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def run(cmd: list[str], check: bool = True, input_bytes: bytes | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=check, input=input_bytes, capture_output=True)


def extract_plist(profile: Path) -> bytes:
    # Prefer security cms -D; fall back to raw XML slice.
    try:
        out = run(["security", "cms", "-D", "-i", str(profile)])
        return out.stdout
    except Exception:
        data = profile.read_bytes()
        start = data.find(b"<?xml")
        end = data.find(b"</plist>")
        if start < 0 or end < 0:
            raise RuntimeError(f"cannot decode profile: {profile}")
        return data[start : end + 8]


def get_cn_from_p12(p12: Path) -> str:
    pem = run(
        ["openssl", "pkcs12", "-in", str(p12), "-passin", "pass:", "-nokeys", "-legacy"],
    ).stdout
    subject = run(
        ["openssl", "x509", "-noout", "-subject", "-nameopt", "oneline,-esc_msb"],
        input_bytes=pem,
    ).stdout.decode()
    if "CN = " not in subject:
        raise RuntimeError(f"no CN in {p12}")
    return subject.split("CN = ")[-1].split(",")[0].strip()


def get_cert_b64(p12: Path) -> str:
    pem = run(
        ["openssl", "pkcs12", "-in", str(p12), "-passin", "pass:", "-nokeys", "-legacy"],
    ).stdout
    der = run(["openssl", "x509", "-outform", "DER"], input_bytes=pem).stdout
    return base64.b64encode(der).decode()


def setup_keychain(p12: Path) -> tuple[str, str]:
    name = "monkeygram-profiles.keychain"
    password = "temp123"
    run(["security", "delete-keychain", name], check=False)
    run(["security", "create-keychain", "-p", password, name])
    existing = run(["security", "list-keychains", "-d", "user"], check=False).stdout.decode()
    existing_paths = [line.strip().strip('"') for line in existing.splitlines() if line.strip()]
    run(["security", "list-keychains", "-d", "user", "-s", name, *existing_paths])
    run(["security", "set-keychain-settings", name])
    run(["security", "unlock-keychain", "-p", password, name])
    run(
        [
            "security",
            "import",
            str(p12),
            "-k",
            name,
            "-P",
            "",
            "-T",
            "/usr/bin/codesign",
            "-T",
            "/usr/bin/security",
        ]
    )
    run(
        [
            "security",
            "set-key-partition-list",
            "-S",
            "apple-tool:,apple:",
            "-k",
            password,
            name,
        ]
    )
    return name, password


def refresh_one(profile: Path, cert_b64: str, identity: str, keychain: str, years: int) -> None:
    plist_bytes = extract_plist(profile)
    data = plistlib.loads(plist_bytes)

    now = dt.datetime.utcnow()
    data["CreationDate"] = now
    data["ExpirationDate"] = now + dt.timedelta(days=365 * years)
    data["DeveloperCertificates"] = [base64.b64decode(cert_b64)]
    data.pop("DER-Encoded-Profile", None)

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        plist_path = tmp_path / "profile.plist"
        out_path = tmp_path / "profile.mobileprovision"
        plist_path.write_bytes(plistlib.dumps(data))
        run(
            [
                "security",
                "cms",
                "-S",
                "-k",
                keychain,
                "-N",
                identity,
                "-i",
                str(plist_path),
                "-o",
                str(out_path),
            ]
        )
        shutil.copyfile(out_path, profile)
        print(
            f"refreshed {profile.name}: expires {data['ExpirationDate'].isoformat()}Z"
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--codesigning-root", required=True, type=Path)
    parser.add_argument("--years", type=int, default=2)
    args = parser.parse_args()

    root = args.codesigning_root.resolve()
    profiles = root / "profiles"
    p12 = root / "certs" / "SelfSigned.p12"
    if not profiles.is_dir() or not p12.is_file():
        print(f"missing profiles or cert under {root}", file=sys.stderr)
        sys.exit(1)

    identity = get_cn_from_p12(p12)
    cert_b64 = get_cert_b64(p12)
    print(f"signing identity: {identity}")

    keychain, _ = setup_keychain(p12)
    try:
        for profile in sorted(profiles.glob("*.mobileprovision")):
            refresh_one(profile, cert_b64, identity, keychain, args.years)
    finally:
        run(["security", "delete-keychain", keychain], check=False)


if __name__ == "__main__":
    main()
