"""
Типы данных для RemoteGamepad
"""
from dataclasses import dataclass
from typing import Dict, List, Optional, Protocol, Callable, Any
from enum import Enum
import asyncio


class ClientStatus(Enum):
    """Статус клиента"""
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ACTIVE = "active"
    DISCONNECTED = "disconnected"
    ERROR = "error"


class GamepadEventType(Enum):
    """Типы событий геймпада"""
    BUTTON_PRESS = "button_press"
    BUTTON_RELEASE = "button_release"
    AXIS_MOVE = "axis_move"
    DPAD = "dpad"


@dataclass
class ClientInfo:
    """Информация о клиенте"""
    client_id: str
    ip_address: str
    user_agent: str
    connected_at: float
    status: ClientStatus
    gamepad_id: Optional[int] = None
    profile_name: Optional[str] = None


@dataclass
class GamepadEvent:
    """Событие геймпада"""
    client_id: str
    event_type: GamepadEventType
    button_code: Optional[str] = None
    axis_name: Optional[str] = None
    value: float = 0.0
    value_x: Optional[int] = None  # Для D-PAD X координата
    value_y: Optional[int] = None  # Для D-PAD Y координата
    timestamp: float = 0.0


@dataclass
class ServerConfig:
    """Конфигурация сервера"""
    host: str = "0.0.0.0"
    port: int = 5002
    max_clients: int = 4
    debug: bool = False
    log_level: str = "INFO"
    pin_code: Optional[str] = None


class EventHandler(Protocol):
    """Протокол для обработчиков событий"""
    async def __call__(self, event: GamepadEvent) -> None: ...


class ClientManager(Protocol):
    """Протокол для менеджера клиентов"""
    async def add_client(self, client_info: ClientInfo) -> bool: ...
    async def remove_client(self, client_id: str) -> bool: ...
    async def get_clients(self) -> List[ClientInfo]: ...
    async def get_client(self, client_id: str) -> Optional[ClientInfo]: ...
    async def generate_client_id(self, ip_address: str) -> str: ...
    async def assign_gamepad(self, client_id: str, gamepad_id: int) -> bool: ...


class GamepadManager(Protocol):
    """Протокол для менеджера геймпадов"""
    async def create_gamepad(self, client_id: str) -> Optional[int]: ...
    async def remove_gamepad(self, gamepad_id: int) -> bool: ...
    async def send_event(self, gamepad_id: int, event: GamepadEvent) -> None: ...
    async def get_gamepad_for_client(self, client_id: str) -> Optional[int]: ...
    async def get_gamepad_count(self) -> int: ...
    async def get_gamepad_info(self) -> List[Dict]: ...
    async def cleanup(self) -> None: ...


EventCallback = Callable[[GamepadEvent], asyncio.Task[None]]
ClientCallback = Callable[[ClientInfo], asyncio.Task[None]]