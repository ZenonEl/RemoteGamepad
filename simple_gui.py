#!/usr/bin/env python3
"""
Простая версия GUI для тестирования
"""
import asyncio
import flet as ft


class SimpleApp:
    def __init__(self):
        self.clients_count = 0
        self.server_running = False
    
    async def main(self, page: ft.Page):
        page.title = "🎮 RemoteGamepad Server"
        page.window.width = 700
        page.window.height = 500
        page.theme_mode = ft.ThemeMode.DARK
        page.padding = 20
        
        # Заголовок
        title = ft.Text(
            "🎮 RemoteGamepad Server",
            size=24,
            weight=ft.FontWeight.BOLD,
            color=ft.colors.BLUE_400
        )
        
        # Статус
        self.status_text = ft.Text(
            "🔴 Сервер остановлен",
            size=16,
            color=ft.colors.RED_400
        )
        
        # Кнопки
        self.start_btn = ft.ElevatedButton(
            "▶️ Запустить сервер",
            on_click=self.start_server,
            bgcolor=ft.colors.GREEN_400
        )
        
        self.stop_btn = ft.ElevatedButton(
            "⏹️ Остановить сервер", 
            on_click=self.stop_server,
            bgcolor=ft.colors.RED_400,
            disabled=True
        )
        
        # Информация
        info_card = ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Text("📊 Информация", weight=ft.FontWeight.BOLD),
                    ft.Text("🌐 Адрес: 0.0.0.0:5002"),
                    ft.Text("👥 Максимум клиентов: 4"),
                    self.status_text
                ]),
                padding=20
            )
        )
        
        # Клиенты
        self.clients_text = ft.Text("👥 Подключенных клиентов: 0")
        
        # Добавляем на страницу
        page.add(
            title,
            ft.Row([self.start_btn, self.stop_btn]),
            info_card,
            self.clients_text,
            ft.Text("✅ GUI приложение работает корректно!", 
                   color=ft.colors.GREEN_400, size=16)
        )
    
    async def start_server(self, e):
        self.server_running = True
        self.status_text.value = "🟢 Сервер запущен"
        self.status_text.color = ft.colors.GREEN_400
        self.start_btn.disabled = True
        self.stop_btn.disabled = False
        
        # Симуляция подключения клиентов
        self.clients_count = 2
        self.clients_text.value = f"👥 Подключенных клиентов: {self.clients_count}"
        
        await e.page.update_async()
    
    async def stop_server(self, e):
        self.server_running = False
        self.status_text.value = "🔴 Сервер остановлен"
        self.status_text.color = ft.colors.RED_400
        self.start_btn.disabled = False
        self.stop_btn.disabled = True
        
        self.clients_count = 0
        self.clients_text.value = f"👥 Подключенных клиентов: {self.clients_count}"
        
        await e.page.update_async()


async def main():
    app = SimpleApp()
    await ft.app_async(target=app.main)


if __name__ == "__main__":
    asyncio.run(main())