import json
import logging
from contextlib import asynccontextmanager
from pprint import pprint
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from src.core.gamepad_manager import GamepadManager

# Настраиваем логгер
logger = logging.getLogger("api")

# Глобальный инстанс менеджера (Singleton для KISS)
gamepad_manager = GamepadManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    logger.info("🚀 Server starting...")
    # При старте ничего сложного не делаем, геймпад создадим при подключении клиента
    yield
    # При выключении очищаем ресурсы
    logger.info("🛑 Server shutting down...")
    await gamepad_manager.cleanup()

app = FastAPI(lifespan=lifespan)

# Монтируем статику (CSS, JS)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def get_index():
    """Отдает главную страницу"""
    return FileResponse("templates/index.html")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    Основной цикл обработки данных от телефона.
    """
    await websocket.accept()
    client_ip = websocket.client.host
    logger.info(f"📱 Client connected: {client_ip}")

    # Создаем геймпад для этого клиента
    # В будущем здесь будет client_id, пока используем "default"
    if await gamepad_manager.create_gamepad("default"):
        logger.info("🎮 Virtual Gamepad ready for input")
    else:
        logger.error("❌ Failed to create gamepad")
        await websocket.close()
        return

    gamepad = await gamepad_manager.get_active_gamepad()
    
    try:
        while True:
            # Получаем сырые данные (JSON)
            data_text = await websocket.receive_text()
            data = json.loads(data_text)

            # --- Обработка данных (Парсинг) ---
            # 1. Оси (Стики)
            if "axes" in data:
                axes = data["axes"]
                
                # Стики
                if "left_stick" in axes:
                    gamepad.send_axis('AxisLx', axes["left_stick"]["x"])
                    gamepad.send_axis('AxisLy', axes["left_stick"]["y"])
                if "right_stick" in axes:
                    gamepad.send_axis('AxisRx', axes["right_stick"]["x"])
                    gamepad.send_axis('AxisRy', axes["right_stick"]["y"])

            # 2. Обработка кнопок, Триггеров и D-Pad
            if "buttons" in data:
                dpad_state = {"up": False, "down": False, "left": False, "right": False}
                
                for btn in data["buttons"]:
                    name = btn.get("name", "Unknown")
                    value = btn.get("value", 0)
                    pressed = btn.get("pressed", False)
                    # ВОТ ОНО: Триггеры обрабатываются как оси ВНУТРИ списка кнопок
                    if name in["TriggerL", "TriggerR"]:
                        # Отправляем value, чтобы сработала старая конвертация (int(value * 255))
                        print(name, value)
                        gamepad.process_trigger_as_button(name, value)
                        continue
                    
                    # D-Pad -> Собираем состояние
                    if name == "Dpad_Up": dpad_state["up"] = pressed
                    elif name == "Dpad_Down": dpad_state["down"] = pressed
                    elif name == "Dpad_Left": dpad_state["left"] = pressed
                    elif name == "Dpad_Right": dpad_state["right"] = pressed
                        
                    # Обычные кнопки (A, B, Start, Mode и т.д.)
                    else:
                        gamepad.send_button(name, pressed)
                
                # 3. Вычисляем и отправляем D-Pad (HAT)
                # X: -1 (Left), 1 (Right), 0 (None)
                hat_x = -1 if dpad_state["left"] else (1 if dpad_state["right"] else 0)
                # Y: -1 (Up), 1 (Down), 0 (None) - В Linux Y инвертирован относительно экрана (обычно -1 это вверх)
                hat_y = -1 if dpad_state["up"] else (1 if dpad_state["down"] else 0)
                
                gamepad.send_dpad(hat_x, hat_y)

    except WebSocketDisconnect:
        logger.info(f"🔌 Client disconnected: {client_ip}")
        # Опционально: удалять геймпад при отключении
        # await gamepad_manager.remove_gamepad() 
        # Но для удобства отладки можно оставлять
    except Exception as e:
        logger.error(f"⚠️ Error in WS loop: {e}")