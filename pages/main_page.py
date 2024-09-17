import threading
import time
from typing import TYPE_CHECKING

import flet as ft

from config.default_settings import DynamicTempSettings
from pages.utils import page_resized
from server import check_server_status, run_flask

if TYPE_CHECKING:
    from pages.page_manager import PageManager

class MainPage:

    @staticmethod
    def get_main_page_ui(self: 'PageManager') -> ft.Column:
        server_status = ft.Text(value="Статус сервера: Ожидание...", size=20)

        def update_status():
            if check_server_status(self.page):
                server_status.value = "Статус сервера: Работает"
                server_status.color = "green"
                toggle_button.text = "Проверить статус"
            else:
                server_status.value = "Статус сервера: Не работает"
                server_status.color = "red"
                toggle_button.text = "Запустить"
            self.page.update()

        def start_server(e):
            server_running = DynamicTempSettings.SERVER_RUNNING
            if server_running:
                # Если сервер работает, проверяем статус
                update_status()
            else:
                # Запуск сервера
                server_running = True
                server_thread = threading.Thread(target=run_flask, daemon=True)
                server_thread.start()
                time.sleep(1)  # Небольшая задержка для запуска сервера
                update_status()

        toggle_button = ft.ElevatedButton(text="Запустить", on_click=start_server)

        # Инициализация статуса при запуске
        update_status()

        nav_menu = ft.Column(
            controls=[
                toggle_button,
                ft.ElevatedButton(text="Настройки", on_click=self.show_settings_page),
                ft.ElevatedButton(text="Статистика", on_click=lambda e: self.show_statistics_page()),
            ],
            alignment=ft.MainAxisAlignment.START,
            spacing=10
        )

        self.current_content = ft.Container(
            content=ft.Column(
                controls=[
                    server_status,
                    ft.Divider(),
                    nav_menu
                ],
                alignment=ft.MainAxisAlignment.START,
                spacing=20,
                scroll=ft.ScrollMode.ALWAYS,
                width=self.page.width,
                height=self.page.height,
                expand=True
            ),
            width=self.page.width,
            height=self.page.height,
            expand=True,
            adaptive=True
        )

        # Привязка обработчика к событию изменения размера окна
        self.page.on_resized = lambda e: page_resized(e, self)
        return self.current_content

