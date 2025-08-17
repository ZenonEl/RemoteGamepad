# 🎮 RemoteGamepad

[![License](https://img.shields.io/badge/license-GPL%203-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-beta-green.svg)](https://github.com/ZenonEl/RemoteGamepad/releases)
[![Python](https://img.shields.io/badge/python-3.13.5+-blue.svg)](https://python.org)
[![Platform](https://img.shields.io/badge/platform-Linux-lightgrey.svg)](https://github.com/ZenonEl/RemoteGamepad)
[![Language](https://img.shields.io/badge/language-EN%20%7C%20RU-blue.svg)](README.ru.md)

> **Transform your smartphone into a wireless gamepad for your PC!** 🚀

RemoteGamepad is an innovative application that allows you to use your smartphone as a wireless gamepad controller. It creates a virtual joystick on your PC that receives real-time input from your mobile device through a web interface.

**Perfect for situations where you can't connect a gamepad directly to your PC** - whether due to hardware limitations, driver issues, or simply wanting to use your mobile device as a controller. This project provides a seamless solution for wireless gamepad control.

## ✨ Features

- 🎯 **Real-time Control**: Instant response with minimal latency
- 🌐 **Web-based Interface**: Works in any modern browser
- 📱 **Cross-platform**: Android, iOS, and desktop browsers supported
- 🎮 **Full Basic Gamepad Support**: Buttons, analog sticks, triggers, and D-pad
- 🔌 **Virtual Device**: Creates a virtual Xbox 360 controller on your PC
- 🎨 **Modern UI**: Beautiful, responsive web interface
- 🌍 **Multi-language**: English and Russian support
- 🔒 **Secure**: Local network communication only

## 🚀 Quick Start

### Prerequisites

- **PC**: Linux
- **Python 3.13.5+** installed
- **Smartphone/Tablet** with a modern browser
- Both devices on the **same local network**

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/ZenonEl/RemoteGamepad.git
   cd RemoteGamepad
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application:**
   ```bash
   flet run gui_main.py
   ```

5. **Connect your device:**
   - Open your browser on your smartphone
   - Navigate to the displayed IP address (e.g., `http://192.168.1.100:5002`)
   - Connect your gamepad to your mobile device
   - Start gaming! 🎮

## 📱 How It Works

```
[Gamepad] → [Smartphone Browser] → [WiFi] → [PC Server] → [Virtual Controller] → [Games]
```

1. **Connect** your physical gamepad to your smartphone
2. **Open** the web interface in your mobile browser
3. **Server** creates a virtual Xbox 360 controller on your PC
4. **Input** from your mobile device is translated to virtual controller events
5. **Games** recognize the virtual controller as a real gamepad

> **⚠️ Note:** This project is currently in **beta development** stage and will continue to evolve with new features and improvements.


## 🔧 Troubleshooting

### Common Issues

**"Permission denied" error on Linux:**
```bash
sudo usermod -a -G input $USER
# Log out and back in, or run:
newgrp input
```

**Controller not detected:**
- Ensure both devices are on the same network
- Check firewall settings
- Verify the server is running and accessible

**High latency:**
- Reduce `INTERVAL_SEND_TIMING` in settings
- Check network quality
- Close unnecessary applications


## 📁 Project Structure

```
RemoteGamepad/
├── src/
│   ├── api/           # FastAPI server implementation
│   ├── core/          # Core gamepad management
│   ├── gui/           # Flet GUI application
│   └── utils/         # Utility functions
├── static/            # Web assets (CSS, JS)
├── templates/         # HTML templates
├── config/            # Configuration files
├── lang/              # Localization files
├── server.py          # Main Flask server
└── main.py            # GUI application entry point
```

## 🌍 Localization

The application supports multiple languages:

- **English** (`lang/en.json`) - [README.md](README.md)
- **Russian** (`lang/ru.json`) - [README.ru.md](README.ru.md)

Add new languages by creating JSON files in the `lang/` directory.


## 🙏 Acknowledgments

- **evdev** library for Linux input device support
- **FastAPI** for the web server framework
- **Flet** for the desktop GUI framework
- **Web Gamepad API** for mobile gamepad support

> **Note:** This project is currently in **beta development** and will continue to improve with new features and enhancements in the future.

## 📞 Contact

- **GitHub**: [@ZenonEl](https://github.com/ZenonEl)
- **Mastodon**: [@ZenonEl@mastodon.ml](https://mastodon.ml/@ZenonEl)
- **Project**: [RemoteGamepad](https://github.com/ZenonEl/RemoteGamepad)


---

<div align="center">

**Made with ❤️ by ZenonEl**

*Transform your gaming experience with RemoteGamepad!*

[⭐ Star this repo](https://github.com/ZenonEl/RemoteGamepad) | [🐛 Report Bug](https://github.com/ZenonEl/RemoteGamepad/issues) | [💡 Request Feature](https://github.com/ZenonEl/RemoteGamepad/issues)

</div>

## 📄 License

This project is licensed under the **GPL 3.0 License** - see the [LICENSE](LICENSE) file for details.
