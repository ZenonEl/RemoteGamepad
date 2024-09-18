import os
import yaml
from config.default_settings import USER_SETTINGS_FILE, DEFAULT_SETTINGS_DICT


def get_setting(key):
    """Получает значение настройки. Если настройки нет, возвращает дефолтное значение из DEFAULT_SETTINGS."""
    user_settings = load_user_settings()
    return user_settings.get(key, DEFAULT_SETTINGS_DICT.get(key))


def set_setting(key, value):
    """Записывает значение настройки в пользовательский YAML-файл."""
    user_settings = load_user_settings()
    user_settings[key] = value
    with open(USER_SETTINGS_FILE, "w") as file:
        yaml.dump(user_settings, file)


def load_user_settings():
    """Загружает пользовательские настройки из YAML-файла. Если файл не существует, создаёт новый."""
    if not os.path.exists(USER_SETTINGS_FILE):
        # Создание нового пустого файла, если его нет
        with open(USER_SETTINGS_FILE, "w") as file:
            yaml.dump({}, file)
        return {}

    with open(USER_SETTINGS_FILE, "r") as file:
        return yaml.safe_load(file) or {}
