# MonkeyGram

Мод Telegram для iPhone с **визуальными** подарками, Stars и TON + веб-превью.

## iOS IPA (основной путь)

Сборка unsigned IPA из последнего Telegram-iOS через **GitHub Actions**:

1. Actions → **Build MonkeyGram IPA** → Run workflow  
2. Скачай артефакт `MonkeyGram.ipa`  
3. Установи через AltStore / Sideloadly / TrollStore  

В приложении: **Настройки → MonkeyGram**

- включить визуалку (кнопка «Отправить подарок» в профиле)  
- включить баланс Stars / TON, ввести и сохранить  
- история пополнений и визуальных трат  

Подробности: [`ios/README.md`](ios/README.md)

## Веб-превью (демо UI)

```bash
cd web
npm install
npm run dev
```

Локальный Telegram-подобный клиент с теми же визуальными функциями (для быстрой проверки UX).
