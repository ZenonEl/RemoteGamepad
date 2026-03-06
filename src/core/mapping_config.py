"""
Конфигурация маппинга кнопок и осей.
Перенесено из старой рабочей версии.
"""
from evdev import ecodes as e

# Маппинг имен кнопок (из JS Frontend) в коды Linux Evdev
BUTTON_MAP = {
    "BtnA": e.BTN_SOUTH,
    "BtnB": e.BTN_EAST,
    "BtnX": e.BTN_WEST,
    "BtnY": e.BTN_NORTH,
    "BtnBack": e.BTN_SELECT,
    "BtnStart": e.BTN_START,
    "BtnThumbL": e.BTN_THUMBL,
    "BtnThumbR": e.BTN_THUMBR,
    "BtnShoulderL": e.BTN_TL,
    "BtnShoulderR": e.BTN_TR,
    "BtnMode": e.BTN_MODE,
    # 🔧 ДОБАВЛЕНО: Триггеры как кнопки (для совместимости с тестерами)
    "TriggerL": e.BTN_TL2,
    "TriggerR": e.BTN_TR2,
}

# Маппинг осей (стики и триггеры)
AXIS_MAP = {
    'AxisLx': e.ABS_X,
    'AxisLy': e.ABS_Y,
    'AxisRx': e.ABS_RX,
    'AxisRy': e.ABS_RY,
    'TriggerL': e.ABS_Z,
    'TriggerR': e.ABS_RZ,
    # D-Pad обрабатывается как оси HAT
    'DpadX': e.ABS_HAT0X,
    'DpadY': e.ABS_HAT0Y,
}

# Настройки масштабирования осей (из старого VirtualJoystick)
AXIS_LIMITS = {
    e.ABS_X: (-32768, 32767),
    e.ABS_Y: (-32768, 32767),
    e.ABS_RX: (-32768, 32767),
    e.ABS_RY: (-32768, 32767),
    e.ABS_Z: (0, 255),    # Trigger L
    e.ABS_RZ: (0, 255),   # Trigger R
    e.ABS_HAT0X: (-1, 1), # Dpad
    e.ABS_HAT0Y: (-1, 1), # Dpad
}