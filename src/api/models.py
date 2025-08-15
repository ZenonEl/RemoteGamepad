"""
Pydantic модели для API
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum

class GamepadButtonEvent(BaseModel):
    """Событие кнопки геймпада"""
    name: str = Field(..., description="Имя кнопки (BtnA, BtnB, и т.д.)")
    pressed: bool = Field(..., description="Нажата ли кнопка")
    value: float = Field(default=0.0, description="Значение кнопки (0.0 или 1.0)")

class GamepadAxisData(BaseModel):
    """Данные осей геймпада"""
    left_stick: Dict[str, float] = Field(..., description="Левый стик {x, y}")
    right_stick: Dict[str, float] = Field(..., description="Правый стик {x, y}")

class GamepadInputData(BaseModel):
    """Входящие данные от клиента"""
    type: str = Field(..., description="Тип события: axis, buttons")
    client_id: Optional[str] = Field(None, description="ID клиента")
    
    # Данные осей
    axes: Optional[GamepadAxisData] = Field(None, description="Данные осей")
    
    # Данные кнопок
    buttons: Optional[List[GamepadButtonEvent]] = Field(None, description="События кнопок")
    
    # Метаданные
    timestamp: Optional[float] = Field(None, description="Временная метка")

class ClientConnectionInfo(BaseModel):
    """Информация для подключения клиента"""
    client_id: str = Field(..., description="Уникальный ID клиента")
    ip_address: str = Field(..., description="IP адрес клиента")
    user_agent: Optional[str] = Field(None, description="User Agent браузера")
    session_token: Optional[str] = Field(None, description="Токен сессии")

class ServerStatusResponse(BaseModel):
    """Ответ статуса сервера"""
    status: str = Field(..., description="Статус: running, stopped")
    uptime: int = Field(..., description="Время работы в секундах")
    clients_count: int = Field(..., description="Количество подключенных клиентов")
    server_info: Dict[str, Any] = Field(..., description="Информация о сервере")

class ConnectionResponse(BaseModel):
    """Ответ на подключение"""
    success: bool = Field(..., description="Успешно ли подключение")
    client_id: str = Field(..., description="ID клиента")
    gamepad_id: Optional[int] = Field(None, description="ID назначенного геймпада")
    message: str = Field(..., description="Сообщение")

class ErrorResponse(BaseModel):
    """Стандартный ответ об ошибке"""
    error: bool = Field(True, description="Флаг ошибки")
    message: str = Field(..., description="Описание ошибки")
    code: Optional[str] = Field(None, description="Код ошибки")

class WebSocketMessageType(str, Enum):
    """Типы WebSocket сообщений"""
    GAMEPAD_EVENT = "gamepad_event"
    CLIENT_CONNECTED = "client_connected"
    CLIENT_DISCONNECTED = "client_disconnected"
    SERVER_STATUS = "server_status"
    ERROR = "error"
    PING = "ping"
    PONG = "pong"

class WebSocketMessage(BaseModel):
    """Базовое WebSocket сообщение"""
    type: WebSocketMessageType = Field(..., description="Тип сообщения")
    data: Dict[str, Any] = Field(..., description="Данные сообщения")
    timestamp: Optional[float] = Field(None, description="Временная метка")
    client_id: Optional[str] = Field(None, description="ID отправителя")

class QRCodeRequest(BaseModel):
    """Запрос генерации QR кода"""
    include_pin: bool = Field(default=False, description="Включить PIN в QR код")
    size: int = Field(default=200, description="Размер QR кода в пикселях")
    format: str = Field(default="png", description="Формат изображения")

class GamepadConfigModel(BaseModel):
    """Конфигурация виртуального геймпада"""
    name: str = Field(..., description="Имя геймпада")
    vendor_id: int = Field(default=0x045e, description="Vendor ID")
    product_id: int = Field(default=0x028e, description="Product ID") 
    version: int = Field(default=0x0110, description="Версия")
    enable_force_feedback: bool = Field(default=False, description="Включить силовую обратную связь")