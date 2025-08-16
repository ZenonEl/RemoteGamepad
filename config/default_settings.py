from dataclasses import dataclass


# * SERVER DATA
SERVER_IP = "0.0.0.0"
SERVER_PORT = 5002

INTERVAL_SEND_TIMING = 50

# Сопоставление номеров кнопок с именами кнопок
from evdev import ecodes as e

BUTTON_MAP = {
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
    # Триггеры НЕ здесь - они обрабатываются как оси в gamepad_manager
}

# * OVERALL
LANGUAGE = "ru"

USER_SETTINGS_FILE = "config/user_settings.yaml"

DEFAULT_SETTINGS_DICT = {
    "SERVER_IP": SERVER_IP,
    "SERVER_PORT": SERVER_PORT,
    "INTERVAL_SEND_TIMING": INTERVAL_SEND_TIMING,
    "BUTTON_MAP": BUTTON_MAP,
    "LANGUAGE": LANGUAGE,
}


@dataclass
class DynamicTempSettings:
    SERVER_RUNNING: bool = False
