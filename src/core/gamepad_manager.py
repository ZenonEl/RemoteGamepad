"""
Менеджер виртуальных геймпадов на базе evdev
"""
import asyncio
import logging
from typing import Dict, Optional, List
import time

from evdev import UInput, AbsInfo, ecodes as e

from ..utils.types import GamepadEvent, GamepadManager as IGamepadManager
from ..core.events import EventBus
from ..config.settings import settings

logger = logging.getLogger(__name__)


class VirtualGamepadDevice:
    """Виртуальный геймпад на основе evdev UInput"""
    
    def __init__(self, gamepad_id: int, name: str = "RemoteGamepad"):
        self.gamepad_id = gamepad_id
        self.name = f"{name}-{gamepad_id}"
        self.device: Optional[UInput] = None
        self.created_at = time.time()
        
        # Настройка capabilities геймпада
        self.caps = {
            e.EV_KEY: [
                e.BTN_SOUTH,  # A
                e.BTN_EAST,   # B  
                e.BTN_NORTH,  # Y
                e.BTN_WEST,   # X
                e.BTN_TL,     # LB
                e.BTN_TR,     # RB
                e.BTN_SELECT, # Back
                e.BTN_START,  # Start
                e.BTN_MODE,   # Guide
                e.BTN_THUMBL, # Left Stick
                e.BTN_THUMBR, # Right Stick
            ],
            e.EV_ABS: [
                # Левый стик
                (e.ABS_X, AbsInfo(0, -32768, 32767, 0, 0, 0)),
                (e.ABS_Y, AbsInfo(0, -32768, 32767, 0, 0, 0)),
                # Правый стик  
                (e.ABS_RX, AbsInfo(0, -32768, 32767, 0, 0, 0)),
                (e.ABS_RY, AbsInfo(0, -32768, 32767, 0, 0, 0)),
                # Триггеры
                (e.ABS_Z, AbsInfo(0, 0, 255, 0, 0, 0)),    # LT
                (e.ABS_RZ, AbsInfo(0, 0, 255, 0, 0, 0)),   # RT
                # D-Pad
                (e.ABS_HAT0X, AbsInfo(0, -1, 1, 0, 0, 0)),
                (e.ABS_HAT0Y, AbsInfo(0, -1, 1, 0, 0, 0)),
            ]
        }
        
        # Состояние D-Pad
        self.dpad_state = {'x': 0, 'y': 0}
        
        logger.debug(f"VirtualGamepad {self.gamepad_id} configured")
    
    async def create(self) -> bool:
        """Создание виртуального устройства"""
        try:
            self.device = UInput(
                self.caps,
                name=self.name,
                vendor=0x045e,   # Microsoft
                product=0x028e,  # Xbox 360 Controller
                version=0x0110,
                bustype=e.BUS_USB
            )
            logger.info(f"Virtual gamepad {self.gamepad_id} created: {self.name}")
            return True
            
        except Exception as ex:
            logger.error(f"Failed to create gamepad {self.gamepad_id}: {ex}")
            return False
    
    async def destroy(self) -> None:
        """Уничтожение виртуального устройства"""
        if self.device:
            try:
                self.device.close()
                logger.info(f"Virtual gamepad {self.gamepad_id} destroyed")
            except Exception as ex:
                logger.error(f"Error destroying gamepad {self.gamepad_id}: {ex}")
            finally:
                self.device = None
    
    async def send_button_event(self, button_code: int, value: int) -> None:
        """Отправка события кнопки"""
        if not self.device:
            return
            
        try:
            self.device.write(e.EV_KEY, button_code, value)
            self.device.syn()
            logger.debug(f"Gamepad {self.gamepad_id}: button {button_code} = {value}")
        except Exception as ex:
            logger.error(f"Error sending button event: {ex}")
    
    async def send_axis_event(self, axis_code: int, value: int) -> None:
        """Отправка события оси"""
        if not self.device:
            return
            
        try:
            self.device.write(e.EV_ABS, axis_code, value)
            self.device.syn()
            logger.debug(f"Gamepad {self.gamepad_id}: axis {axis_code} = {value}")
        except Exception as ex:
            logger.error(f"Error sending axis event: {ex}")
    
    async def send_dpad_event(self, x: int, y: int) -> None:
        """Отправка события D-Pad"""
        if not self.device:
            return
            
        try:
            self.device.write(e.EV_ABS, e.ABS_HAT0X, x)
            self.device.write(e.EV_ABS, e.ABS_HAT0Y, y)
            self.device.syn()
            
            self.dpad_state['x'] = x
            self.dpad_state['y'] = y
            
            logger.debug(f"Gamepad {self.gamepad_id}: dpad ({x}, {y})")
        except Exception as ex:
            logger.error(f"Error sending dpad event: {ex}")


