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
        
        # НЕ запускаем периодические задачи здесь - они вызывают ошибки
        
        logger.info("GUI application started")
    
    async def _wait_for_page_ready(self) -> None:
        """Ожидание готовности страницы"""
        if not self.page:
            return
        
        # Проверяем что страница готова
        max_attempts = 10
        for attempt in range(max_attempts):
            try:
                # Пробуем получить доступ к странице
                if hasattr(self.page, '_page'):
                    break
                await asyncio.sleep(0.1)
            except Exception:
                await asyncio.sleep(0.1)
        
        logger.debug(f"Page ready after {attempt + 1} attempts")
    
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
        title = ft.Container(
            content=ft.Text(
                "🎮 RemoteGamepad Server",
                size=28,
                weight=ft.FontWeight.BOLD,
                color=Colors.WHITE
            ),
            padding=20,
            bgcolor=Colors.BLUE_900,
            border_radius=12,
            margin=ft.margin.only(bottom=20)
        )
        
        # Статус сервера
        self.status_text = ft.Container(
            content=ft.Text(
                "🔴 Сервер остановлен",
                size=18,
                weight=ft.FontWeight.NORMAL,
                color=Colors.WHITE
            ),
            padding=15,
            bgcolor=Colors.RED_900,
            border_radius=8,
            margin=ft.margin.only(bottom=20)
        )
        
        # Управление сервером
        self.server_controls = ft.Container(
            content=ft.Row([
                ft.ElevatedButton(
                    "▶️ Запустить сервер",
                    on_click=self._start_server,
                    bgcolor=Colors.GREEN_600,
                    color=Colors.WHITE,
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=8),
                        padding=15
                    )
                ),
                ft.ElevatedButton(
                    "⏹️ Остановить сервер",
                    on_click=self._stop_server,
                    bgcolor=Colors.RED_600,
                    color=Colors.WHITE,
                    disabled=True,
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=8),
                        padding=15
                    )
                ),
                ft.ElevatedButton(
                    "⚙️ Настройки",
                    on_click=self._open_settings,
                    bgcolor=Colors.BLUE_600,
                    color=Colors.WHITE,
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=8),
                        padding=15
                    )
                ),
                ft.ElevatedButton(
                    "🔄 Обновить список",
                    on_click=self._refresh_client_list,
                    bgcolor=Colors.ORANGE_600,
                    color=Colors.WHITE,
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=8),
                        padding=15
                    )
                )
            ], spacing=10),
            padding=20,
            bgcolor=Colors.GREY_900,
            border_radius=12,
            margin=ft.margin.only(bottom=20)
        )
        
        # Поле для IP адреса сервера
        self.server_ip_field = ft.TextField(
            value=settings.server.host,
            width=250,
            hint_text="IP для запуска сервера (0.0.0.0 = все интерфейсы)",
            border_color=Colors.BLUE_400,
            focused_border_color=Colors.BLUE_200,
            hint_style=ft.TextStyle(color=Colors.GREY_400)
        )
        
        self.server_ip_input = ft.Container(
            content=ft.Column([
                ft.Text("🌐 IP адрес сервера", size=16, weight=ft.FontWeight.NORMAL, color=Colors.WHITE),
                self.server_ip_field
            ]),
            padding=15,
            bgcolor=Colors.GREY_900,
            border_radius=8,
            margin=ft.margin.only(bottom=10)
        )
        
        # Поле для IP адреса в QR-кода
        self.qr_ip_field = ft.TextField(
            value="100.102.5.118",
            width=250,
            hint_text="IP для подключения клиентов",
            border_color=Colors.GREEN_400,
            focused_border_color=Colors.GREEN_200,
            hint_style=ft.TextStyle(color=Colors.GREY_400)
        )
        
        self.qr_ip_input = ft.Container(
            content=ft.Column([
                ft.Text("📱 IP для QR-кода", size=16, weight=ft.FontWeight.NORMAL, color=Colors.WHITE),
                self.qr_ip_field
            ]),
            padding=15,
            bgcolor=Colors.GREY_900,
            border_radius=8,
            margin=ft.margin.only(bottom=20)
        )
        
        # Информация о сервере
        server_info = ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Text("📊 Информация о сервере", weight=ft.FontWeight.BOLD),
                    ft.Text(f"🌐 Сервер: {settings.server.host}:{settings.server.port}"),
                    ft.Text(f"👥 Максимум клиентов: {settings.server.max_clients}"),
                    self.status_text,
                    ft.Divider(),
                    ft.Text("🔧 Настройки подключения:", weight=ft.FontWeight.BOLD),
                    ft.Text("IP сервера (для запуска):"),
                    self.server_ip_input,
                    ft.Text("IP для QR-кода (для клиентов):"),
                    self.qr_ip_input
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
        
        # Собираем все элементы в ScrollView
        main_content = ft.Column([
            title,
            self.server_controls,
            ft.Row([
                ft.Column([server_info, clients_card], expand=2),
                ft.Column([qr_card], expand=1)
            ], expand=True)
        ], spacing=20)
        
        # Добавляем прокрутку через ListView
        self.page.add(
            ft.ListView(
                controls=[main_content],
                expand=True,
                spacing=20,
                padding=20
            )
        )
        
        logger.info("UI built and ready")
    
    async def _setup_event_handlers(self) -> None:
        """Настройка обработчиков событий"""
        # Подписываемся на события клиентов
        self.event_bus.subscribe_client("client_connected", self._on_client_connected)
        self.event_bus.subscribe_client("client_disconnected", self._on_client_disconnected)
        self.event_bus.subscribe_client("client_profile_updated", self._on_client_profile_updated)
        
        # Запускаем периодическое обновление списка клиентов
        # НЕ используем asyncio.create_task() здесь - это может вызвать проблемы с event loop
        
        logger.debug("Event handlers set up")
    
    async def _start_server(self, e: ft.ControlEvent) -> None:
        """Запуск сервера"""
        try:
            # Получаем IP из поля ввода
            server_ip = self.server_ip_field.value if self.server_ip_field.value else "0.0.0.0"
            
            # Обновляем настройки сервера
            self.server._host = server_ip
            logger.info(f"Starting server on {server_ip}:{settings.server.port}")
            
            # Запускаем сервер в отдельном потоке
            import threading
            server_thread = threading.Thread(
                target=self._run_server_in_thread,
                args=(server_ip,),
                daemon=True
            )
            server_thread.start()
            
            # Ждем немного для запуска
            await asyncio.sleep(1.0)
            
            # Проверяем статус через uvicorn
            if hasattr(self.server, '_server_instance') and self.server._server_instance:
                # Устанавливаем флаг запуска
                self.server.is_running = True
                await self._update_server_status(True)
                await self._update_qr_code()
                logger.info("Server started successfully")
            else:
                # Дополнительная проверка - возможно сервер уже запущен
                await asyncio.sleep(0.5)
                if hasattr(self.server, '_server_instance') and self.server._server_instance:
                    self.server.is_running = True
                    await self._update_server_status(True)
                    await self._update_qr_code()
                    logger.info("Server started successfully (delayed check)")
                else:
                    await self._show_error("Не удалось запустить сервер")
                
        except Exception as ex:
            logger.error(f"Failed to start server: {ex}")
            await self._show_error(f"Ошибка запуска сервера: {ex}")
    
    def _run_server_in_thread(self, host: str) -> None:
        """Запуск сервера в отдельном потоке"""
        try:
            import asyncio
            import uvicorn
            
            # Создаем новый event loop для потока
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Запускаем сервер
            config = uvicorn.Config(
                app=self.server.app,
                host=host,
                port=settings.server.port,
                log_level=settings.server.log_level.lower(),
                access_log=settings.server.debug
            )
            
            server = uvicorn.Server(config)
            self.server._server_instance = server
            self.server._host = host
            
            # Устанавливаем флаг запуска
            self.server.is_running = True
            logger.info(f"Server thread started on {host}:{settings.server.port}")
            
            # Запускаем сервер
            loop.run_until_complete(server.serve())
            
        except Exception as e:
            logger.error(f"Error in server thread: {e}")
            self.server.is_running = False
    
    async def _stop_server(self, e: ft.ControlEvent) -> None:
        """Остановка сервера"""
        try:
            # Останавливаем сервер
            if hasattr(self.server, '_server_instance') and self.server._server_instance:
                self.server._server_instance.should_exit = True
                self.server.is_running = False
                logger.info("Server stop signal sent")
            else:
                logger.warning("No server instance found")
            
            # Удаляем всех клиентов при остановке сервера
            try:
                await self.client_manager.cleanup_all_clients()
                logger.info("All clients removed after server stop")
            except Exception as ex:
                logger.error(f"Error cleaning up clients: {ex}")
            
            # Обновляем UI
            await self._update_server_status(False)
            await self._clear_qr_code()
            await self._update_client_list()
            logger.info("Server stopped successfully")
            
        except Exception as ex:
            logger.error(f"Failed to stop server: {ex}")
            await self._show_error(f"Ошибка остановки сервера: {ex}")
    
    async def _open_settings(self, e: ft.ControlEvent) -> None:
        """Открытие настроек"""
        # TODO: Реализовать окно настроек
        logger.info("Settings dialog requested")
    
    async def _refresh_client_list(self, e: ft.ControlEvent) -> None:
        """Принудительное обновление списка клиентов"""
        logger.info("Manual refresh of client list requested")
        try:
            # Получаем клиентов напрямую без await
            clients = self.client_manager._clients.values()
            await self._update_client_list_direct(list(clients))
        except Exception as ex:
            logger.error(f"Error refreshing client list: {ex}")
            await self._show_error(f"Ошибка обновления: {ex}")
    
    async def _update_server_status(self, is_running: bool) -> None:
        """Обновление статуса сервера в UI"""
        if not self.status_text or not self.server_controls:
            return
        
        if is_running:
            self.status_text.content.value = "🟢 Сервер запущен"
            self.status_text.bgcolor = Colors.GREEN_900
            # Обновляем кнопки
            self.server_controls.content.controls[0].disabled = True  # Запустить
            self.server_controls.content.controls[1].disabled = False  # Остановить
        else:
            self.status_text.content.value = "🔴 Сервер остановлен"
            self.status_text.bgcolor = Colors.RED_900
            # Обновляем кнопки
            self.server_controls.content.controls[0].disabled = False  # Запустить
            self.server_controls.content.controls[1].disabled = True  # Остановить
        
        # ПРИНУДИТЕЛЬНО обновляем элементы
        if self.status_text:
            self.status_text.update()
        if self.server_controls:
            self.server_controls.update()
            
        logger.info(f"Server status updated: {'running' if is_running else 'stopped'}")
    
    async def _on_client_connected(self, client_info) -> None:
        """Обработчик подключения клиента"""
        profile_name = getattr(client_info, 'profile_name', None) or 'Без имени'
        logger.info(f"🟢 Клиент подключился: {client_info.client_id} ({client_info.ip_address}) - {profile_name}")
        await self._update_client_list()
        logger.debug(f"Client connected event handled: {client_info.client_id}")
    
    async def _on_client_disconnected(self, client_info) -> None:
        """Обработчик отключения клиента"""
        profile_name = getattr(client_info, 'profile_name', None) or 'Без имени'
        logger.info(f"🔴 Клиент отключился: {client_info.client_id} ({client_info.ip_address}) - {profile_name}")
        await self._update_client_list()
        logger.debug(f"Client disconnected event handled: {client_info.client_id}")
    
    async def _on_client_profile_updated(self, client_info) -> None:
        """Обработчик обновления профиля клиента"""
        profile_name = getattr(client_info, 'profile_name', None) or 'Без имени'
        logger.info(f"🔄 Профиль клиента обновлен: {client_info.client_id} -> {profile_name}")
        await self._update_client_list()
        logger.debug(f"Client profile updated event handled: {client_info.client_id}")
    
    async def _update_client_list(self) -> None:
        """Обновление списка клиентов"""
        if not self.client_list:
            return
        
        try:
            # Получаем клиентов напрямую без await
            clients = list(self.client_manager._clients.values())
            await self._update_client_list_direct(clients)
        except Exception as ex:
            logger.error(f"Error updating client list: {ex}")
            # Fallback - показываем ошибку
            if self.client_list:
                self.client_list.controls.clear()
                self.client_list.controls.append(
                    ft.Text(f"Ошибка загрузки: {ex}", color=Colors.RED_400)
                )
                self.client_list.update()
    
    async def _update_client_list_direct(self, clients: list) -> None:
        """Прямое обновление списка клиентов без обращения к ClientManager"""
        if not self.client_list:
            return
        
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
                
                # Показываем имя клиента если есть
                client_name = getattr(client, 'profile_name', None) or client.client_id
                
                client_card = ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Text(f"🔗 {client_name}", weight=ft.FontWeight.BOLD, expand=True, color=Colors.WHITE),
                            ft.Icon(ft.Icons.CIRCLE, color=status_color, size=16)
                        ]),
                        ft.Text(f"📍 {client.ip_address}", size=12, color=Colors.GREY_300),
                        ft.Text(f"🆔 {client.client_id[:8]}...", size=10, color=Colors.GREY_400),
                        ft.Text(f"⏰ {self._format_time(client.connected_at)}", size=10, color=Colors.GREY_400)
                    ]),
                    padding=20,
                    bgcolor=Colors.GREY_800,
                    border_radius=12,
                    border=ft.border.all(1, Colors.GREY_700),
                    margin=ft.margin.only(bottom=10),
                    shadow=ft.BoxShadow(
                        spread_radius=1,
                        blur_radius=15,
                        color=Colors.BLACK,
                        offset=ft.Offset(2, 2)
                    )
                )
                self.client_list.controls.append(client_card)
        
        if self.client_list:
            self.client_list.update()
            
        logger.info(f"Client list updated directly with {len(clients)} clients")
    
    def _format_time(self, timestamp: float) -> str:
        """Форматирование времени подключения"""
        try:
            from datetime import datetime
            dt = datetime.fromtimestamp(timestamp)
            now = datetime.now()
            diff = now - dt
            
            if diff.days > 0:
                return f"{diff.days}д {diff.seconds // 3600}ч"
            elif diff.seconds > 3600:
                return f"{diff.seconds // 3600}ч {(diff.seconds % 3600) // 60}м"
            elif diff.seconds > 60:
                return f"{diff.seconds // 60}м"
            else:
                return f"{diff.seconds}с"
        except:
            return "???"
    
    async def _show_error(self, message: str) -> None:
        """Показ сообщения об ошибке"""
        # НЕ показываем snackbar - Flet не готов
        logger.error(f"Error: {message}")
    
    async def _show_info(self, message: str) -> None:
        """Показ информационного сообщения"""
        # НЕ показываем snackbar - Flet не готов
        logger.info(f"Info: {message}")
    
    async def _update_qr_code(self) -> None:
        """Обновление QR-кода"""
        try:
            import qrcode
            import socket
            import os
            
            # Получаем IP из поля ввода для QR-кода
            qr_ip = self.qr_ip_field.value if self.qr_ip_field.value else "100.102.5.118"
            url = f"http://{qr_ip}:{settings.server.port}"
            
            logger.info(f"Generating QR code for URL: {url}")
            
            # Генерируем QR код
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(url)
            qr.make(fit=True)
            
            # Создаем изображение
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Сохраняем в проектную папку (более надежно)
            qr_dir = os.path.join(os.getcwd(), "temp")
            os.makedirs(qr_dir, exist_ok=True)
            qr_path = os.path.join(qr_dir, "qr_code.png")
            
            img.save(qr_path)
            logger.info(f"QR code saved to: {qr_path}")
            
            # Проверяем, что файл создался
            if not os.path.exists(qr_path):
                raise FileNotFoundError(f"QR file not created: {qr_path}")
            
            file_size = os.path.getsize(qr_path)
            logger.info(f"QR file size: {file_size} bytes")
            
            # Обновляем UI
            if self.qr_container:
                # Очищаем старые элементы
                self.qr_container.controls.clear()
                
                # Создаем новое изображение
                qr_img = ft.Image(
                    src=qr_path,
                    width=150,
                    height=150,
                    fit=ft.ImageFit.CONTAIN,
                    border_radius=10
                )
                
                self.qr_container.controls.append(qr_img)
                
                self.qr_container.update()
                
                logger.info("QR code UI updated successfully")
                logger.info(f"QR-код сгенерирован для {qr_ip}")
            
        except Exception as e:
            logger.error(f"Error generating QR code: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            await self._show_error(f"Ошибка генерации QR-кода: {str(e)}")
    
    async def _clear_qr_code(self) -> None:
        """Очистка QR-кода"""
        try:
            if self.qr_container:
                placeholder = ft.Container(
                    content=ft.Text("Сервер остановлен\nНажмите 'Запустить'", 
                                   text_align=ft.TextAlign.CENTER, size=12),
                    bgcolor=Colors.GREY_200,
                    height=150,
                    width=150,
                    alignment=ft.alignment.center,
                    border_radius=10
                )
                self.qr_container.controls.clear()
                self.qr_container.controls.append(placeholder)
                
                self.qr_container.update()
                
                logger.info("QR code cleared, showing placeholder")
                
        except Exception as e:
            logger.error(f"Error clearing QR code: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")


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