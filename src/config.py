import os

# Простейшая загрузка .env без лишних библиотек (KISS)
env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
if os.path.exists(env_path):
    with open(env_path, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                key, val = line.split("=", 1)
                os.environ[key.strip()] = val.strip()

# Глобальные настройки
PORT = int(os.getenv("PORT", 5002))
EXTERNAL_URL = os.getenv("EXTERNAL_URL", "")