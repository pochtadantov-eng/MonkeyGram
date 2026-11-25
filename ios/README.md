# MonkeyGram iOS (Telegram-iOS mod → IPA)

Сборка **unsigned IPA** на базе последнего [Telegram-iOS](https://github.com/TelegramMessenger/Telegram-iOS) с визуальными функциями MonkeyGram.

## Что добавляет мод

В **Настройки → MonkeyGram**:

1. **Включить визуалку** — кнопка «Отправить подарок» в профиле  
2. **Включить баланс** — поля Stars / TON + «Сохранить балансы» (UserDefaults, не сбрасываются)  
3. Истории Stars / TON с визуальными пополнениями и тратами  
4. При покупке подарка/NFT с включённым визуальным балансом — списание визуальных Stars (без реального платежа Telegram)

Имя приложения на SpringBoard: **MonkeyGram**.

## GitHub Actions → IPA

Workflow: `.github/workflows/build-ipa.yml`

1. Открой **Actions → Build MonkeyGram IPA → Run workflow**  
2. Дождись job на `macos-15` (полная сборка Telegram-iOS долгая: часто 1–3+ часа)  
3. Скачай артефакт **MonkeyGram-ipa** (`MonkeyGram.ipa`)  
4. На `main` также создаётся GitHub Release с IPA

### Установка на iPhone

IPA **unsigned** (как community-сборки Telegram-iOS):

- AltStore / SideStore  
- Sideloadly  
- TrollStore (если устройство поддерживает)

Нужен свой Apple ID для sideload (или TrollStore).

## Локально (macOS + Xcode)

```bash
git clone --recursive https://github.com/TelegramMessenger/Telegram-iOS.git
python3 /path/to/MonkeyGram/ios/scripts/apply_monkeygram_patches.py \
  --telegram-root Telegram-iOS \
  --overlay-root /path/to/MonkeyGram/ios

cd Telegram-iOS
python3 build-system/Make/ImportCertificates.py --path build-system/fake-codesigning/certs
python3 build-system/Make/Make.py \
  --overrideXcodeVersion \
  build \
  --configurationPath=build-system/monkeygram-configuration.json \
  --codesigningInformationPath=build-system/fake-codesigning \
  --configuration=release_arm64 \
  --buildNumber=100001 \
  --outputBuildArtifactsPath=build/artifacts
```

IPA: `build/artifacts/Telegram.ipa` (после патча display name = MonkeyGram).

## Важно

- Для App Store / своего bundle id получи [api_id](https://core.telegram.org/api/obtaining_api_id) и правь `ios/configuration/monkeygram-configuration.json`.  
- Community CI использует `fake-codesigning`; для установки на устройство без джейлбрейка нужен sideload.  
- Версия Xcode в upstream `versions.json` может отличаться от runner’а — workflow включает `--overrideXcodeVersion`.
