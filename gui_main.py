#!/usr/bin/env python3
"""
RemoteGamepad GUI launcher
Запуск GUI версии сервера

Использование:
    .venv/bin/python gui_main.py
    или
    flet run gui_main.py
"""
import asyncio
import logging
import sys
from pathlib import Path

# Добавляем src в путь для импортов
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.gui.app import run_gui_app
from src.config.settings import settings


def setup_logging() -> None:
    """Настройка логирования"""
    logging.basicConfig(
        level=getattr(logging, settings.server.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(settings.logs_dir / settings.log_file)
        ]
    )


async def main() -> None:
    """Главная функция"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("🎮 Starting RemoteGamepad GUI...")
        logger.info(f"📁 Project root: {settings.project_root}")
        logger.info(f"🌐 Server config: {settings.server.host}:{settings.server.port}")
        
        await run_gui_app()
        
    except KeyboardInterrupt:
        logger.info("👋 Application stopped by user")
    except Exception as e:
        logger.error(f"❌ Application error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())