import flet as ft


from pages.page_manager import init_gui


def main(page: ft.Page):
    page.title = "Joystick Controller"

    init_gui(page)

# Запуск приложения
if __name__ == '__main__':
    ft.app(target=main)
