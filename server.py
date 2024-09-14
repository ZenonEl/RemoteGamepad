from loguru import logger
import pyxinput
import socket
import json

# Инициализация виртуального контроллера Xbox 360
controller = pyxinput.vController()

# Конфигурация сокета
HOST = '192.168.0.106'  # IP вашего ПК
PORT = 8081             # Порт для подключения

# Сопоставление номеров кнопок с именами кнопок
button_map = {
    0: 'BtnA',
    1: 'BtnB',
    2: 'BtnX',
    3: 'BtnY',
    4: 'BtnBack',
    5: 'BtnStart',
    6: 'BtnStart',
    7: 'BtnThumbL',
    8: 'BtnThumbR',
    9: 'BtnShoulderL',
    10: 'BtnShoulderR',
    11: 'Dpad_Up',
    12: 'Dpad_Down',
    13: 'Dpad_Left',
    14: 'Dpad_Right',
    15: 'TriggerL',
    16: 'TriggerR'
}

prev_axes = {
    'left_stick': {'x': 0, 'y': 0},
    'right_stick': {'x': 0, 'y': 0}
}

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
    server_socket.bind((HOST, PORT))
    server_socket.listen()
    logger.info(f"Сервер запущен на {HOST}:{PORT}. Ожидание подключения...")

    conn, addr = server_socket.accept()
    with conn:
        logger.info(f'Подключено к: {addr[0]}:{addr[1]}')

        buffer = ""  # Буфер для хранения частично полученных данных
        while True:
            try:
                data = conn.recv(1024)
                if not data:
                    break

                buffer += data.decode()

                # Разбираем данные из буфера по символам разделителя JSON (в данном случае '}')
                while '}' in buffer:
                    try:

                        json_message, buffer = buffer.split('}', 1)
                        json_message += '}'
                        json_message = json_message + buffer
                        parsed_data = json.loads(json_message)

                        if parsed_data.get("type") == "axis":
                            axes = parsed_data["axes"]

                            l_stick_x = float(axes["left_stick"]["x"])
                            l_stick_y = float(axes["left_stick"]["y"] * -1)
                            r_stick_x = float(axes["right_stick"]["x"])
                            r_stick_y = float(axes["right_stick"]["y"] * -1)

                            if (l_stick_x != prev_axes['left_stick']['x']) or (l_stick_y != prev_axes['left_stick']['y']):
                                controller.set_value('AxisLx', l_stick_x)
                                controller.set_value('AxisLy', l_stick_y)

                            if (r_stick_x != prev_axes['right_stick']['x']) or (r_stick_y != prev_axes['right_stick']['y']):
                                controller.set_value('AxisRx', r_stick_x)
                                controller.set_value('AxisRy', r_stick_y)

                            prev_axes = {
                                'left_stick': {'x': l_stick_x, 'y': l_stick_y},
                                'right_stick': {'x': r_stick_x, 'y': r_stick_y}
                            }

                        try:
                            if parsed_data.get("type") == "button":
                                button_number = parsed_data['button']

                                if button_number in button_map:
                                    button = button_map[button_number]
                                    if button.startswith('Dpad'):
                                        controller.set_value('Dpad', 0)
                                        if parsed_data["action"] == "up":
                                            controller.set_value('Dpad', 0)

                                        elif parsed_data["action"] == "down":
                                            dpad_value = {
                                                11: 1,  # Up
                                                12: 2,  # Down
                                                13: 4,  # Left
                                                14: 8,  # Right
                                            }.get(button_number, 0)  # Значение по умолчанию - Off
                                            controller.set_value('Dpad', dpad_value)

                                    else:
                                        if parsed_data["action"] == "down":
                                            controller.set_value('Dpad', 0)
                                            controller.set_value(button, 1)  # Нажатие кнопки
                                        elif parsed_data["action"] == "up":
                                            controller.set_value('Dpad', 0)
                                            controller.set_value(button, 0)  # Отпускание кнопки

                        except Exception as e:
                            logger.error(f"Ошибка: {e}")
                    except json.JSONDecodeError:
                        pass

            except Exception as e:
                logger.error(f"Ошибка: {e}")
    logger.warning("Connection closed")
