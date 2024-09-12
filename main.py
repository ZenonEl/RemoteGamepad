import socket
import json
from pyvjoy import VJoyDevice
from pyvjoystick import vjoy

# Конфигурация сокета
HOST = '192.168.0.106'  # IP-адрес вашего ПК
PORT = 8081              # Порт для подключения

# Инициализация виртуального джойстика
vjoy_device_id = 1  # Используйте номер устройства, который вам нужен
vjoy_device = VJoyDevice(vjoy_device_id)

# Создаем сокет
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
    server_socket.bind((HOST, PORT))
    server_socket.listen()
    print(f"Сервер запущен на {HOST}:{PORT}. Ожидание подключения...")

    conn, addr = server_socket.accept()
    with conn:
        print('Подключено к', addr)
        while True:
            vjoy_device.reset()

            try:
                data = conn.recv(1024)
                if not data:
                    # vjoy_device.reset()
                    break

                # Обработка данных
                message = data.decode()

                print('Получено от клиента:', message, end='\n\n')

                # vjoy_device.reset()
                # Парсинг JSON
                try:
                    # Обработка нескольких JSON-объектов, если они приходят в одном сообщении
                    messages = message.split('}{')
                    for i in range(len(messages)):
                        if i > 0:
                            messages[i] = '{' + messages[i]
                        if i < len(messages) - 1:
                            messages[i] = messages[i] + '}'

                        parsed_data = json.loads(messages[i])
                        if parsed_data["type"] == "button":
                            button_number = parsed_data["button"]  # Используем 0-индексацию
                            if parsed_data["action"] == "down":
                                vjoy_device.set_button(button_number + 1, 1)  # Устанавливаем кнопку нажатой
                            elif parsed_data["action"] == "up":
                                vjoy_device.set_button(button_number + 1, 0)  # Устанавливаем кнопку отпущенной
                        elif parsed_data["type"] == "axis":
                            # Обработка осей
                            axes = parsed_data["axes"]
                            try:
                                # Устанавливаем оси с использованием vjoy.HID_USAGE
                                vjoy_device.set_axis(vjoy.HID_USAGE.X, int((axes["left_stick"]["x"] + 1) * 32767.5))  # X
                                vjoy_device.set_axis(vjoy.HID_USAGE.Y, int((axes["left_stick"]["y"] + 1) * 32767.5))  # Y
                                vjoy_device.set_axis(vjoy.HID_USAGE.Z, int((axes["right_stick"]["x"] + 1) * 32767.5))  # RX
                                vjoy_device.set_axis(vjoy.HID_USAGE.RZ, int((axes["right_stick"]["y"] + 1) * 32767.5))  # RY
                                x_value = int((axes["left_stick"]["x"] + 1) * 32767.5)
                                y_value = int((axes["left_stick"]["y"] + 1) * 32767.5)
                                rx_value = int((axes["right_stick"]["x"] + 1) * 32767.5)
                                ry_value = int((axes["right_stick"]["y"] + 1) * 32767.5)
                                print(f"Установлены оси: X = {x_value}, Y = {y_value}, RX = {rx_value}, RY = {ry_value}")
                                # vjoy_device.update()  # Обновляем состояние
                            except Exception as e:
                                print(f"Ошибка при установке осей: {e}")
                except json.JSONDecodeError:
                    print("Ошибка декодирования JSON:", message)
            except Exception as e:
                print(f"Ошибка: {e}")
                break

# Не забудьте сбросить состояние контроллера при завершении
vjoy_device.reset()
