import socket
import pygame
import json

# Конфигурация сокета
HOST = '192.168.0.106'  # IP-адрес вашего ПК
PORT = 8081              # Порт для подключения

pygame.init()
pygame.joystick.init()

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    clock = pygame.time.Clock()

    joysticks = [pygame.joystick.Joystick(x) for x in range(pygame.joystick.get_count())]

    prev_state = {}

    while True:
        for event in pygame.event.get():
            if event.type == pygame.JOYBUTTONDOWN or event.type == pygame.JOYBUTTONUP or event.type == pygame.JOYAXISMOTION:
                # Проверяем, что джойстик все еще подключен
                if event.joy < len(joysticks) and joysticks[event.joy].get_init():
                    data = {}
                    if event.type == pygame.JOYBUTTONDOWN:
                        data = {
                            "type": "button",
                            "action": "down",
                            "joystick": event.joy,
                            "button": event.button
                        }
                    elif event.type == pygame.JOYBUTTONUP:
                        data = {
                            "type": "button",
                            "action": "up",
                            "joystick": event.joy,
                            "button": event.button
                        }
                    elif event.type == pygame.JOYAXISMOTION:
                        joystick = joysticks[event.joy]
                        axis_count = joystick.get_numaxes()

                        axis_data = {}
                        if axis_count > 0:
                            axis_data["left_stick"] = {
                                "x": joystick.get_axis(0) if axis_count > 0 else 0,  # Ось X левого стика
                                "y": joystick.get_axis(1) if axis_count > 1 else 0   # Ось Y левого стика
                            }
                        if axis_count > 2:
                            axis_data["right_stick"] = {
                                "x": joystick.get_axis(2) if axis_count > 2 else 0,  # Ось X правого стика
                                "y": joystick.get_axis(3) if axis_count > 3 else 0   # Ось Y правого стика
                            }

                        # Сравниваем текущее состояние с предыдущим
                        if prev_state.get(event.joy, {}) != axis_data:
                            data = {
                                "type": "axis",
                                "joystick": event.joy,
                                "axes": axis_data
                            }
                            prev_state[event.joy] = axis_data

                    if data:
                        message = json.dumps(data)
                        s.sendall(message.encode())

        # Ограничиваем частоту обновления
        clock.tick(10)