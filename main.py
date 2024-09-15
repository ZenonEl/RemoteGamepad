import flet as ft
from flask import Flask, render_template_string, request, jsonify
from loguru import logger
import pyxinput
import threading
import time

import requests

# Конфигурация сервера
SERVER_IP = '192.168.0.106'
SERVER_PORT = 8081
INTERVAL_SEND_TIMING = 50

# Сопоставление номеров кнопок с именами кнопок
BUTTON_MAP = {
    0: 'BtnA',
    1: 'BtnB',
    2: 'BtnX',
    3: 'BtnY',
    8: 'BtnBack',
    9: 'BtnStart',
    10: 'BtnThumbL',
    11: 'BtnThumbR',
    4: 'BtnShoulderL',
    5: 'BtnShoulderR',
    12: 'Dpad_Up',
    13: 'Dpad_Down',
    14: 'Dpad_Left',
    15: 'Dpad_Right',
    6: 'TriggerL',
    7: 'TriggerR'
}

# Инициализация контроллера
controller = pyxinput.vController()
app = Flask(__name__)

# Флаг для отслеживания состояния сервера
server_running = False


# Flask маршруты
@app.route('/')
def index():
    return render_template_string('''
<!DOCTYPE html>
<html>
<head>
    <title>Joystick Data</title>
    <style>
        body { font-family: Arial, sans-serif; }
        #output { margin-top: 20px; }
    </style>
</head>
<body>
    <h1>Joystick Data</h1>
    <div id="output"></div>
    <script>
        const intervalTime = {{interval_time}};
        // Сопоставление индексов кнопок с их именами
        const buttonMap = {
            0: 'BtnA',
            1: 'BtnB',
            2: 'BtnX',
            3: 'BtnY',
            8: 'BtnBack',
            9: 'BtnStart',
            10: 'BtnThumbL',
            11: 'BtnThumbR',
            4: 'BtnShoulderL',
            5: 'BtnShoulderR',
            12: 'Dpad_Up',
            13: 'Dpad_Down',
            14: 'Dpad_Left',
            15: 'Dpad_Right',
            6: 'TriggerL',
            7: 'TriggerR'
        };
        function getGamepadData() {
            const gamepads = navigator.getGamepads();
            if (gamepads[0]) {
                const axes = {
                    left_stick: {
                        x: gamepads[0].axes[0],
                        y: gamepads[0].axes[1]
                    },
                    right_stick: {
                        x: gamepads[0].axes[2],
                        y: gamepads[0].axes[3]
                    }
                };
                const buttons = gamepads[0].buttons.map((button, index) => ({
                    name: buttonMap[index] || `Button${index}`,
                    pressed: button.pressed,
                    value: button.value,
                    index: index
                }));
                return { type: "axis", axes: axes, buttons: buttons };
            }
            return null;
        }

        function sendGamepadData() {
            const data = getGamepadData();
            if (data) {
                fetch('/gamepad_data', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(data)
                }).then(response => {
                    return response.json();
                }).then(result => {
                    console.log('Response from server:', result);
                }).catch(error => {
                    console.error('Error:', error);
                });
            }
        }

        setInterval(sendGamepadData, intervalTime);
    </script>
</body>
</html>
    ''', interval_time=INTERVAL_SEND_TIMING)

@app.route('/gamepad_data', methods=['POST'])
def handle_gamepad_data():
    data = request.json
    if not data:
        logger.error("Нет данных в запросе")
        return jsonify({'status': 'error', 'message': 'No data received'}), 400

    logger.info(f"Получены данные: {data}")

    if data.get("type") == "axis":
        axes = data["axes"]

        l_stick_x = float(axes["left_stick"]["x"])
        l_stick_y = float(axes["left_stick"]["y"] * -1)
        r_stick_x = float(axes["right_stick"]["x"])
        r_stick_y = float(axes["right_stick"]["y"] * -1)

        controller.set_value('AxisLx', l_stick_x)
        controller.set_value('AxisLy', l_stick_y)
        controller.set_value('AxisRx', r_stick_x)
        controller.set_value('AxisRy', r_stick_y)

    if "buttons" in data:
        buttons = data["buttons"]
        for button_data in buttons:
            button_name = button_data["name"]
            is_pressed = button_data["pressed"]

            if button_name:
                if button_name.startswith('Dpad') and is_pressed:
                    dpad_map = {
                        'Dpad_Up': controller.DPAD_UP,
                        'Dpad_Down': controller.DPAD_DOWN,
                        'Dpad_Left': controller.DPAD_LEFT,
                        'Dpad_Right': controller.DPAD_RIGHT
                    }

                    dpad_value = dpad_map.get(button_name, controller.DPAD_OFF)
                    controller.set_value('Dpad', dpad_value if is_pressed else 0)

                else:
                    try:
                        if button_name in BUTTON_MAP.values():
                            controller.set_value('Dpad', controller.DPAD_OFF)
                            controller.set_value(button_name, 1 if is_pressed else 0)
                    except Exception as e:
                        logger.error(f"Не удалось установить состояние кнопки {button_name}: {e}")

    return jsonify({'status': 'success'}), 200

# Функция для запуска Flask-сервера
def run_flask():
    global server_running
    server_running = True
    app.run(host=SERVER_IP, port=SERVER_PORT)
    server_running = False


# GUI с помощью Flet
def main(page: ft.Page):
    page.title = "Joystick Controller"
    
    server_status = ft.Text(value="Статус сервера: Ожидание...", size=20)

    def update_status():
        if check_server_status():
            server_status.value = "Статус сервера: Работает"
            server_status.color = "green"
            toggle_button.text = "Проверить статус"
        else:
            server_status.value = "Статус сервера: Не работает"
            server_status.color = "red"
            toggle_button.text = "Запустить"
        page.update()

    def toggle_server(e):
        if server_running:
            # Если сервер работает, проверяем статус
            update_status()
        else:
            # Запуск сервера
            threading.Thread(target=run_flask, daemon=True).start()
            time.sleep(1)  # Небольшая задержка для запуска сервера
            update_status()

    def check_server_status():
        url = f"http://{SERVER_IP}:{SERVER_PORT}/"
        for _ in range(3):  # Попытки 3 раза
            try:
                response = requests.get(url, timeout=2)  # Тайм-аут 2 секунды
                if response.status_code == 200:
                    return True
            except requests.RequestException:
                time.sleep(1)  # Задержка перед следующей попыткой
        return False

    toggle_button = ft.ElevatedButton(text="Запустить", on_click=toggle_server)

    # Инициализация статуса при запуске
    update_status()

    nav_menu = ft.Column(
        controls=[
            toggle_button,
            ft.ElevatedButton(text="Настройки", on_click=lambda e: page.go("/settings")),
            ft.ElevatedButton(text="Статистика", on_click=lambda e: page.go("/statistics")),
        ],
        alignment=ft.MainAxisAlignment.START,
        spacing=10
    )

    main_content = ft.Column(
        controls=[
            server_status,
            ft.Divider(),
            nav_menu
        ],
        alignment=ft.MainAxisAlignment.START,
        spacing=20
    )

    page.add(main_content)


# Запуск приложения
if __name__ == '__main__':
    # Запуск GUI
    ft.app(target=main)
