import uvicorn
import os
import sys
from loguru import logger

# Простая конфигурация (можно вынести в .env)
HOST = "0.0.0.0"
PORT = 5002

if __name__ == "__main__":
    try:
        # Проверка прав доступа к uinput
        if not os.access('/dev/uinput', os.W_OK):
            logger.warning("⚠️  WARNING: No write access to /dev/uinput!")
            logger.warning("👉 Run: sudo bash scripts/setup_udev.sh")
            # Мы не выходим, так как может быть пользователь просто тестирует UI
        
        logger.info(f"🚀 RemoteGamepad Server starting on http://{HOST}:{PORT}")
        logger.info("📱 Connect your phone to this IP address")
        
        # Запуск сервера
        # workers=1 важно для WebSocket и Singleton паттерна в KISS архитектуре
        uvicorn.run("src.api.server:app", host=HOST, port=PORT, reload=False, workers=1)
        
    except KeyboardInterrupt:
        logger.info("👋 Server stopped by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)
