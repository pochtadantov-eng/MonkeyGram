# MonkeyGram iOS (Telegram-iOS mod → IPA)

Сборка **unsigned IPA** на базе последнего [Telegram-iOS](https://github.com/TelegramMessenger/Telegram-iOS) с визуальным слоем в духе VisualGram — **без ключей активации / Secure Enclave**.

Источник визуалки: разобранный VisualGram IPA (`VisualGramLocalAppearance`, gift grid, balance history, marketplace buy). Бинарник нельзя вставить в Bazel — логика перенесена в `MonkeyGramVisual` + патчи TelegramUI.

## Что добавляет мод

В **Настройки → MonkeyGram** (доступ всегда открыт):

1. **Включить визуалку** — «Отправить подарок» в профиле + локальный маркетплейс NFT  
2. **Включить баланс** — Stars / TON (Grams) + сохранение (UserDefaults)  
3. Истории Stars / TON  
4. **Инвентарь** визуальных NFT после покупок на маркетплейсе  
5. Покупка подарка/NFT (в т.ч. Cookie Heart) списывает визуальный баланс — **без** Telegram payments / `buyStarGift`  
6. Display name: **MonkeyGram**

На первом запуске визуалка и баланс включены по умолчанию.

## GitHub Actions → IPA

Workflow: `.github/workflows/build-ipa.yml`

1. **Actions → Build MonkeyGram IPA → Run workflow**  
2. Job на `xcode-27` (полная сборка часто 1–3+ часа)  
3. Артефакт **MonkeyGram-ipa** (`MonkeyGram.ipa`)  
4. На `main` — GitHub Release с IPA

### Установка

IPA **unsigned**:

- AltStore / SideStore  
- Sideloadly  
- TrollStore

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

## Важно

- Для своего bundle id: [api_id](https://core.telegram.org/api/obtaining_api_id) → `ios/configuration/monkeygram-configuration.json`.  
- Community CI = `fake-codesigning`; на устройство — sideload.  
- Полный VisualGram (craft / schedule / emoji status / wallet card) — только ключевые buy/balance/inventory пути; без `app.visualgram.activation*`.
