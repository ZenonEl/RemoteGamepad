"""
Настройки приложения
"""
import os
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field

from ..utils.types import ServerConfig


@dataclass
class AppSettings:
    """Настройки приложения"""
    
    # Сервер
    server: ServerConfig = field(default_factory=ServerConfig)
    
    # Пути
    project_root: Path = field(default_factory=lambda: Path(__file__).parent.parent.parent)
    config_dir: Path = field(default_factory=lambda: Path(__file__).parent.parent / "config")
    logs_dir: Path = field(default_factory=lambda: Path(__file__).parent.parent.parent / "logs")
    
    # GUI
    gui_title: str = "RemoteGamepad Server"
    gui_width: int = 800
    gui_height: int = 600
    gui_theme: str = "dark"
    
    # Безопасность
    require_pin: bool = False
    pin_code: Optional[str] = None
    allowed_ips: list[str] = field(default_factory=list)
    session_timeout: int = 3600  # секунды
    
    # Виртуальные геймпады
    max_gamepads: int = 4
    gamepad_name_template: str = "RemoteGamepad-{id}"
    
    # Логирование
    log_file: str = "remoteGamepad.log"
    log_rotation: str = "1 MB"
    log_retention: int = 10  # файлов
    
    def __post_init__(self) -> None:
        """Инициализация после создания объекта"""
        # Создаем директории если их нет
        self.logs_dir.mkdir(exist_ok=True, parents=True)
        
        # Загружаем настройки из переменных окружения
        self._load_from_env()
    
    def _load_from_env(self) -> None:
        """Загрузка настроек из переменных окружения"""
        # Сервер
        if host := os.getenv("RG_HOST"):
            self.server.host = host
        else:
            # По умолчанию используем 0.0.0.0 для всех интерфейсов
            self.server.host = "0.0.0.0"
        
        if port := os.getenv("RG_PORT"):
            self.server.port = int(port)
        
        if debug := os.getenv("RG_DEBUG"):
            self.server.debug = debug.lower() in ("true", "1", "yes")
        
        # Безопасность
        if pin := os.getenv("RG_PIN"):
            self.pin_code = pin
            self.require_pin = True
        
        if ips := os.getenv("RG_ALLOWED_IPS"):
            self.allowed_ips = [ip.strip() for ip in ips.split(",")]
        
        # Геймпады
        if max_pads := os.getenv("RG_MAX_GAMEPADS"):
            self.max_gamepads = int(max_pads)
    
    def to_dict(self) -> dict:
        """Конвертация в словарь для сериализации"""
        return {
            "server": {
                "host": self.server.host,
                "port": self.server.port,
                "max_clients": self.server.max_clients,
                "debug": self.server.debug,
                "log_level": self.server.log_level,
                "pin_code": self.server.pin_code,
            },
            "gui": {
                "title": self.gui_title,
                "width": self.gui_width,
                "height": self.gui_height,
                "theme": self.gui_theme,
            },
            "security": {
                "require_pin": self.require_pin,
                "pin_code": self.pin_code,
                "allowed_ips": self.allowed_ips,
                "session_timeout": self.session_timeout,
            },
            "gamepads": {
                "max_gamepads": self.max_gamepads,
                "name_template": self.gamepad_name_template,
            }
        }


# Глобальные настройки
settings = AppSettings()