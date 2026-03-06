import uvicorn
import os
import sys
import socket
import qrcode
from loguru import logger

# Простая конфигурация
PORT = 5002

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

        # 2. Получение IP и генерация ссылки
        local_ip = get_local_ip()
        url = f"http://{local_ip}:{PORT}"
        
        print("\n" + "="*40)
        print(f"🎮 RemoteGamepad готов к работе!")
        print(f"🔗 Откройте на телефоне: {url}")
        print("="*40 + "\n")
        
        # 3. Рисуем QR
        try:
            print_qr(url)
        except Exception:
            logger.warning("Не удалось отрисовать QR-код (возможно, шрифт терминала не поддерживает)")

        # 4. Запуск сервера
        uvicorn.run("src.api.server:app", host="0.0.0.0", port=PORT, log_level="warning")
        
    except KeyboardInterrupt:
        logger.info("\n👋 Сервер остановлен.")
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        sys.exit(1)
