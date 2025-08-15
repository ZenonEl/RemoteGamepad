#!/usr/bin/env python3
"""
RemoteGamepad - Main launcher
Запуск сервера для виртуального геймпада
"""

if __name__ == "__main__":
    print("🎮 Запуск RemoteGamepad сервера...")
    print("Для остановки нажмите Ctrl+C")
    try:
        import server
        server.run_flask()
    except KeyboardInterrupt:
        print("\n🛑 Сервер остановлен")
    except Exception as e:
        print(f"❌ Ошибка запуска: {e}")
        print("💡 Попробуйте: python server.py")
