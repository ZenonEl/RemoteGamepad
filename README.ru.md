# 🎮 RemoteGamepad

[![License](https://img.shields.io/badge/license-GPL--3.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.13+-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Platform](https://img.shields.io/badge/platform-Linux-FCC624.svg?logo=linux&logoColor=black)](#)
[![Lang](https://img.shields.io/badge/lang-EN%20%7C%20RU-success.svg)](README.md)

> Превращает смартфон в беспроводной геймпад Xbox 360 для игр на Linux-ПК.

RemoteGamepad — это мост между браузером телефона и виртуальным контроллером Xbox 360 на Linux. Телефон читает ввод через **Web Gamepad API**, шлёт его по **WebSocket** на сервер на **FastAPI**, а сервер транслирует события в `/dev/uinput` через **evdev**. Игры на ПК видят его как обычный геймпад Xbox 360 — никаких модификаций со стороны игры не нужно.

**Какую нишу закрывает:** ситуации, когда геймпад не подключается напрямую к ПК (нет драйверов, проблемы с BT-сопряжением, нюансы железа), но к телефону — подключается. Или когда вообще нет физического контроллера, и нужны экранные сенсорные кнопки.

---

## ✨ Что внутри стоит посмотреть

- **Честная имперсонация Xbox 360.** Виртуальное устройство регистрируется в ядре под именем `Microsoft X-Box 360 pad` с реальными vendor/product ID (`0x045e:0x028e`). Steam, SDL2 и mapping-библиотеки внутри игр автоматически подхватывают правильный профиль Xbox вместо generic-пада со сломанными триггерами.
- **Триггеры работают как оси и кнопки одновременно.** `LT/RT` уходят и как оси `ABS_Z`/`ABS_RZ` (0–255), и как button-события `BTN_TL2`/`BTN_TR2` (порог срабатывания >25/255). Это нужно потому, что разные тестеры и игры читают разные формы.
- **Async через один WebSocket.** Единственный endpoint `/ws`, один JSON-фрейм несёт стики + кнопки + D-pad. Задержка в локальной Wi-Fi сети упирается в радиоканал, не в сервер.
- **QR-код в консоль.** При старте `main.py` рисует ASCII QR-код с URL локальной сети. Если задан `EXTERNAL_URL` (zrok / ngrok / любой туннель) — печатается второй QR для публичного адреса. Навёл камеру, открыл UI, играешь.
- **Явные `AbsInfo`.** Стики 16-bit signed (`-32768..32767`), триггеры 8-bit unsigned (`0..255`), D-pad как hat-switch (`-1..1`), `fuzz`/`flat` обнулены. Так обходятся плавающие dead zones из дефолтов ядра разных дистрибутивов.

## 🛠 Стек

| Слой | Технология |
|---|---|
| HTTP / WebSocket-сервер | **FastAPI** + `uvicorn[standard]` (async/await) |
| Виртуальный геймпад | **python-evdev** → `/dev/uinput` |
| Frontend | Web Gamepad API + **HTMX** + Materialize CSS |
| Шаблоны | Jinja2 (`templates/index.html`) |
| Конфигурация | `.env` (PORT, EXTERNAL_URL) |
| Логирование | **Loguru** |
| QR | `qrcode[pil]` — ASCII-печать в консоль |
| i18n | `lang/{en,ru}.json` + HTMX-свитчер языка в UI |
| Зависимости | **uv** (`pyproject.toml` + `uv.lock`) |
| Язык | Python 3.13 |
| Лицензия | GPL-3.0 |

## 🏗 Архитектура

```
┌──────────────┐  USB/BT/OTG ┌──────────┐ WebSocket  ┌─────────────┐  evdev   ┌────────┐
│  Физический  │ ──────────▶ │  Phone   │ ─────────▶ │   FastAPI   │ ───────▶ │ Linux  │
│  контроллер  │             │ (Browser │  JSON over │  /ws + /    │  uinput  │ kernel │
│   (опц.)     │             │  Gamepad │  local WiFi│  (uvicorn)  │          │        │
└──────────────┘             │   API)   │            └─────────────┘          └────┬───┘
                             └──────────┘                                          │
                                  ▲                                                ▼
                                  │ touch UI                                ┌─────────────┐
                                  │ (если нет                               │   Любая     │
                                  │  физ. пада)                             │   игра      │
                                                                            │ (SDL2/Steam)│
                                                                            └─────────────┘
```

1. Телефон собирает ввод — либо с физического геймпада через `navigator.getGamepads()`, либо через экранные кнопки.
2. Клиент сериализует `{axes, buttons}` в JSON и шлёт в открытый WebSocket.
3. FastAPI распарсивает: оси → `EV_ABS`, кнопки → `EV_KEY`, D-pad → hat-оси.
4. evdev пишет в `/dev/uinput`, ядро Linux создаёт настоящее input-устройство.
5. Игра видит штатный Xbox 360 controller.

## 🚀 Быстрый старт

### Требования

- Linux (любой современный дистрибутив — `/dev/uinput` есть в mainline-ядре)
- Python **3.13+**
- [`uv`](https://docs.astral.sh/uv/getting-started/installation/) — менеджер зависимостей: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- Смартфон или планшет с современным браузером, в **той же Wi-Fi-сети**

### Установка

```bash
# 1. Клонируем
git clone https://github.com/ZenonEl/RemoteGamepad.git
cd RemoteGamepad

# 2. Однократно: даём пользователю права на создание виртуальных input-устройств
sudo bash scripts/setup_udev.sh
# после этого нужен один re-login — группа input применится только в новой сессии

# 3. Ставим зависимости (uv читает pyproject.toml + uv.lock)
uv sync

# 4. (Опционально) настраиваем туннель
cp .env.example .env
# отредактируйте .env, EXTERNAL_URL нужен только если открываете доступ через zrok/ngrok

# 5. Запускаем
uv run main.py
```

Сервер напечатает в консоль QR-код с адресом `http://<ваш-LAN-IP>:5002`. Сканируете телефоном — открывается touch UI. Если к телефону подключен физический контроллер — он сразу работает; если нет — управляете экранными кнопками.

### Структура

```
RemoteGamepad/
├── main.py                       # точка входа — печать QR + запуск uvicorn
├── pyproject.toml                # uv-зависимости
├── uv.lock
├── .env.example
├── scripts/setup_udev.sh         # права на uinput
├── src/
│   ├── config.py                 # PORT, EXTERNAL_URL
│   ├── api/server.py             # FastAPI: GET /, WS /ws, статика
│   └── core/
│       ├── gamepad_manager.py    # VirtualGamepadDevice + менеджер
│       └── mapping_config.py     # JS-имена кнопок → коды evdev
├── templates/
│   ├── index.html                # основной UI
│   └── translations.html
├── static/                       # JS / CSS
├── lang/{en,ru}.json             # i18n-строки
└── assets/                       # иконки, картинки
```

## 🔧 Troubleshooting

**`Permission denied` на `/dev/uinput`** — не запускался (или не было re-login после) `scripts/setup_udev.sh`. Скрипт создаёт udev-правило, разрешающее группе `input` писать в `uinput`, добавляет пользователя в `input` и подгружает модуль `uinput`. Права на группу применяются только в новой сессии.

**Телефон не открывает `http://<LAN-IP>:5002`** — порт зарезан фаерволом.
- `firewalld`: `sudo firewall-cmd --add-port=5002/tcp --permanent && sudo firewall-cmd --reload`
- `ufw`: `sudo ufw allow 5002/tcp`
- Проверка на ПК: `curl -I http://localhost:5002`.

**Кнопки работают в браузере, но игра видит их неправильно** — убедитесь, что игра использует SDL2-маппинги (большинство современных движков — да). Проверить, что устройство видится как Xbox 360: `cat /proc/bus/input/devices | grep -A4 "X-Box 360"`.

**Хочется доступа извне локалки** — поднимите zrok / ngrok на `localhost:5002`, положите публичный URL в `.env` как `EXTERNAL_URL`, перезапустите. Второй QR с публичным адресом будет напечатан рядом.

## 🧪 Статус и ограничения

- **Beta.** Протокол и маппинги могут меняться между коммитами.
- **Один виртуальный геймпад на инстанс сервера** — менеджер сейчас single-slot (KISS).
- **Только Linux.** Привязка к `/dev/uinput`; для Windows/macOS нужен другой backend виртуального драйвера.
- **Без аутентификации.** Кто угодно в той же Wi-Fi, кто знает URL, сможет управлять падом. Держите сервер в доверенной сети или за туннелем с авторизацией.
- **Автоматических тестов в текущей ветке нет.**

## 📜 Лицензия

GPL-3.0 — см. [LICENSE](LICENSE).

## 📞 Контакты

- GitHub: **[@ZenonEl](https://github.com/ZenonEl)**
- Mastodon: **[@ZenonEl@mastodon.ml](https://mastodon.ml/@ZenonEl)**

---

<div align="center">

[⭐ Star](https://github.com/ZenonEl/RemoteGamepad) · [🐛 Issue](https://github.com/ZenonEl/RemoteGamepad/issues) · [💡 Idea](https://github.com/ZenonEl/RemoteGamepad/issues)

</div>
