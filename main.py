import uvicorn
import os
import sys
import socket
import qrcode
from loguru import logger

from src.config import PORT, EXTERNAL_URL

def get_local_ip():
    """Получает локальный IP адрес машины в сети"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def print_qr(url):
    """Рисует QR код в консоли"""
    qr = qrcode.QRCode()
    qr.add_data(url)
    qr.make(fit=True)
    # Выводим в консоль инвертированными цветами (для темных терминалов)
    qr.print_ascii(invert=True)

if __name__ == "__main__":
    try:
        # 1. Проверка прав
        if not os.access('/dev/uinput', os.W_OK) and os.path.exists('/dev/uinput'):
            logger.warning("⚠️  Нет прав записи в /dev/uinput! Геймпад может не создаться.")
            logger.warning("👉 Запустите: sudo bash scripts/setup_udev.sh")

        # 2. Рисуем локальный QR
        local_ip = get_local_ip()
        local_url = f"http://{local_ip}:{PORT}"
        
        print("\n" + "="*50)
        print(f"🏠 ЛОКАЛЬНАЯ СЕТЬ (Wi-Fi)")
        print(f"🔗 Откройте: {local_url}")
        print("="*50)
        try:
            print_qr(local_url)
        except Exception:
            logger.warning("Не удалось отрисовать локальный QR-код")

        # 3. Рисуем внешний QR (если есть туннель)
        if EXTERNAL_URL:
            print("\n" + "="*50)
            print(f"🌍 ВНЕШНЯЯ СЕТЬ (zrok / ngrok)")
            print(f"🔗 Откройте: {EXTERNAL_URL}")
            print("="*50)
            try:
                print_qr(EXTERNAL_URL)
            except Exception:
                logger.warning("Не удалось отрисовать внешний QR-код")
                
        print("\n🎮 Сервер запущен. Ожидание подключений...\n")
        print("="*50)  # 🔧 Разделитель после QR-кодов

        # 4. Запуск сервера
        uvicorn.run("src.api.server:app", host="0.0.0.0", port=PORT, log_level="info")
        
    except KeyboardInterrupt:
        logger.info("\n👋 Сервер остановлен.")
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        sys.exit(1)
