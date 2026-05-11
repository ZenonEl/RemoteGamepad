# 🎮 RemoteGamepad

[![License](https://img.shields.io/badge/license-GPL--3.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.13+-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Platform](https://img.shields.io/badge/platform-Linux-FCC624.svg?logo=linux&logoColor=black)](#)
[![Lang](https://img.shields.io/badge/lang-EN%20%7C%20RU-success.svg)](README.ru.md)

> Turn your smartphone into a wireless Xbox 360 gamepad for Linux PC games.

RemoteGamepad bridges a phone's browser to a virtual Xbox 360 controller on Linux. The phone reads input via the **Web Gamepad API**, streams it over **WebSocket** to a **FastAPI** server, and the server emits real `evdev` events into `/dev/uinput`. Games on the PC see a standard Xbox 360 pad — no game-side modifications needed.

**Niche it solves:** situations where a controller won't connect directly to the PC (missing drivers, Bluetooth pairing issues, hardware quirks) but the phone *can* see it. Or no physical pad at all — drive the virtual one with the on-screen touch UI.

---

## ✨ What's worth a look

- **Faithful Xbox 360 impersonation.** The virtual device registers in the kernel as `Microsoft X-Box 360 pad` with the genuine vendor/product IDs (`0x045e:0x028e`). Steam, SDL2 and in-game mapping libraries automatically pick the proper Xbox profile instead of falling back to a generic pad with broken triggers.
- **Triggers behave as axes *and* buttons.** `LT/RT` are sent both as `ABS_Z`/`ABS_RZ` axes (0–255) and as `BTN_TL2`/`BTN_TR2` button events (button threshold > 25/255). Different testers and games read different forms — this hits both.
- **Async over a single WebSocket.** One `/ws` endpoint, one JSON frame carrying sticks + buttons + D-pad. Latency on a LAN is dominated by the radio link, not the server.
- **Console QR codes.** On startup `main.py` prints an ASCII QR for the LAN URL. If `EXTERNAL_URL` is set (zrok / ngrok / any tunnel), a second QR for the public address is printed alongside. Aim the camera, the UI opens, play.
- **Explicit `AbsInfo`.** Sticks are 16-bit signed (`-32768..32767`), triggers 8-bit unsigned (`0..255`), D-pad is a hat switch (`-1..1`), `fuzz` and `flat` are zero. Sidesteps the floating dead zones you get from kernel defaults that vary across distros.

## 🛠 Tech stack

| Layer | Technology |
|---|---|
| HTTP / WebSocket server | **FastAPI** + `uvicorn[standard]` (async/await) |
| Virtual gamepad | **python-evdev** → `/dev/uinput` |
| Frontend | Web Gamepad API + **HTMX** + Materialize CSS |
| Templates | Jinja2 (`templates/index.html`) |
| Config | `.env` (PORT, EXTERNAL_URL) |
| Logging | **Loguru** |
| QR | `qrcode[pil]` — ASCII console output |
| i18n | `lang/{en,ru}.json` + HTMX language switcher |
| Dependency manager | **uv** (`pyproject.toml` + `uv.lock`) |
| Language | Python 3.13 |
| License | GPL-3.0 |

## 🏗 Architecture

```
┌──────────────┐  USB/BT/OTG ┌──────────┐ WebSocket  ┌─────────────┐  evdev   ┌────────┐
│  Physical    │ ──────────▶ │  Phone   │ ─────────▶ │   FastAPI   │ ───────▶ │ Linux  │
│  controller  │             │ (Browser │  JSON over │  /ws + /    │  uinput  │ kernel │
│   (opt.)     │             │  Gamepad │  local WiFi│  (uvicorn)  │          │        │
└──────────────┘             │   API)   │            └─────────────┘          └────┬───┘
                             └──────────┘                                          │
                                  ▲                                                ▼
                                  │ touch UI                                ┌─────────────┐
                                  │ (no physical                            │   Any game  │
                                  │  pad case)                              │ (SDL2/Steam)│
                                                                            └─────────────┘
```

1. Phone collects input — either from a physical pad via `navigator.getGamepads()`, or via the on-screen touch UI.
2. The client serialises `{axes, buttons}` to JSON and pushes it through an open WebSocket.
3. FastAPI demultiplexes: axes → `EV_ABS`, buttons → `EV_KEY`, D-pad → hat axes.
4. evdev writes to `/dev/uinput`; the Linux kernel exposes a real input device.
5. Games see a regular Xbox 360 controller.

## 🚀 Quick start

### Prerequisites

- Linux (any modern distro — `/dev/uinput` ships with the mainline kernel)
- Python **3.13+**
- [`uv`](https://docs.astral.sh/uv/getting-started/installation/) — dependency manager: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- A smartphone or tablet with a modern browser on the **same Wi-Fi**

### Install

```bash
# 1. Clone
git clone https://github.com/ZenonEl/RemoteGamepad.git
cd RemoteGamepad

# 2. One-time: grant your user permission to create virtual input devices
sudo bash scripts/setup_udev.sh
# Re-login once after this — the input group only applies to a new session.

# 3. Install dependencies (uv reads pyproject.toml + uv.lock)
uv sync

# 4. (Optional) configure a tunnel
cp .env.example .env
# Edit .env: EXTERNAL_URL is only needed when exposing the server via zrok/ngrok.

# 5. Run
uv run main.py
```

The server prints a QR code in the console pointing at `http://<your-LAN-IP>:5002`. Scan it with your phone — the touch UI opens. If a physical controller is attached to the phone, it Just Works; otherwise the on-screen controls drive the virtual pad.

### Layout

```
RemoteGamepad/
├── main.py                       # entry point — QR codes + uvicorn
├── pyproject.toml                # uv-managed deps
├── uv.lock
├── .env.example
├── scripts/setup_udev.sh         # uinput permissions
├── src/
│   ├── config.py                 # PORT, EXTERNAL_URL
│   ├── api/server.py             # FastAPI: GET /, WS /ws, static mount
│   └── core/
│       ├── gamepad_manager.py    # VirtualGamepadDevice + manager
│       └── mapping_config.py     # JS button names → evdev keycodes
├── templates/
│   ├── index.html                # main UI
│   └── translations.html
├── static/                       # JS / CSS
├── lang/{en,ru}.json             # i18n strings
└── assets/                       # icons, images
```

## 🔧 Troubleshooting

**`Permission denied` on `/dev/uinput`** — `scripts/setup_udev.sh` wasn't run, or there was no re-login afterwards. The script creates a udev rule granting the `input` group write access to `uinput`, adds your user to `input`, and loads the `uinput` kernel module. Group membership only applies to a fresh session.

**Phone can't reach `http://<LAN-IP>:5002`** — the port is blocked by the firewall.
- `firewalld`: `sudo firewall-cmd --add-port=5002/tcp --permanent && sudo firewall-cmd --reload`
- `ufw`: `sudo ufw allow 5002/tcp`
- Sanity-check on the PC: `curl -I http://localhost:5002`.

**Buttons fire in the browser but the game maps them wrong** — make sure the game uses SDL2 mappings (most modern engines do). Verify the device shows up as Xbox 360 in the kernel: `cat /proc/bus/input/devices | grep -A4 "X-Box 360"`.

**Want it reachable from outside the LAN?** Run zrok or ngrok pointing at `localhost:5002`, drop the public URL into `.env` as `EXTERNAL_URL`, restart. A second QR is printed for that URL.

## 🧪 Status & limitations

- **Beta.** The wire protocol and mappings may change between commits.
- **One virtual gamepad per server instance** — the manager is single-slot today (KISS).
- **Linux only.** Coupled to `/dev/uinput`; Windows / macOS would need a different virtual-driver backend.
- **No authentication.** Anyone on the same Wi-Fi who knows the URL can drive the pad. Keep it on a trusted network or behind a tunnel that does auth.
- **No automated tests in this branch yet.**

## 📜 License

GPL-3.0 — see [LICENSE](LICENSE).

## 📞 Contact

- GitHub: **[@ZenonEl](https://github.com/ZenonEl)**

---

<div align="center">

[⭐ Star](https://github.com/ZenonEl/RemoteGamepad) · [🐛 Issue](https://github.com/ZenonEl/RemoteGamepad/issues) · [💡 Idea](https://github.com/ZenonEl/RemoteGamepad/issues)

</div>
