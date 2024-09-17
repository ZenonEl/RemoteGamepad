from config.default_settings import INTERVAL_SEND_TIMING, SERVER_IP, SERVER_PORT
from config.settings import set_setting
from pages.main_page import MainPage
from pages.settings import ResetAndApplySettings, SettingsPage

import flet as ft

from pages.utils import page_resized

class PageManager:
    def __init__(self, page: ft.Page):
        self.page = page
        self.current_content = None

    def apply_settings(self, e=None):
        """Применяет настройки и сохраняет их в файл пользователя."""
        # Создаем диалог для подтверждения применения настроек
        dlg_modal: ft.AlertDialog = ResetAndApplySettings.get_apply_alert(self)

        self.page.overlay.append(dlg_modal)
        dlg_modal.open = True
        self.page.update()


    def confirm_apply_settings(self):
        """Подтверждает применение настроек и сохраняет их."""
        # Получаем значения из полей ввода
        dlg: ft.AlertDialog = ResetAndApplySettings.process_apply_settings(self)
        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()

    def reset_settings(self, e=None):
        """Сбрасывает настройки к дефолтным значениям."""
        # Создаем диалог для подтверждения сброса настроек
        dlg_modal = ft.AlertDialog(
            title=ft.Text("Подтверждение"),
            content=ft.Text("Вы уверены, что хотите сбросить настройки к дефолтным значениям?"),
            actions=[
                ft.TextButton("Да", on_click=lambda e: self.confirm_reset_settings()),
                ft.TextButton("Нет", on_click=lambda e: self.close_dlg(dlg_modal)),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.page.overlay.append(dlg_modal)
        dlg_modal.open = True
        self.page.update()

    def confirm_reset_settings(self):
        """Подтверждает сброс настроек к дефолтным значениям."""
        # Сбрасываем настройки к дефолтным значениям
        set_setting('SERVER_IP', SERVER_IP)
        set_setting('SERVER_PORT', SERVER_PORT)
        set_setting('INTERVAL_SEND_TIMING', INTERVAL_SEND_TIMING)

        # Показываем сообщение о сбросе настроек
        dlg = ft.AlertDialog(
            title=ft.Text("Настройки сброшены!"),
            content=ft.Text("Ваши настройки были сброшены к дефолтным значениям. Откройте вкладку вновь чтобы обновить значения в полях."),
            actions=[ft.TextButton("OK", on_click=lambda e: self.close_dlg(dlg))],
        )
        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()

    def close_dlg(self, dlg):
        """Закрывает диалог."""
        dlg.open = False
        self.page.update()

    def clear_current_content(self):
        """Удаляет текущие элементы страницы."""
        if self.current_content:
            self.page.controls.remove(self.current_content)
            self.current_content = None
            self.page.update()

    def show_main_page(self, e=None):
        """Отображает главную страницу."""
        self.clear_current_content()

        self.current_content = MainPage.get_main_page_ui(self)

        self.page.add(self.current_content)
        self.page.update()

    def show_statistics_page(self):
        """Отображает страницу статистики (пока заглушка)."""
        self.clear_current_content()

        stats_text = ft.Text(value="Статистика приложения", size=20)
        back_button = ft.ElevatedButton(text="Назад", on_click=self.show_main_page)

        stats_content = ft.Column(
            controls=[
                stats_text,
                back_button
            ],
            alignment=ft.MainAxisAlignment.START,
            spacing=10
        )

        self.current_content = stats_content
        self.page.add(self.current_content)

    def show_settings_page(self, e=None):
        """Отображает страницу настройки."""
        self.clear_current_content()

        settings_content = SettingsPage.get_settings_gui(self)

        self.current_content = settings_content
        self.page.add(self.current_content)

    def show_loading_ring_page(self):
        """Отображает индикатор загрузки страницы."""
        self.clear_current_content()

        loading_ring = ft.ProgressRing()
        back_button = ft.ElevatedButton(text="Назад", on_click=self.show_main_page)

        loading_content = ft.Column(
            controls=[
                loading_ring,
                back_button
            ],
            alignment=ft.MainAxisAlignment.START,
            spacing=10
        )

        self.current_content = loading_content
        self.page.on_resized = lambda e: page_resized(e, self)
        self.page.add(self.current_content)


def init_gui(page):
    page_manager = PageManager(page)
    page_manager.show_main_page()