import uvicorn
from loguru import logger
import sys

if __name__ == "__main__":
    try:
        # Напоминание про KISS: Пока хардкодим, конфиг подключим позже
        logger.info("🚀 Starting RemoteGamepad (Linux Native)...")
        
        # В будущем здесь будет запуск FastAPI
        # uvicorn.run("src.api.app:app", host="0.0.0.0", port=5002, reload=True)
        
        logger.success("Environment is ready. Waiting for API implementation.")
        
    except KeyboardInterrupt:
        logger.info("Stopping...")
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)
