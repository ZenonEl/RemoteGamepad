import requests
import json, os
import sys
from pathlib import Path

# Добавляем корневую папку в путь для импортов
sys.path.insert(0, str(Path(__file__).parent))

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

        self.DPAD_OFF = 0
        self.DPAD_UP = 1
        self.DPAD_DOWN = 2
        self.DPAD_LEFT = 3
        self.DPAD_RIGHT = 4

    def set_value(self, name, value, is_pressed=None):
        logger.info(f"set_value called: name='{name}', value={value} (type: {type(value)}), is_pressed={is_pressed}")
        
        axis_map = {
            'AxisLx': e.ABS_X,
            'AxisLy': e.ABS_Y,
            'AxisRx': e.ABS_RX,
            'AxisRy': e.ABS_RY,
        }
        
        # Триггеры обрабатываем отдельно
        trigger_map = {
            'TriggerL': e.ABS_Z,
            'TriggerR': e.ABS_RZ
        }
        
        if name in axis_map:
            # Обычные оси (стики)
            scaled_value = int(value * 32767)
            if 'Ly' in name or 'Ry' in name:
                scaled_value = -scaled_value
            self.device.write(e.EV_ABS, axis_map[name], scaled_value)
            self.device.syn()
        elif name in trigger_map:
            # Триггеры - если это булево значение (кнопка), конвертируем в 0-255
            if isinstance(value, bool):
                # value = True -> 255, value = False -> 0
                trigger_value = 255 if value else 0
            else:
                # Если пришло число 0.0-1.0, конвертируем в 0-255
                trigger_value = int(value * 255)
            
            logger.info(f"Trigger {name}: value={value} -> trigger_value={trigger_value}")
            self.device.write(e.EV_ABS, trigger_map[name], trigger_value)
            self.device.syn()
        elif name == "Dpad":
            self._handle_dpad(value, is_pressed)
        else:
            btn_code = BUTTON_MAP.get(name)
            if btn_code is not None:
                # Проверяем что это не триггер
                if btn_code in ["TRIGGER_L", "TRIGGER_R"]:
                    # Это триггер - обрабатываем как ось
                    if btn_code == "TRIGGER_L":
                        trigger_code = e.ABS_Z
                    else:  # TRIGGER_R
                        trigger_code = e.ABS_RZ
                    
                    # Конвертируем булево значение в 0-255
                    if isinstance(value, bool):
                        trigger_value = 255 if value else 0
                    else:
                        trigger_value = int(value * 255)
                    
                    logger.info(f"Processing trigger {name} as axis: value={value} -> {trigger_value}")
                    self.device.write(e.EV_ABS, trigger_code, trigger_value)
                    self.device.syn()
                else:
                    # Обычная кнопка
                    self.device.write(e.EV_KEY, btn_code, 1 if value else 0)
                    self.device.syn()
        self.device.syn()


def process_btn_data(data):
    if "buttons" in data:
        logger.info(f"Received buttons data: {data['buttons']}")
        for btn in data["buttons"]:
            if not btn["name"].startswith("Dpad"):
                logger.info(f"Processing button: {btn['name']} = {btn['pressed']} (type: {type(btn['pressed'])})")
                set_btn_state(btn["name"], btn["pressed"])

        button_dict = {button['name']: button for button in data['buttons']}

        dpad_up_value = button_dict.get('Dpad_Up', {}).get('value', 0)
        dpad_down_value = button_dict.get('Dpad_Down', {}).get('value', 0)
        dpad_left_value = button_dict.get('Dpad_Left', {}).get('value', 0)
        dpad_right_value = button_dict.get('Dpad_Right', {}).get('value', 0)

        dpad_x = dpad_right_value - dpad_left_value
        dpad_y = dpad_up_value - dpad_down_value

        print(f"dpad_x: {dpad_x}, dpad_y: {dpad_y}")

        controller.device.write(e.EV_ABS, e.ABS_HAT0X, dpad_x)
        controller.device.write(e.EV_ABS, e.ABS_HAT0Y, dpad_y * -1)
        controller.device.syn()

def set_btn_state(button_name, is_pressed):
        logger.info(f"set_btn_state: {button_name} = {is_pressed} (type: {type(is_pressed)})")
        if button_name in BUTTON_MAP:
            logger.info(f"Button {button_name} found in BUTTON_MAP, calling set_value")
            controller.set_value(button_name, is_pressed)
        else:
            logger.warning(f"Button {button_name} NOT found in BUTTON_MAP")

# Flask

@app.route("/gamepad_data", methods=["POST"])
def handle_gamepad_data():
    data = request.json
    if not data:
        return jsonify({"status": "error"}), 400

    if data.get("type") == "axis":
        axes = data["axes"]
        controller.set_value('AxisLx', float(axes["left_stick"]["x"]))
        controller.set_value('AxisLy', float(axes["left_stick"]["y"]) * -1)
        controller.set_value('AxisRx', float(axes["right_stick"]["x"]))
        controller.set_value('AxisRy', float(axes["right_stick"]["y"]) * -1)

    process_btn_data(data)
    return jsonify({"status": "success"}), 200

def run_flask():
    app.run(
        host=get_setting("SERVER_IP"),
        port=get_setting("SERVER_PORT"),
        debug=get_setting("DEBUG")
    )

def load_translations(lang):
    lang_dir = os.path.join(app.root_path, 'lang')
    with open(os.path.join(lang_dir, f'{lang}.json'), 'r', encoding='utf-8') as f:
        return json.load(f)

@app.route('/lang/<lang>')
def get_translations(lang):
    if lang not in ['ru', 'en']:
        return jsonify({"error": "Language not supported"}), 404
    
    translations = load_translations(lang)
    return render_template('translations.html', translations=translations)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/ping')
def ping():
    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    controller = VirtualJoystick()
    run_flask()