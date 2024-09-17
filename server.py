import flet as ft
import pyxinput
import requests
from flask import Flask, jsonify, render_template, request
from loguru import logger

from config.default_settings import BUTTON_MAP
from config.settings import get_setting

app = Flask(__name__)

controller = pyxinput.vController()


@app.route("/gamepad_data", methods=["POST"])
def handle_gamepad_data():
    data = request.json
    if not data:
        logger.error("Нет данных в запросе")
        return jsonify({"status": "error", "message": "No data received"}), 400

    logger.info(f"Получены данные: {data}")

    if data.get("type") == "axis":
        axes = data["axes"]

        l_stick_x = float(axes["left_stick"]["x"])
        l_stick_y = float(axes["left_stick"]["y"] * -1)
        r_stick_x = float(axes["right_stick"]["x"])
        r_stick_y = float(axes["right_stick"]["y"] * -1)

        controller.set_value("AxisLx", l_stick_x)
        controller.set_value("AxisLy", l_stick_y)
        controller.set_value("AxisRx", r_stick_x)
        controller.set_value("AxisRy", r_stick_y)

    process_btn_data(data)

    return jsonify({"status": "success"}), 200


# Flask маршруты
@app.route('/')
def index():
    return render_template('index.html')

def run_flask():
    app.run(host=get_setting("SERVER_IP"), port=get_setting("SERVER_PORT"))


def check_server_status(page: ft.Page):
    server_ip = get_setting("SERVER_IP")
    server_port = get_setting("SERVER_PORT")
    url = f"http://{server_ip}:{server_port}"
    container = ft.Container(
        content=ft.Column(
            [
                ft.Text(
                    "Проверка статуса сервера...",
                    style=ft.TextThemeStyle.HEADLINE_SMALL,
                ),
                ft.Column(
                    [ft.ProgressRing()],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        width=page.width,  # Ширина контейнера равна ширине окна
        height=page.height,  # Высота контейнера равна высоте окна
    )

    page.add(container)
    page.update()
    try:
        response = requests.get(url, timeout=1)  # Тайм-аут 2 секунды
        if response.status_code == 200:
            page.remove(container)
            return True
    except requests.RequestException:
        page.remove(container)
        return False

    page.remove(container)
    return True if response.status_code == 200 else False


def process_btn_data(data):
    if "buttons" in data:
        buttons = data["buttons"]
        for button_data in buttons:
            button_name = button_data["name"]
            is_pressed = button_data["pressed"]
            set_btn_state(button_name, is_pressed)


def set_btn_state(button_name, is_pressed):
    if button_name:
        if button_name.startswith("Dpad") and is_pressed:
            set_dpad(button_name, is_pressed)

        else:
            try:
                if button_name in BUTTON_MAP.values():
                    controller.set_value("Dpad", controller.DPAD_OFF)
                    controller.set_value(button_name, 1 if is_pressed else 0)
            except Exception as e:
                logger.error(
                    f"Не удалось установить состояние кнопки {button_name}: {e}"
                )


def set_dpad(button_name, is_pressed):
    dpad_map = {
        "Dpad_Up": controller.DPAD_UP,
        "Dpad_Down": controller.DPAD_DOWN,
        "Dpad_Left": controller.DPAD_LEFT,
        "Dpad_Right": controller.DPAD_RIGHT,
    }

    dpad_value = dpad_map.get(button_name, controller.DPAD_OFF)
    controller.set_value("Dpad", dpad_value if is_pressed else 0)
