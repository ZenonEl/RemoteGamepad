import json
import logging
from contextlib import asynccontextmanager
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
                # Левый стик
                if "left_stick" in axes:
                    gamepad.send_axis('AxisLx', axes["left_stick"]["x"])
                    gamepad.send_axis('AxisLy', axes["left_stick"]["y"]) # Инверсия Y обычно на клиенте или тут
                
                # Правый стик
                if "right_stick" in axes:
                    gamepad.send_axis('AxisRx', axes["right_stick"]["x"])
                    gamepad.send_axis('AxisRy', axes["right_stick"]["y"])

            # 2. Кнопки и Триггеры
            if "buttons" in data:
                for btn in data["buttons"]:
                    name = btn.get("name")
                    value = btn.get("value", 0)
                    pressed = btn.get("pressed", False)

                    # Триггеры (L2/R2) - это оси, а не кнопки
                    if name in ["TriggerL", "TriggerR"]:
                        gamepad.send_axis(name, value)
                    
                    # Крестовина (D-Pad) - часто приходит как кнопки, но в Linux это ось HAT
                    elif name.startswith("Dpad"):
                        # Логику D-pad лучше считать на клиенте или тут собрать состояние
                        # Для KISS пока пропустим сложную логику Dpad, если она не критична,
                        # или добавим позже. В старом коде это работало через button events.
                        # Если Dpad приходит как кнопка (0/1), можно сэмулировать нажатие.
                        # Но в mapping_config у нас DpadX/Y.
                        pass # TODO: Реализовать D-pad логику если потребуется
                        
                    else:
                        # Обычные кнопки (A, B, X, Y, Start, Back...)
                        gamepad.send_button(name, pressed)

    except WebSocketDisconnect:
        logger.info(f"🔌 Client disconnected: {client_ip}")
        # Опционально: удалять геймпад при отключении
        # await gamepad_manager.remove_gamepad() 
        # Но для удобства отладки можно оставлять
    except Exception as e:
        logger.error(f"⚠️ Error in WS loop: {e}")