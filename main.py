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
    4: 'BtnBack',        # Select Button
    5: 'BtnStart',       # Start Button
    6: 'BtnStart',       # Start Button (mapped to 6)
    7: 'BtnThumbL',      # Left Thumbstick Click
    8: 'BtnThumbR',      # Right Thumbstick Click
    9: 'BtnShoulderL',   # Left Shoulder Button
    10: 'BtnShoulderR',  # Right Shoulder Button
    11: 'Dpad_Up',       # Dpad Up
    12: 'Dpad_Down',    # Dpad Right
    13: 'Dpad_Left',     # Dpad Down
    14: 'Dpad_Right',     # Dpad Left
    15: 'TriggerL',      # Left Trigger
    16: 'TriggerR'       # Right Trigger
}

# Инициализация переменных для хранения предыдущих значений осей
prev_axes = {
    'left_stick': {'x': 0, 'y': 0},
    'right_stick': {'x': 0, 'y': 0}
}

# Создаем сокет
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
    server_socket.bind((HOST, PORT))
    server_socket.listen()
    print(f"Сервер запущен на {HOST}:{PORT}. Ожидание подключения...")

    conn, addr = server_socket.accept()
    with conn:
        print('Подключено к', addr)
        buffer = ""  # Буфер для хранения частично полученных данных
        while True:
            try:
                data = conn.recv(1024)
                if not data:
                    break

                buffer += data.decode()  # Добавляем новые данные в буфер

                # Разбираем данные из буфера по символам разделителя JSON (в данном случае '}')
                while '}' in buffer:
                    try:
                        controller.set_value('Dpad', 0)

                        # Находим первое завершенное сообщение
                        json_message, buffer = buffer.split('}', 1)
                        json_message += '}'  # Восстанавливаем потерянную закрывающую фигурную скобку
                        json_message = json_message + buffer
                        # Декодируем JSON
                        parsed_data = json.loads(json_message)
                        print('Получено от клиента:', parsed_data)

                        # Обработка данных осей
                        if parsed_data.get("type") == "axis":
                            axes = parsed_data["axes"]
                            
                            # Извлечение значений осей
                            l_stick_x = int(axes["left_stick"]["x"] * 32767)
                            l_stick_y = int(axes["left_stick"]["y"] * 32767)
                            r_stick_x = int(axes["right_stick"]["x"] * 32767)
                            r_stick_y = int(axes["right_stick"]["y"] * 32767)

                            # Установка значений для осей, если они изменились
                            if (l_stick_x != prev_axes['left_stick']['x']) or (l_stick_y != prev_axes['left_stick']['y']):
                                controller.set_value('AxisLx', l_stick_x)
                                controller.set_value('AxisLy', l_stick_y)
                                print('AxisLx:', l_stick_x, 'AxisLy:', l_stick_y)
                                if l_stick_x == 127 or l_stick_y == 127:
                                    controller.set_value('AxisLx', int(0))
                                    controller.set_value('AxisLy', int(0))

                            if (r_stick_x != prev_axes['right_stick']['x']) or (r_stick_y != prev_axes['right_stick']['y']):
                                controller.set_value('AxisRx', r_stick_x)
                                controller.set_value('AxisRy', r_stick_y)
                                print('AxisRx:', r_stick_x, 'AxisRy:', r_stick_y)
                                if r_stick_x == 127 or r_stick_y == 127:
                                    controller.set_value('AxisRx', int(0))
                                    controller.set_value('AxisRy', int(0))

                            # Обновляем предыдущие значения
                            prev_axes = {
                                'left_stick': {'x': l_stick_x, 'y': l_stick_y},
                                'right_stick': {'x': r_stick_x, 'y': r_stick_y}
                            }
                        else:
                            controller.set_value('AxisLx', int(0))
                            controller.set_value('AxisLy', int(0))
                            controller.set_value('AxisRx', int(0))
                            controller.set_value('AxisRy', int(0))

                        # Обработка кнопок
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
                                            14: 8,  # Right
                                            12: 2,  # Down
                                            13: 4   # Left
                                        }.get(button_number, 0)  # Значение по умолчанию - Off
                                        controller.set_value('Dpad', dpad_value)

                                else:
                                    if parsed_data["action"] == "down":
                                        controller.set_value('Dpad', 0)
                                        controller.set_value(button, 1)  # Нажатие кнопки
                                    elif parsed_data["action"] == "up":
                                        controller.set_value('Dpad', 0)
                                        controller.set_value(button, 0)  # Отпускание кнопки

                    except json.JSONDecodeError:
                        print("Ошибка декодирования JSON:", json_message)

            except Exception as e:
                print(f"Ошибка: {e}")
                break
