from dataclasses import dataclass


# * SERVER DATA
SERVER_IP = "192.168.0.106"
SERVER_PORT = 8081

INTERVAL_SEND_TIMING = 50

# Сопоставление номеров кнопок с именами кнопок
BUTTON_MAP = {
    0: "BtnA",
    1: "BtnB",
    2: "BtnX",
    3: "BtnY",
    4: "BtnBack",
    5: "BtnStart",
    6: "BtnThumbL",
    7: "BtnThumbR",
    8: "BtnShoulderL",
    9: "BtnShoulderR",
    15: "TriggerL",
    16: "TriggerR",
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
