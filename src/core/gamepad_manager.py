"""
Менеджер виртуальных геймпадов на базе evdev.
Отвечает за трансляцию событий в ядро Linux.
"""
import asyncio
from typing import Optional
import time

from evdev import UInput, AbsInfo, ecodes as e
from loguru import logger

from .mapping_config import BUTTON_MAP, AXIS_MAP

logger = logger.bind(module="gamepad")


class VirtualGamepadDevice:
    """Виртуальный геймпад на основе evdev UInput"""
    
    def __init__(self, gamepad_id: int, name: str = "RemoteGamepad"):
        self.gamepad_id = gamepad_id
        self.name = f"{name}-{gamepad_id}"
        self.device: Optional[UInput] = None
        self.created_at = time.time()
        
        # Настройка capabilities геймпада (наш виртуальный джойстик)
        # ВАЖНО: Используем явные значения AbsInfo, как в старом рабочем коде,
        # чтобы избежать проблем с дефолтными значениями fuzz/flat в ядре Linux.
        self.caps = {
            e.EV_KEY: list(BUTTON_MAP.values()),
            e.EV_ABS: [
                # Стики (16-bit signed: -32768..32767)
                (e.ABS_X, AbsInfo(value=0, min=-32768, max=32767, fuzz=0, flat=0, resolution=0)),
                (e.ABS_Y, AbsInfo(value=0, min=-32768, max=32767, fuzz=0, flat=0, resolution=0)),
                (e.ABS_RX, AbsInfo(value=0, min=-32768, max=32767, fuzz=0, flat=0, resolution=0)),
                (e.ABS_RY, AbsInfo(value=0, min=-32768, max=32767, fuzz=0, flat=0, resolution=0)),
                
                # Триггеры (8-bit unsigned: 0..255)
                # Критично: min=0, max=255.
                (e.ABS_Z, AbsInfo(value=0, min=0, max=255, fuzz=0, flat=0, resolution=0)),
                (e.ABS_RZ, AbsInfo(value=0, min=0, max=255, fuzz=0, flat=0, resolution=0)),
                
                # D-Pad (Hat switch: -1..1)
                (e.ABS_HAT0X, AbsInfo(value=0, min=-1, max=1, fuzz=0, flat=0, resolution=0)),
                (e.ABS_HAT0Y, AbsInfo(value=0, min=-1, max=1, fuzz=0, flat=0, resolution=0)),
            ]
        }
        
        # 🔧 ТРЕКИНГ состояния триггеров (для отправки button-событий)
        self._trigger_state = {"TriggerL": False, "TriggerR": False}
    
    def create(self) -> bool:
        """Создание виртуального устройства в системе"""
        try:
            # ВАЖНО: Имя устройства должно быть СТРОГО 'Microsoft X-Box 360 pad'.
            # Многие игры, тестеры и библиотеки (в т.ч. SDL2/Steam) определяют
            # возможности геймпада по его имени! Если имя другое, они используют
            # "generic" профиль, игнорируют триггеры (оси Z/RZ) и путают местами X/Y.
            self.device = UInput(
                self.caps,
                name='Microsoft X-Box 360 pad',  
                vendor=0x045e,   
                product=0x028e,  
                version=0x0110,
                bustype=e.BUS_USB
            )
            logger.info(f"✅ Создан виртуальный геймпад: {self.name} (как Xbox 360)")
            return True
        except PermissionError:
            logger.error("❌ Нет прав доступа к /dev/uinput! Запустите скрипт scripts/setup_udev.sh")
            return False
        except Exception as ex:
            logger.error(f"❌ Ошибка создания геймпада {self.gamepad_id}: {ex}")
            return False
    
    def destroy(self) -> None:
        """Удаление виртуального устройства"""
        if self.device:
            try:
                self.device.close()
                logger.info(f"🗑️ Геймпад {self.name} отключен")
            except Exception as ex:
                logger.error(f"Ошибка при удалении геймпада {self.name}: {ex}")
            finally:
                self.device = None
    
    def send_button(self, button_name: str, is_pressed: bool) -> None:
        """Отправка события кнопки"""
        if not self.device or button_name not in BUTTON_MAP:
            return
            
        btn_code = BUTTON_MAP[button_name]
        value = 1 if is_pressed else 0
        self.device.write(e.EV_KEY, btn_code, value)
        self.device.syn()
    
    def send_axis(self, axis_name: str, value: float) -> None:
        """Отправка события оси со скалированием (0.0..1.0 -> -32768..32767)"""
        if not self.device or axis_name not in AXIS_MAP:
            return
            
        axis_code = AXIS_MAP[axis_name]

        # Скалирование значения
        if axis_name in ['TriggerL', 'TriggerR']:
            # Триггеры: 0.0 до 1.0 -> 0 до 255
            scaled_value = int(value * 255)
        else:
            # Стики: -1.0 до 1.0 -> -32768 до 32767
            scaled_value = int(value * 32767)

        self.device.write(e.EV_ABS, axis_code, scaled_value)
        self.device.syn()

    def send_dpad(self, x: int, y: int) -> None:
        """Отправка события крестовины (D-Pad)"""
        if not self.device:
            return

        self.device.write(e.EV_ABS, AXIS_MAP['DpadX'], x)
        self.device.write(e.EV_ABS, AXIS_MAP['DpadY'], y)
        self.device.syn()

    def process_trigger_as_button(self, name: str, value) -> None:
        """
        🔧 ИСПРАВЛЕНО: Обработка триггеров как ОСЕЙ + КНОПОК одновременно
        Многие тестеры проверяют оба типа событий!
        """
        if not self.device:
            return
            
        # Определяем код оси
        trigger_code = e.ABS_Z if name == "TriggerL" else e.ABS_RZ
        
        # Конвертируем значение в 0-255
        if isinstance(value, bool):
            trigger_value = 255 if value else 0
        else:
            trigger_value = int(float(value) * 255)
        
        self.device.write(e.EV_ABS, trigger_code, trigger_value)
        
        # Порог срабатывания кнопки: >10% нажатия
        is_pressed = trigger_value > 25
        
        # Отправляем button-событие только если состояние изменилось
        if self._trigger_state.get(name) != is_pressed:
            self._trigger_state[name] = is_pressed
            btn_code = BUTTON_MAP.get(name)
            if btn_code:
                self.device.write(e.EV_KEY, btn_code, 1 if is_pressed else 0)
                logger.debug(f"🎯 Trigger {name} button event: {is_pressed} (value={trigger_value})")
        
        self.device.syn()

class GamepadManager:
    """Оркестратор виртуальных геймпадов (KISS - пока поддерживаем 1 геймпад)"""
    
    def __init__(self):
        self.gamepad: Optional[VirtualGamepadDevice] = None
        self._lock = asyncio.Lock()
        logger.info("GamepadManager инициализирован")
    
    async def create_gamepad(self, client_id: str) -> bool:
        """Создает геймпад для клиента (если его еще нет)"""
        async with self._lock:
            if self.gamepad is not None:
                # Геймпад уже создан, переиспользуем (KISS)
                return True
                
            gamepad = VirtualGamepadDevice(gamepad_id=1, name="RemoteGamepad")
            if gamepad.create():
                self.gamepad = gamepad
                return True
            return False
            
    async def remove_gamepad(self) -> None:
        """Удаляет активный геймпад"""
        async with self._lock:
            if self.gamepad:
                self.gamepad.destroy()
                self.gamepad = None

    async def get_active_gamepad(self) -> Optional[VirtualGamepadDevice]:
        """Возвращает текущий геймпад"""
        return self.gamepad

    async def cleanup(self) -> None:
        """Очистка при завершении работы сервера"""
        await self.remove_gamepad()