class GamepadManagerImpl(IGamepadManager):
    """Реализация менеджера виртуальных геймпадов"""
    
    def __init__(self, event_bus: EventBus):
        self._gamepads: Dict[int, VirtualGamepadDevice] = {}
        self._client_gamepad_map: Dict[str, int] = {}
        self._event_bus = event_bus
        self._next_gamepad_id = 1
        self._lock = asyncio.Lock()
        
        # Маппинг кнопок
        self._button_map = {
            "BtnA": e.BTN_SOUTH,
            "BtnB": e.BTN_EAST,
            "BtnX": e.BTN_NORTH, 
            "BtnY": e.BTN_WEST,
            "BtnBack": e.BTN_SELECT,
            "BtnStart": e.BTN_START,
            "BtnThumbL": e.BTN_THUMBL,
            "BtnThumbR": e.BTN_THUMBR,
            "BtnShoulderL": e.BTN_TL,
            "BtnShoulderR": e.BTN_TR,
        }
        
        # Маппинг осей
        self._axis_map = {
            'AxisLx': e.ABS_X,
            'AxisLy': e.ABS_Y,
            'AxisRx': e.ABS_RX,
            'AxisRy': e.ABS_RY,
            'TriggerL': e.ABS_Z,
            'TriggerR': e.ABS_RZ
        }
        
        logger.info("GamepadManager initialized")
    
    async def create_gamepad(self, client_id: str) -> Optional[int]:
        """Создание виртуального геймпада для клиента"""
        async with self._lock:
            # Проверяем, есть ли уже геймпад для этого клиента
            if client_id in self._client_gamepad_map:
                return self._client_gamepad_map[client_id]
            
            # Проверяем лимит геймпадов
            if len(self._gamepads) >= settings.max_gamepads:
                logger.warning(f"Cannot create gamepad for {client_id}: limit reached")
                return None
            
            # Создаем новый геймпад
            gamepad_id = self._next_gamepad_id
            self._next_gamepad_id += 1
            
            gamepad = VirtualGamepadDevice(
                gamepad_id, 
                settings.gamepad_name_template.format(id=gamepad_id)
            )
            
            if await gamepad.create():
                self._gamepads[gamepad_id] = gamepad
                self._client_gamepad_map[client_id] = gamepad_id
                
                logger.info(f"Created gamepad {gamepad_id} for client {client_id}")
                return gamepad_id
            
            return None
    
    async def remove_gamepad(self, gamepad_id: int) -> bool:
        """Удаление виртуального геймпада"""
        async with self._lock:
            if gamepad_id not in self._gamepads:
                return False
            
            gamepad = self._gamepads[gamepad_id]
            await gamepad.destroy()
            
            # Удаляем из мапинга клиентов
            client_to_remove = None
            for client_id, gpad_id in self._client_gamepad_map.items():
                if gpad_id == gamepad_id:
                    client_to_remove = client_id
                    break
            
            if client_to_remove:
                del self._client_gamepad_map[client_to_remove]
            
            del self._gamepads[gamepad_id]
            
            logger.info(f"Removed gamepad {gamepad_id}")
            return True
    
    async def send_event(self, gamepad_id: int, event: GamepadEvent) -> None:
        """Отправка события в виртуальный геймпад"""
        async with self._lock:
            if gamepad_id not in self._gamepads:
                logger.warning(f"Gamepad {gamepad_id} not found")
                return
            
            gamepad = self._gamepads[gamepad_id]
            
            if event.event_type.value == "button_press" or event.event_type.value == "button_release":
                if event.button_code and event.button_code in self._button_map:
                    button_evdev_code = self._button_map[event.button_code]
                    value = 1 if event.event_type.value == "button_press" else 0
                    await gamepad.send_button_event(button_evdev_code, value)
            
            elif event.event_type.value == "axis_move":
                if event.axis_name and event.axis_name in self._axis_map:
                    axis_evdev_code = self._axis_map[event.axis_name]
                    # Конвертируем значение в диапазон evdev
                    scaled_value = int(event.value * 32767)
                    if 'Ly' in event.axis_name or 'Ry' in event.axis_name:
                        scaled_value = -scaled_value  # Инвертируем Y оси
                    await gamepad.send_axis_event(axis_evdev_code, scaled_value)
            
            elif event.event_type.value == "dpad":
                # D-Pad события нужно парсить из данных события
                # Это будет реализовано при обработке входящих данных
                pass
    
    async def get_gamepad_for_client(self, client_id: str) -> Optional[int]:
        """Получение ID геймпада для клиента"""
        async with self._lock:
            return self._client_gamepad_map.get(client_id)
    
    async def get_gamepad_count(self) -> int:
        """Получение количества активных геймпадов"""
        async with self._lock:
            return len(self._gamepads)
    
    async def get_gamepad_info(self) -> List[Dict]:
        """Получение информации о всех геймпадах"""
        async with self._lock:
            info = []
            for gamepad_id, gamepad in self._gamepads.items():
                # Находим клиента для этого геймпада
                client_id = None
                for cid, gid in self._client_gamepad_map.items():
                    if gid == gamepad_id:
                        client_id = cid
                        break
                
                info.append({
                    "gamepad_id": gamepad_id,
                    "name": gamepad.name,
                    "client_id": client_id,
                    "created_at": gamepad.created_at,
                    "device_path": getattr(gamepad.device, 'device', None) if gamepad.device else None
                })
            
            return info
    
    async def cleanup(self) -> None:
        """Очистка всех геймпадов"""
        async with self._lock:
            for gamepad in self._gamepads.values():
                await gamepad.destroy()
            
            self._gamepads.clear()
            self._client_gamepad_map.clear()
            
            logger.info("All gamepads cleaned up")