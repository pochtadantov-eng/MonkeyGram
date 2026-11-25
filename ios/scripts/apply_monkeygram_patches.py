#!/usr/bin/env python3
"""Apply MonkeyGram visual-mod patches onto a Telegram-iOS checkout."""

from __future__ import annotations

import argparse
import pathlib
import re
import shutil
import sys


def die(msg: str) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def replace_once(path: pathlib.Path, old: str, new: str, label: str) -> None:
    text = path.read_text(encoding="utf-8")
    if old not in text:
        if new.strip() in text or label in text:
            print(f"skip (already applied): {label}")
            return
        die(f"pattern not found for {label} in {path}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")
    print(f"patched: {label}")


def insert_after(path: pathlib.Path, marker: str, insertion: str, label: str) -> None:
    text = path.read_text(encoding="utf-8")
    if insertion.strip() in text:
        print(f"skip (already applied): {label}")
        return
    if marker not in text:
        die(f"marker not found for {label} in {path}")
    path.write_text(text.replace(marker, marker + insertion, 1), encoding="utf-8")
    print(f"patched: {label}")


def ensure_dep(build_path: pathlib.Path, dep: str, label: str) -> None:
    text = build_path.read_text(encoding="utf-8")
    if dep in text:
        print(f"skip (dep present): {label}")
        return
    # Insert after deps = [
    m = re.search(r"deps\s*=\s*\[", text)
    if not m:
        die(f"deps block not found in {build_path}")
    idx = m.end()
    text = text[:idx] + f'\n        "{dep}",' + text[idx:]
    build_path.write_text(text, encoding="utf-8")
    print(f"patched: {label}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--telegram-root", required=True, type=pathlib.Path)
    parser.add_argument("--overlay-root", required=True, type=pathlib.Path)
    args = parser.parse_args()

    tg = args.telegram_root.resolve()
    overlay = args.overlay_root.resolve()
    if not (tg / "versions.json").exists():
        die(f"not a Telegram-iOS tree: {tg}")

    # 1) Copy MonkeyGramVisual module
    src_mod = overlay / "sources" / "MonkeyGramVisual"
    dst_mod = tg / "submodules" / "MonkeyGramVisual"
    if dst_mod.exists():
        shutil.rmtree(dst_mod)
    shutil.copytree(src_mod, dst_mod)
    print(f"copied module -> {dst_mod}")

    # 2) Copy settings controller into PeerInfoScreen
    peer_info_sources = tg / "submodules" / "TelegramUI" / "Components" / "PeerInfo" / "PeerInfoScreen" / "Sources"
    shutil.copy2(
        overlay / "sources" / "MonkeyGramVisualSettingsController.swift",
        peer_info_sources / "MonkeyGramVisualSettingsController.swift",
    )
    print("copied MonkeyGramVisualSettingsController.swift")

    # 3) Add Bazel deps
    ensure_dep(
        tg / "submodules" / "TelegramUI" / "Components" / "PeerInfo" / "PeerInfoScreen" / "BUILD",
        "//submodules/MonkeyGramVisual:MonkeyGramVisual",
        "PeerInfoScreen -> MonkeyGramVisual",
    )
    ensure_dep(
        tg / "submodules" / "TelegramUI" / "Components" / "Gifts" / "GiftSetupScreen" / "BUILD",
        "//submodules/MonkeyGramVisual:MonkeyGramVisual",
        "GiftSetupScreen -> MonkeyGramVisual",
    )
    ensure_dep(
        tg / "submodules" / "TelegramUI" / "Components" / "Stars" / "StarsTransactionsScreen" / "BUILD",
        "//submodules/MonkeyGramVisual:MonkeyGramVisual",
        "StarsTransactionsScreen -> MonkeyGramVisual",
    )

    # 4) Settings section enum
    peer_info = peer_info_sources / "PeerInfoScreen.swift"
    replace_once(
        peer_info,
        "    case wallet\n}",
        "    case wallet\n    case monkeygram\n}",
        "PeerInfoSettingsSection.monkeygram",
    )

    # 5) Settings list item + visual balances / gifts
    settings_items = peer_info_sources / "PeerInfoSettingsItems.swift"
    insert_after(
        settings_items,
        "import WalletContext\n",
        "import MonkeyGramVisual\n",
        "import MonkeyGramVisual in settings items",
    )

    balance_block_old = """    if let starsState = data.starsState {
        if !isPremiumDisabled || abs(starsState.balance.value) > 0 {
            let balanceText: NSAttributedString
            if abs(starsState.balance.value) > 0 {
                let formattedLabel = formatStarsAmountText(starsState.balance, dateTimeFormat: presentationData.dateTimeFormat)
                let smallLabelFont = Font.regular(floor(presentationData.listsFontSize.itemListBaseFontSize / 17.0 * 13.0))
                let labelFont = Font.regular(presentationData.listsFontSize.itemListBaseFontSize)
                let labelColor = presentationData.theme.list.itemSecondaryTextColor
                balanceText = tonAmountAttributedString(formattedLabel, integralFont: labelFont, fractionalFont: smallLabelFont, color: labelColor, decimalSeparator: presentationData.dateTimeFormat.decimalSeparator)
            } else {
                balanceText = NSAttributedString()
            }
            items[.payment]!.append(PeerInfoScreenDisclosureItem(id: 102, label: .attributedText(balanceText), text: presentationData.strings.Settings_Stars, icon: PresentationResourcesSettings.stars, action: {
                interaction.openSettings(.stars)
            }))
        }
    }
    if let tonState = data.tonState {
        if abs(tonState.balance.value) > 0 {
            let balanceText: NSAttributedString
            if abs(tonState.balance.value) > 0 {
                let formattedLabel = formatTonAmountText(tonState.balance.value, dateTimeFormat: presentationData.dateTimeFormat)
                let smallLabelFont = Font.regular(floor(presentationData.listsFontSize.itemListBaseFontSize / 17.0 * 13.0))
                let labelFont = Font.regular(presentationData.listsFontSize.itemListBaseFontSize)
                let labelColor = presentationData.theme.list.itemSecondaryTextColor
                balanceText = tonAmountAttributedString(formattedLabel, integralFont: labelFont, fractionalFont: smallLabelFont, color: labelColor, decimalSeparator: presentationData.dateTimeFormat.decimalSeparator)
            } else {
                balanceText = NSAttributedString()
            }
            items[.payment]!.append(PeerInfoScreenDisclosureItem(id: 103, label: .attributedText(balanceText), text: presentationData.strings.Settings_MyTon, icon: PresentationResourcesSettings.gramEarnings, action: {
                interaction.openSettings(.ton)
            }))
        }
    }"""

    balance_block_new = """    let monkeyStore = MonkeyGramVisualStore.shared
    let visualBalanceOn = monkeyStore.visualBalanceEnabled
    if let starsState = data.starsState {
        let starsValue = visualBalanceOn ? StarsAmount(value: Int64(monkeyStore.starsBalance.rounded(.down)), nanos: 0) : starsState.balance
        if !isPremiumDisabled || abs(starsValue.value) > 0 || visualBalanceOn {
            let balanceText: NSAttributedString
            if abs(starsValue.value) > 0 || visualBalanceOn {
                let formattedLabel = formatStarsAmountText(starsValue, dateTimeFormat: presentationData.dateTimeFormat)
                let smallLabelFont = Font.regular(floor(presentationData.listsFontSize.itemListBaseFontSize / 17.0 * 13.0))
                let labelFont = Font.regular(presentationData.listsFontSize.itemListBaseFontSize)
                let labelColor = presentationData.theme.list.itemSecondaryTextColor
                balanceText = tonAmountAttributedString(formattedLabel, integralFont: labelFont, fractionalFont: smallLabelFont, color: labelColor, decimalSeparator: presentationData.dateTimeFormat.decimalSeparator)
            } else {
                balanceText = NSAttributedString()
            }
            items[.payment]!.append(PeerInfoScreenDisclosureItem(id: 102, label: .attributedText(balanceText), text: presentationData.strings.Settings_Stars, icon: PresentationResourcesSettings.stars, action: {
                interaction.openSettings(.stars)
            }))
        }
    }
    if let tonState = data.tonState {
        let tonValue = visualBalanceOn ? Int64((monkeyStore.tonBalance * 1_000_000_000.0).rounded()) : tonState.balance.value
        if abs(tonValue) > 0 || visualBalanceOn {
            let balanceText: NSAttributedString
            if abs(tonValue) > 0 || visualBalanceOn {
                let formattedLabel = formatTonAmountText(tonValue, dateTimeFormat: presentationData.dateTimeFormat)
                let smallLabelFont = Font.regular(floor(presentationData.listsFontSize.itemListBaseFontSize / 17.0 * 13.0))
                let labelFont = Font.regular(presentationData.listsFontSize.itemListBaseFontSize)
                let labelColor = presentationData.theme.list.itemSecondaryTextColor
                balanceText = tonAmountAttributedString(formattedLabel, integralFont: labelFont, fractionalFont: smallLabelFont, color: labelColor, decimalSeparator: presentationData.dateTimeFormat.decimalSeparator)
            } else {
                balanceText = NSAttributedString()
            }
            items[.payment]!.append(PeerInfoScreenDisclosureItem(id: 103, label: .attributedText(balanceText), text: presentationData.strings.Settings_MyTon, icon: PresentationResourcesSettings.gramEarnings, action: {
                interaction.openSettings(.ton)
            }))
        }
    }"""
    replace_once(settings_items, balance_block_old, balance_block_new, "visual Stars/TON balances")

    gift_old = """    if let starsState = data.starsState {
        if !isPremiumDisabled || starsState.balance > StarsAmount.zero {
            items[.payment]!.append(PeerInfoScreenDisclosureItem(id: 105, label: .text(""), text: presentationData.strings.Settings_SendGift, icon: PresentationResourcesSettings.premiumGift, action: {
                interaction.openSettings(.premiumGift)
            }))
        }
    }"""
    gift_new = """    if let starsState = data.starsState {
        if !isPremiumDisabled || starsState.balance > StarsAmount.zero || MonkeyGramVisualStore.shared.visualGiftsEnabled {
            items[.payment]!.append(PeerInfoScreenDisclosureItem(id: 105, label: .text(""), text: presentationData.strings.Settings_SendGift, icon: PresentationResourcesSettings.premiumGift, action: {
                interaction.openSettings(.premiumGift)
            }))
        }
    }"""
    replace_once(settings_items, gift_old, gift_new, "always show Send Gift when visual gifts on")

    insert_after(
        settings_items,
        """    items[.support]!.append(PeerInfoScreenDisclosureItem(id: 0, text: presentationData.strings.Settings_Support, icon: PresentationResourcesSettings.support, action: {
        interaction.openSettings(.support)
    }))
""",
        """    items[.extra]!.append(PeerInfoScreenDisclosureItem(id: 50, text: "MonkeyGram", icon: PresentationResourcesSettings.premium, action: {
        interaction.openSettings(.monkeygram)
    }))
""",
        "MonkeyGram settings row",
    )

    # 6) openSettings handler
    settings_actions = peer_info_sources / "PeerInfoScreenSettingsActions.swift"
    insert_after(
        settings_actions,
        "import UndoUI\n",
        "import MonkeyGramVisual\n",
        "import MonkeyGramVisual in settings actions",
    )
    replace_once(
        settings_actions,
        """        case .wallet:
            guard WalletConfiguration.with(appConfiguration: self.context.currentAppConfiguration.with { $0 }).isAvailable else {
                self.controller?.present(UndoOverlayController(presentationData: self.presentationData, content: .info(title: nil, text: self.presentationData.strings.Wallet_Unavailable, timeout: nil, customUndoText: nil), action: { _ in return false }), in: .window(.root))
                return
            }
            push(self.context.sharedContext.makeWalletScreen(context: self.context))
        }
    }
""",
        """        case .wallet:
            guard WalletConfiguration.with(appConfiguration: self.context.currentAppConfiguration.with { $0 }).isAvailable else {
                self.controller?.present(UndoOverlayController(presentationData: self.presentationData, content: .info(title: nil, text: self.presentationData.strings.Wallet_Unavailable, timeout: nil, customUndoText: nil), action: { _ in return false }), in: .window(.root))
                return
            }
            push(self.context.sharedContext.makeWalletScreen(context: self.context))
        case .monkeygram:
            push(monkeyGramVisualSettingsController(context: self.context))
        }
    }
""",
        "openSettings(.monkeygram)",
    )

    # When visual balance enabled, Stars/TON screens open MonkeyGram history instead of (or before) real history
    replace_once(
        settings_actions,
        """        case .stars:
            if let starsContext = self.controller?.starsContext {
                push(self.context.sharedContext.makeStarsTransactionsScreen(context: self.context, starsContext: starsContext))
            }
        case .ton:
            if let tonContext = self.controller?.tonContext {
                push(self.context.sharedContext.makeStarsTransactionsScreen(context: self.context, starsContext: tonContext))
            }
""",
        """        case .stars:
            if MonkeyGramVisualStore.shared.visualBalanceEnabled {
                push(monkeyGramHistoryController(context: self.context, currency: .stars))
            } else if let starsContext = self.controller?.starsContext {
                push(self.context.sharedContext.makeStarsTransactionsScreen(context: self.context, starsContext: starsContext))
            }
        case .ton:
            if MonkeyGramVisualStore.shared.visualBalanceEnabled {
                push(monkeyGramHistoryController(context: self.context, currency: .ton))
            } else if let tonContext = self.controller?.tonContext {
                push(self.context.sharedContext.makeStarsTransactionsScreen(context: self.context, starsContext: tonContext))
            }
""",
        "visual Stars/TON history routing",
    )

    # 7) Profile gift row when visual gifts enabled
    profile_items = peer_info_sources / "PeerInfoProfileItems.swift"
    insert_after(
        profile_items,
        "import BoostLevelIconComponent\n",
        "import MonkeyGramVisual\n",
        "import MonkeyGramVisual in profile items",
    )
    replace_once(
        profile_items,
        """                }, contextAction: birthdayContextAction, requestLayout: { _ in
                }))
            }
            
            var hasAbout = false
""",
        """                }, contextAction: birthdayContextAction, requestLayout: { _ in
                }))
            }

            if MonkeyGramVisualStore.shared.visualGiftsEnabled, user.id != context.account.peerId, user.botInfo == nil, !user.flags.contains(.isSupport) {
                items[currentPeerInfoSection]!.append(PeerInfoScreenActionItem(id: "monkeygram.sendGift", text: presentationData.strings.Profile_SendGift, icon: PresentationResourcesSettings.premiumGift, action: {
                    interaction.openPremiumGift()
                }))
            }
            
            var hasAbout = false
""",
        "profile Send Gift row (visual)",
    )
    # 8) GiftSetupScreen visual spend
    gift_setup = tg / "submodules" / "TelegramUI" / "Components" / "Gifts" / "GiftSetupScreen" / "Sources" / "GiftSetupScreen.swift"
    insert_after(
        gift_setup,
        "import TelegramCore\n",
        "import MonkeyGramVisual\n",
        "import MonkeyGramVisual in GiftSetupScreen",
    )
    replace_once(
        gift_setup,
        """            if starsState.balance < StarsAmount(value: finalPrice, nanos: 0) {
                let _ = (self.optionsPromise.get()
                |> filter { $0 != nil }
                |> take(1)
                |> deliverOnMainQueue).startStandalone(next: { [weak self, starsContext] options in
                    guard let self, let component = self.component, let controller = self.environment?.controller() else {
                        return
                    }
                    let purchaseController = component.context.sharedContext.makeStarsPurchaseScreen(
                        context: component.context,
                        starsContext: starsContext,
                        options: options ?? [],
                        purpose: .starGift(peerId: component.peerId, requiredStars: finalPrice),
                        targetPeerId: nil,
                        customTheme: nil,
                        completion: { [weak self, weak starsContext] stars in
                            guard let self, let starsContext else {
                                return
                            }
                            self.inProgress = true
                            self.state?.updated()
                            
                            starsContext.add(balance: StarsAmount(value: stars, nanos: 0))
                            let _ = (starsContext.onUpdate
                            |> deliverOnMainQueue).start(next: {
                                proceed()
                            })
                        }
                    )
                    controller.push(purchaseController)
                })
            } else {
                proceed()
            }
""",
        """            let monkey = MonkeyGramVisualStore.shared
            if monkey.visualBalanceEnabled, let component = self.component, let controller = self.environment?.controller() {
                let presentationData = component.context.sharedContext.currentPresentationData.with { $0 }
                let ok = monkey.spend(
                    currency: .stars,
                    amount: Double(finalPrice),
                    title: "Подарок / NFT",
                    subtitle: "Визуальная покупка"
                )
                if ok {
                    controller.present(UndoOverlayController(presentationData: presentationData, content: .succeed(text: "Визуальная покупка · −\\(finalPrice) Stars", timeout: 2.5, customUndoText: nil), elevatedLayout: false, action: { _ in false }), in: .window(.root))
                    controller.dismiss()
                } else {
                    let alertController = textAlertController(context: component.context, title: nil, text: "Недостаточно визуальных Stars. Пополните баланс в Настройки → MonkeyGram.", actions: [TextAlertAction(type: .defaultAction, title: presentationData.strings.Common_OK, action: {})])
                    controller.present(alertController, in: .window(.root))
                }
            } else if starsState.balance < StarsAmount(value: finalPrice, nanos: 0) {
                let _ = (self.optionsPromise.get()
                |> filter { $0 != nil }
                |> take(1)
                |> deliverOnMainQueue).startStandalone(next: { [weak self, starsContext] options in
                    guard let self, let component = self.component, let controller = self.environment?.controller() else {
                        return
                    }
                    let purchaseController = component.context.sharedContext.makeStarsPurchaseScreen(
                        context: component.context,
                        starsContext: starsContext,
                        options: options ?? [],
                        purpose: .starGift(peerId: component.peerId, requiredStars: finalPrice),
                        targetPeerId: nil,
                        customTheme: nil,
                        completion: { [weak self, weak starsContext] stars in
                            guard let self, let starsContext else {
                                return
                            }
                            self.inProgress = true
                            self.state?.updated()
                            
                            starsContext.add(balance: StarsAmount(value: stars, nanos: 0))
                            let _ = (starsContext.onUpdate
                            |> deliverOnMainQueue).start(next: {
                                proceed()
                            })
                        }
                    )
                    controller.push(purchaseController)
                })
            } else {
                proceed()
            }
""",
        "GiftSetupScreen visual spend",
    )

    # 9) Rename app display name
    telegram_build = tg / "Telegram" / "BUILD"
    replace_once(
        telegram_build,
        """    <key>CFBundleDisplayName</key>
    <string>Telegram</string>
""",
        """    <key>CFBundleDisplayName</key>
    <string>MonkeyGram</string>
""",
        "CFBundleDisplayName MonkeyGram",
    )

    # 10) Optional configuration overlay
    conf_src = overlay / "configuration" / "monkeygram-configuration.json"
    conf_dst = tg / "build-system" / "monkeygram-configuration.json"
    if conf_src.exists():
        shutil.copy2(conf_src, conf_dst)
        print(f"copied {conf_dst.name}")

    print("MonkeyGram patches applied successfully.")


if __name__ == "__main__":
    main()
