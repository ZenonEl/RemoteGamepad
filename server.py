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

        self.dpad_state = {
            'x': 0,
            'y': 0
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

    # def _handle_dpad(self, value, is_pressed):
    #     # Определяем изменение по осям X и Y
    #     x_changed = False
    #     y_changed = False
    #     print(y_changed, x_changed)
    #     if value in [self.DPAD_LEFT, self.DPAD_RIGHT]:
    #         if is_pressed:
    #             self.dpad_state['x'] = 222 if value == self.DPAD_LEFT else 1
    #             x_changed = True
    #         else:
    #             if self.dpad_state['x'] != 0 and not is_pressed:
    #                 self.dpad_state['x'] = 0
    #                 x_changed = True
    #     elif value in [self.DPAD_UP, self.DPAD_DOWN]:
    #         if is_pressed:
    #             self.dpad_state['y'] = 1 if value == self.DPAD_UP else 1
    #             y_changed = True
    #         else:
    #             if self.dpad_state['y'] != 0 and not is_pressed:
    #                 self.dpad_state['y'] = 0
    #                 y_changed = True

    #     # Отправляем обновления только если состояние изменилось
    #     if x_changed:
    #         self.device.write(e.EV_ABS, e.ABS_HAT0X, self.dpad_state['x'])
    #     if y_changed:
    #         self.device.write(e.EV_ABS, e.ABS_HAT0Y, self.dpad_state['y'])

    #     # Синхронизация изменений
    #     self.device.syn()


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
        # Сначала обрабатываем все кнопки, затем обновляем D-pad
        for btn in data["buttons"]:
            if not btn["name"].startswith("Dpad"):
                set_btn_state(btn["name"], btn["pressed"])

        button_dict = {button['name']: button for button in data['buttons']}

        # Извлекаем значения D-pad
        dpad_up_value = button_dict.get('Dpad_Up', {}).get('value', 0)
        dpad_down_value = button_dict.get('Dpad_Down', {}).get('value', 0)
        dpad_left_value = button_dict.get('Dpad_Left', {}).get('value', 0)
        dpad_right_value = button_dict.get('Dpad_Right', {}).get('value', 0)

        # Вычисляем dpad_x и dpad_y
        dpad_x = dpad_right_value - dpad_left_value
        dpad_y = dpad_up_value - dpad_down_value

        # Выводим результаты
        print(f"dpad_x: {dpad_x}, dpad_y: {dpad_y}")

        # После обработки всех кнопок, синхронизируем D-pad
        controller.device.write(e.EV_ABS, e.ABS_HAT0X, dpad_x)
        controller.device.write(e.EV_ABS, e.ABS_HAT0Y, dpad_y * -1)
        controller.device.syn()

def set_btn_state(button_name, is_pressed):
    # if button_name.startswith("Dpad"):
    #     dpad_mapping = {
    #         "Dpad_Up": (0, -1),
    #         "Dpad_Down": (0, 1),
    #         "Dpad_Left": (-1, 0),
    #         "Dpad_Right": (1, 0)
    #     }
    #     x, y = dpad_mapping.get(button_name, (0, 0))
    #     # Обновляем только соответствующую ось
    #     if x != 0:
    #         controller.dpad_state['x'] = x if is_pressed else 0
    #     if y != 0:
    #         controller.dpad_state['y'] = y if is_pressed else 0
        
    #     # Важно: не вызываем device.syn() здесь, чтобы избежать частичных обновлений
    # else:
    #     # Обработка других кнопок
        if button_name in BUTTON_MAP:
            controller.set_value(button_name, is_pressed)

if __name__ == "__main__":
    run_flask()