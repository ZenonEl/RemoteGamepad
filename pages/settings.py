from config.default_settings import INTERVAL_SEND_TIMING, SERVER_IP, SERVER_PORT
from config.settings import get_setting, set_setting
from typing import TYPE_CHECKING

from pages.utils import page_resized

if TYPE_CHECKING:
    from pages.page_manager import PageManager


import flet as ft


class SettingsPage:

    @staticmethod
    def get_settings_gui(self: 'PageManager') -> ft.Column:
        self.page.title = "Настройки"

        settings_text = ft.Text(value="Настройки приложения", size=20)

        # Получаем настройки из файла
        server_ip = get_setting('SERVER_IP')
        server_port = get_setting('SERVER_PORT')
        send_interval = get_setting('INTERVAL_SEND_TIMING')

        # Настройки сервера
        server_ip_text = ft.Text("IP адрес сервера:")
        server_ip_field = ft.TextField(
            label="IP адрес сервера",
            border=ft.InputBorder.UNDERLINE,
            filled=True,
            hint_text=f"Введите IP адрес сервера, пример: {SERVER_IP}",
            value=server_ip
        )

        server_port_text = ft.Text("Порт сервера:")
        server_port_field = ft.TextField(
            label="Порт сервера",
            border=ft.InputBorder.UNDERLINE,
            filled=True,
            hint_text=f"Введите порт сервера, пример: {SERVER_PORT}",
            value=str(server_port)
        )

        send_interval_text = ft.Text("Интервал отправки данных от клиента на сервер (мс):")
        send_interval_field = ft.TextField(
            label="Интервал отправки данных от клиента на сервер",
            border=ft.InputBorder.UNDERLINE,
            filled=True,
            hint_text=f"Введите интервал отправки в миллисекундах, пример: {INTERVAL_SEND_TIMING}",
            value=str(send_interval)
        )

        # Настройки языка
        language_text = ft.Text("Язык интерфейса:")
        language_dropdown = ft.Dropdown(
            width=200,
            options=[
                ft.dropdown.Option("Русский"),
                ft.dropdown.Option("English")
            ],
            value="Русский",
            hint_text="Выберите язык интерфейса"
        )

        # Настройки интерфейса
        dynamic_layout_text = ft.Text("Сворачивание в трей:")
        dynamic_layout_switch = ft.Switch(value=False)

        apply_button = ft.ElevatedButton(text="Применить настройки", on_click=self.apply_settings)
        reset_button = ft.ElevatedButton(text="Сбросить настройки", on_click=self.reset_settings, color="red")
        back_button = ft.ElevatedButton(text="Назад", on_click=self.show_main_page)

        settings_content = ft.Column(
            controls=[
                settings_text,
                server_ip_text,
                server_ip_field,
                server_port_text,
                server_port_field,
                send_interval_text,
                send_interval_field,
                ft.Divider(),
                language_text,
                language_dropdown,
                ft.Divider(),
                dynamic_layout_text,
                dynamic_layout_switch,
                ft.Divider(),
                apply_button,
                reset_button,
                back_button
            ],
            alignment=ft.MainAxisAlignment.START,
            spacing=10,
            width=self.page.width,
            height=self.page.height,
            expand=True,
            scroll=ft.ScrollMode.AUTO
        )

        self.page.on_resized = lambda e: page_resized(e, self)
        return settings_content


class ResetAndApplySettings:
    @staticmethod
    def get_apply_alert(self: 'PageManager') -> ft.AlertDialog:
        dlg_modal = ft.AlertDialog(
            title=ft.Text("Подтверждение"),
            content=ft.Text("Вы уверены, что хотите применить настройки?"),
            actions=[
                ft.TextButton("Да", on_click=lambda e: self.confirm_apply_settings()),
                ft.TextButton("Нет", on_click=lambda e: self.close_dlg(dlg_modal)),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        return dlg_modal

    @staticmethod
    def process_apply_settings(self: 'PageManager') -> ft.AlertDialog:
            server_ip = self.page.controls[0].controls[2].value  # IP адрес сервера
            server_port = self.page.controls[0].controls[4].value  # Порт сервера
            send_interval = self.page.controls[0].controls[6].value  # Интервал отправки

            # Сохраняем настройки в файл
            set_setting('SERVER_IP', server_ip)
            set_setting('SERVER_PORT', int(server_port))  # Приводим к int
            set_setting('INTERVAL_SEND_TIMING', int(send_interval))  # Приводим к int

            # Показываем сообщение об успешном применении
            dlg = ft.AlertDialog(
                title=ft.Text("Настройки применены!"),
                content=ft.Text("Ваши настройки были успешно сохранены."),
                actions=[ft.TextButton("OK", on_click=lambda e: self.close_dlg(dlg))],
            )

            return dlg