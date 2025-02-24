import flet as ft
import requests
from evdev import UInput, AbsInfo, ecodes as e
from flask import Flask, jsonify, render_template, request
from loguru import logger

from config.default_settings import BUTTON_MAP
from config.settings import get_setting

app = Flask(__name__)

class VirtualJoystick:
    def __init__(self):
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
                (e.ABS_X, AbsInfo(0, -32768, 32767, 0, 0, 0)),
                (e.ABS_Y, AbsInfo(0, -32768, 32767, 0, 0, 0)),
                (e.ABS_RX, AbsInfo(0, -32768, 32767, 0, 0, 0)),
                (e.ABS_RY, AbsInfo(0, -32768, 32767, 0, 0, 0)),
                (e.ABS_Z, AbsInfo(0, 0, 255, 0, 0, 0)),    # LT
                (e.ABS_RZ, AbsInfo(0, 0, 255, 0, 0, 0)),   # RT
                (e.ABS_HAT0X, AbsInfo(0, -1, 1, 0, 0, 0)),
                (e.ABS_HAT0Y, AbsInfo(0, -1, 1, 0, 0, 0)),
            ]
        }
        
        self.device = UInput(
            self.caps,
            name='Microsoft X-Box 360 pad',
            vendor=0x045e,
            product=0x028e,
            version=0x0110,
            bustype=e.BUS_USB
        )

        # Константы для D-Pad
        self.DPAD_OFF = 0
        self.DPAD_UP = 1
        self.DPAD_DOWN = 2
        self.DPAD_LEFT = 3
        self.DPAD_RIGHT = 4

    def set_value(self, name, value, is_pressed=None):
        axis_map = {
            'AxisLx': e.ABS_X,
            'AxisLy': e.ABS_Y,
            'AxisRx': e.ABS_RX,
            'AxisRy': e.ABS_RY,
            'TriggerL': e.ABS_Z,
            'TriggerR': e.ABS_RZ
        }
        
        if name in axis_map:
            # Инверсия осей Y
            scaled_value = int(value * 32767)
            if 'Ly' in name or 'Ry' in name:
                scaled_value = -scaled_value
            self.device.write(e.EV_ABS, axis_map[name], scaled_value)
            self.device.syn()
        elif name == "Dpad":
            self._handle_dpad(value, is_pressed)
        else:
            btn_code = BUTTON_MAP.get(name)
            if btn_code is not None:
                self.device.write(e.EV_KEY, btn_code, 1 if value else 0)
                self.device.syn()

    def _handle_dpad(self, value, is_pressed):
        print(f"Value: {value}, Is pressed: {is_pressed}")  # Отладочный вывод
        import time
        if is_pressed:
            if value == self.DPAD_LEFT:
                print("D-pad left pressed")  # Отладка
                self.device.write(e.EV_ABS, e.ABS_HAT0X, -1)
                time.sleep(0.3)
            elif value == self.DPAD_RIGHT:
                print("D-pad right pressed")  # Отладка
                self.device.write(e.EV_ABS, e.ABS_HAT0X, 1)
            elif value == self.DPAD_UP:
                print("D-pad up pressed")  # Отладка
                self.device.write(e.EV_ABS, e.ABS_HAT0Y, -1)
                time.sleep(0.3)
            elif value == self.DPAD_DOWN:
                print("D-pad down pressed")  # Отладка
                self.device.write(e.EV_ABS, e.ABS_HAT0Y, 1)
        else:
            if value == self.DPAD_LEFT or value == self.DPAD_RIGHT:
                print("D-pad X-axis released")  # Отладка
                self.device.write(e.EV_ABS, e.ABS_HAT0X, 0)
            elif value == self.DPAD_UP or value == self.DPAD_DOWN:
                print("D-pad Y-axis released")  # Отладка
                self.device.write(e.EV_ABS, e.ABS_HAT0Y, 0)
        self.device.syn()


# Инициализация контроллера

controller = VirtualJoystick()

@app.route("/gamepad_data", methods=["POST"])
def handle_gamepad_data():
    data = request.json
    if not data:
        return jsonify({"status": "error"}), 400

    # Обработка осей (без инверсии)
    if data.get("type") == "axis":
        axes = data["axes"]
        controller.set_value('AxisLx', float(axes["left_stick"]["x"]))
        controller.set_value('AxisLy', float(axes["left_stick"]["y"]) * -1)
        controller.set_value('AxisRx', float(axes["right_stick"]["x"]))
        controller.set_value('AxisRy', float(axes["right_stick"]["y"]) * -1)

    process_btn_data(data)
    return jsonify({"status": "success"}), 200

@app.route('/')
def index():
    return render_template('index.html')

def run_flask():
    app.run(
        host=get_setting("SERVER_IP"),
        port=get_setting("SERVER_PORT"),
        debug=get_setting("DEBUG")
    )

def check_server_status(page: ft.Page):
    server_ip = get_setting("SERVER_IP")
    server_port = get_setting("SERVER_PORT")
    url = f"http://{server_ip}:{server_port}"
    
    container = ft.Container(
        content=ft.Column([
            ft.Text("Проверка статуса сервера...", style=ft.TextThemeStyle.HEADLINE_SMALL),
            ft.ProgressRing()
        ], alignment=ft.MainAxisAlignment.CENTER),
        width=page.width,
        height=page.height,
    )
    
    page.add(container)
    page.update()
    
    try:
        response = requests.get(url, timeout=2)
        status = response.status_code == 200
    except requests.RequestException:
        status = False
    
    page.remove(container)
    return status

def process_btn_data(data):
    if "buttons" in data:
        for btn in data["buttons"]:
            set_btn_state(btn["name"], btn["pressed"])

def set_btn_state(button_name, is_pressed):
    if not button_name:
        return
    if button_name.startswith("Dpad"):
        # Обработка D-Pad
        dpad_mapping = {
        "Dpad_Up": controller.DPAD_UP,      # 1
        "Dpad_Down": controller.DPAD_DOWN,  # 2
        "Dpad_Left": controller.DPAD_LEFT,  # 3
        "Dpad_Right": controller.DPAD_RIGHT # 4
    }

        # Используем DPAD_OFF (0) если кнопка отпущена
        dpad_value = dpad_mapping.get(button_name, controller.DPAD_OFF)
        controller.set_value("Dpad", dpad_value, is_pressed)
    else:
        # Используем прямое сопоставление из BUTTON_MAP
        if button_name in BUTTON_MAP:
            controller.set_value(button_name, is_pressed)

if __name__ == "__main__":
    run_flask()