"""
Главное GUI приложение на Flet
"""
import asyncio
import logging
from typing import Optional

import flet as ft
from flet import Colors

from ..config.settings import settings
from ..utils.dependency import container, inject
from ..core.events import EventBus
from ..core.client_manager import ClientManagerImpl
from ..core.gamepad_manager import GamepadManagerImpl
from ..api.server import FastAPIServer
from ..utils.types import ClientManager, GamepadManager

logger = logging.getLogger(__name__)


class RemoteGamepadApp:
    """Основное GUI приложение"""
    
    def __init__(self) -> None:
        self.page: Optional[ft.Page] = None
        self.event_bus: EventBus = inject(EventBus)
        self.client_manager: ClientManager = inject(ClientManager)
        self.gamepad_manager: GamepadManager = inject(GamepadManager)
        self.server: FastAPIServer = inject(FastAPIServer)
        
        # UI элементы
        self.status_text: Optional[ft.Text] = None
        self.client_list: Optional[ft.ListView] = None
        self.server_controls: Optional[ft.Row] = None
        self.qr_image: Optional[ft.Image] = None
        
        logger.info("RemoteGamepadApp initialized")
    
    async def main(self, page: ft.Page) -> None:
        """Главная функция приложения"""
        self.page = page
        await self._setup_page()
        await self._build_ui()
        await self._setup_event_handlers()
        
        logger.info("GUI application started")
    
    async def _setup_page(self) -> None:
        """Настройка основной страницы"""
        if not self.page:
            return
        
        self.page.title = settings.gui_title
        self.page.window.width = settings.gui_width
        self.page.window.height = settings.gui_height
        self.page.theme_mode = ft.ThemeMode.DARK if settings.gui_theme == "dark" else ft.ThemeMode.LIGHT
        self.page.padding = 20
        self.page.spacing = 20
    
    async def _build_ui(self) -> None:
        """Построение пользовательского интерфейса"""
        if not self.page:
            return
        
        # Заголовок
        title = ft.Text(
            "🎮 RemoteGamepad Server",
            size=24,
            weight=ft.FontWeight.BOLD,
            color=Colors.BLUE_400
        )
        
        # Статус сервера
        self.status_text = ft.Text(
            "🔴 Сервер остановлен",
            size=16,
            color=Colors.RED_400
        )
        
        # Управление сервером
        self.server_controls = ft.Row([
            ft.ElevatedButton(
                "▶️ Запустить сервер",
                on_click=self._start_server,
                bgcolor=Colors.GREEN_400,
                color=Colors.WHITE
            ),
            ft.ElevatedButton(
                "⏹️ Остановить сервер",
                on_click=self._stop_server,
                bgcolor=Colors.RED_400,
                color=Colors.WHITE,
                disabled=True
            ),
            ft.ElevatedButton(
                "⚙️ Настройки",
                on_click=self._open_settings,
                bgcolor=Colors.BLUE_400,
                color=Colors.WHITE
            )
        ])
        
        # Информация о сервере
        server_info = ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Text("📊 Информация о сервере", weight=ft.FontWeight.BOLD),
                    ft.Text(f"🌐 Адрес: {settings.server.host}:{settings.server.port}"),
                    ft.Text(f"👥 Максимум клиентов: {settings.server.max_clients}"),
                    self.status_text
                ]),
                padding=15
            )
        )
        
        # Список клиентов
        self.client_list = ft.ListView(
            height=200,
            spacing=5,
            padding=ft.padding.all(10)
        )
        
        clients_card = ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Text("👥 Подключенные клиенты", weight=ft.FontWeight.BOLD),
                    self.client_list
                ]),
                padding=15
            )
        )
        
        # QR код для подключения
        self.qr_image = ft.Image(
            width=150,
            height=150,
            fit=ft.ImageFit.CONTAIN
        )
        
        qr_placeholder = ft.Container(
            content=ft.Text("Запустите сервер\nдля генерации QR", 
                           text_align=ft.TextAlign.CENTER, size=12),
            bgcolor=Colors.GREY_200,
            height=150,
            width=150,
            alignment=ft.alignment.center,
            border_radius=10
        )
        
        self.qr_container = ft.Stack([qr_placeholder])
        
        qr_card = ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Text("📱 QR-код для подключения", weight=ft.FontWeight.BOLD),
                    self.qr_container
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=15
            )
        )
        
        # Добавляем все элементы на страницу
        self.page.add(
            title,
            self.server_controls,
            ft.Row([
                ft.Column([server_info, clients_card], expand=2),
                ft.Column([qr_card], expand=1)
            ], expand=True)
        )
    
    async def _setup_event_handlers(self) -> None:
        """Настройка обработчиков событий"""
        # Подписываемся на события клиентов
        self.event_bus.subscribe_client("client_connected", self._on_client_connected)
        self.event_bus.subscribe_client("client_disconnected", self._on_client_disconnected)
        
        logger.debug("Event handlers set up")
    
    async def _start_server(self, e: ft.ControlEvent) -> None:
        """Запуск сервера"""
        try:
            if await self.server.start():
                await self._update_server_status(True)
                await self._update_qr_code()
                logger.info("Server started successfully")
            else:
                await self._show_error("Не удалось запустить сервер")
        except Exception as ex:
            logger.error(f"Failed to start server: {ex}")
            await self._show_error(f"Ошибка запуска сервера: {ex}")
    
    async def _stop_server(self, e: ft.ControlEvent) -> None:
        """Остановка сервера"""
        try:
            if await self.server.stop():
                await self._update_server_status(False)
                await self._clear_qr_code()
                logger.info("Server stopped successfully")
            else:
                await self._show_error("Не удалось остановить сервер")
        except Exception as ex:
            logger.error(f"Failed to stop server: {ex}")
            await self._show_error(f"Ошибка остановки сервера: {ex}")
    
    async def _open_settings(self, e: ft.ControlEvent) -> None:
        """Открытие настроек"""
        # TODO: Реализовать окно настроек
        logger.info("Settings dialog requested")
        await self._show_info("Настройки будут доступны в следующей версии")
    
    async def _update_server_status(self, is_running: bool) -> None:
        """Обновление статуса сервера в UI"""
        if not self.status_text or not self.server_controls:
            return
        
        if is_running:
            self.status_text.value = "🟢 Сервер запущен"
            self.status_text.color = ft.colors.GREEN_400
            # Обновляем кнопки
            self.server_controls.controls[0].disabled = True  # Запустить
            self.server_controls.controls[1].disabled = False  # Остановить
        else:
            self.status_text.value = "🔴 Сервер остановлен"
            self.status_text.color = ft.colors.RED_400
            # Обновляем кнопки
            self.server_controls.controls[0].disabled = False  # Запустить
            self.server_controls.controls[1].disabled = True  # Остановить
        
        if self.page:
            await self.page.update_async()
    
    async def _on_client_connected(self, client_info) -> None:
        """Обработчик подключения клиента"""
        await self._update_client_list()
        logger.debug(f"Client connected event handled: {client_info.client_id}")
    
    async def _on_client_disconnected(self, client_info) -> None:
        """Обработчик отключения клиента"""
        await self._update_client_list()
        logger.debug(f"Client disconnected event handled: {client_info.client_id}")
    
    async def _update_client_list(self) -> None:
        """Обновление списка клиентов"""
        if not self.client_list:
            return
        
        clients = await self.client_manager.get_clients()
        self.client_list.controls.clear()
        
        if not clients:
            self.client_list.controls.append(
                ft.Text("Нет подключенных клиентов", italic=True)
            )
        else:
            for client in clients:
                status_color = {
                    "connected": Colors.GREEN_400,
                    "active": Colors.BLUE_400,
                    "disconnected": Colors.RED_400,
                    "error": Colors.ORANGE_400
                }.get(client.status.value, Colors.GREY_400)
                
                client_card = ft.Container(
                    content=ft.Row([
                        ft.Text(f"🔗 {client.client_id}", expand=True),
                        ft.Text(f"📍 {client.ip_address}"),
                        ft.Icon(ft.icons.CIRCLE, color=status_color, size=12)
                    ]),
                    padding=10,
                    bgcolor=Colors.SURFACE_VARIANT,
                    border_radius=5
                )
                self.client_list.controls.append(client_card)
        
        if self.page:
            await self.page.update_async()
    
    async def _show_error(self, message: str) -> None:
        """Показ сообщения об ошибке"""
        if self.page:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(message),
                bgcolor=Colors.RED_400
            )
            self.page.snack_bar.open = True
            await self.page.update_async()
    
    async def _show_info(self, message: str) -> None:
        """Показ информационного сообщения"""
        if self.page:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(message),
                bgcolor=Colors.BLUE_400
            )
            self.page.snack_bar.open = True
            await self.page.update_async()
    
    async def _update_qr_code(self) -> None:
        """Обновление QR-кода"""
        try:
            import qrcode
            import io
            import socket
            
            # Получаем локальный IP
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            url = f"http://{local_ip}:{settings.server.port}"
            
            # Генерируем QR код
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(url)
            qr.make(fit=True)
            
            # Сохраняем во временный файл
            img = qr.make_image(fill_color="black", back_color="white")
            temp_path = "/tmp/qr_code.png"
            img.save(temp_path)
            
            # Обновляем UI
            if self.qr_container and self.page:
                self.qr_image.src = temp_path
                self.qr_container.controls.clear()
                self.qr_container.controls.append(self.qr_image)
                await self.page.update_async()
                
            logger.info(f"QR code generated for {url}")
            
        except Exception as e:
            logger.error(f"Error generating QR code: {e}")
            await self._show_error("Ошибка генерации QR-кода")
    
    async def _clear_qr_code(self) -> None:
        """Очистка QR-кода"""
        try:
            if self.qr_container and self.page:
                placeholder = ft.Container(
                    content=ft.Text("Сервер остановлен", 
                                   text_align=ft.TextAlign.CENTER, size=12),
                    bgcolor=Colors.GREY_200,
                    height=150,
                    width=150,
                    alignment=ft.alignment.center,
                    border_radius=10
                )
                self.qr_container.controls.clear()
                self.qr_container.controls.append(placeholder)
                await self.page.update_async()
        except Exception as e:
            logger.error(f"Error clearing QR code: {e}")


async def run_gui_app() -> None:
    """Запуск GUI приложения"""
    # Настройка DI контейнера
    event_bus = EventBus()
    client_manager = ClientManagerImpl(event_bus, settings.server.max_clients)
    gamepad_manager = GamepadManagerImpl(event_bus)
    fastapi_server = FastAPIServer(event_bus, client_manager, gamepad_manager)
    
    container.register_singleton(EventBus, event_bus)
    container.register_singleton(ClientManager, client_manager)
    container.register_singleton(GamepadManager, gamepad_manager)
    container.register_singleton(FastAPIServer, fastapi_server)
    
    # Создание и запуск приложения
    app = RemoteGamepadApp()
    
    # Запуск Flet приложения
    await ft.app_async(target=app.main)