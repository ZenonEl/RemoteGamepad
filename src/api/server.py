"""
FastAPI сервер для RemoteGamepad
"""
import asyncio
import logging
import time
import os
from typing import Dict, List, Optional
import json
import qrcode
import io
import base64
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, Response
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from ..utils.types import GamepadEvent, GamepadEventType, ClientInfo, ClientStatus
from ..api.models import (
    GamepadInputData, ServerStatusResponse, ConnectionResponse, 
    ErrorResponse, WebSocketMessage, WebSocketMessageType, QRCodeRequest
)
from ..core.events import EventBus
from ..core.client_manager import ClientManagerImpl
from ..core.gamepad_manager import GamepadManagerImpl
from ..config.settings import settings
from ..utils.dependency import container

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Менеджер WebSocket подключений"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        """Подключение WebSocket клиента"""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"WebSocket client {client_id} connected")
    
    def disconnect(self, client_id: str):
        """Отключение WebSocket клиента"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"WebSocket client {client_id} disconnected")
    
    async def send_personal_message(self, message: dict, client_id: str):
        """Отправка персонального сообщения"""
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error sending message to {client_id}: {e}")
                self.disconnect(client_id)
    
    async def broadcast(self, message: dict):
        """Отправка сообщения всем подключенным клиентам"""
        for client_id in list(self.active_connections.keys()):
            await self.send_personal_message(message, client_id)


class FastAPIServer:
    """FastAPI сервер с интеграцией в нашу архитектуру"""
    
    def __init__(self, event_bus: EventBus, client_manager: ClientManagerImpl, gamepad_manager: GamepadManagerImpl):
        self.app: Optional[FastAPI] = None
        self.server: Optional[uvicorn.Server] = None
        self.server_task: Optional[asyncio.Task] = None
        self.event_bus: EventBus = event_bus
        self.client_manager: ClientManagerImpl = client_manager
        self.gamepad_manager: GamepadManagerImpl = gamepad_manager
        self.connection_manager = ConnectionManager()
        self.start_time = time.time()
        self.is_running = False
        
        # Атрибуты для управления сервером
        self._host = "0.0.0.0"
        self._server_instance = None
        
        self._setup_app()
        self._setup_event_handlers()
        
        logger.info("FastAPI server initialized")
    
    def _setup_app(self):
        """Настройка FastAPI приложения"""
        
        @asynccontextmanager
        async def lifespan(app: FastAPI):
            # Startup
            logger.info("FastAPI server starting up...")
            yield
            # Shutdown  
            logger.info("FastAPI server shutting down...")
            await self.gamepad_manager.cleanup()
        
        self.app = FastAPI(
            title="RemoteGamepad Server",
            description="Сервер для удаленного управления геймпадом",
            version="2.0.0",
            lifespan=lifespan
        )
        
        # CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # В продакшене ограничить
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Static files
        try:
            static_dir = os.path.join(os.getcwd(), "static")
            if os.path.exists(static_dir):
                self.app.mount("/static", StaticFiles(directory=static_dir), name="static")
                logger.info(f"Static files mounted from: {static_dir}")
            else:
                logger.warning(f"Static directory not found: {static_dir}")
        except Exception as e:
            logger.warning(f"Could not mount static files: {e}")
        
        self._setup_routes()
    
    def _setup_routes(self):
        """Настройка маршрутов"""
        
        @self.app.get("/", response_class=HTMLResponse)
        async def index():
            """Главная страница"""
            try:
                template_path = os.path.join(os.getcwd(), "templates", "index.html")
                if os.path.exists(template_path):
                    with open(template_path, "r", encoding="utf-8") as f:
                        return f.read()
                else:
                    logger.warning(f"Template not found: {template_path}")
                    return "<h1>RemoteGamepad Server</h1><p>Template not found</p>"
            except Exception as e:
                logger.error(f"Error loading template: {e}")
                return f"<h1>RemoteGamepad Server</h1><p>Error loading template: {e}</p>"
        
        @self.app.get("/status", response_model=ServerStatusResponse)
        async def get_status():
            """Статус сервера"""
            clients = await self.client_manager.get_clients()
            gamepad_count = await self.gamepad_manager.get_gamepad_count()
            
            return ServerStatusResponse(
                status="running" if self.is_running else "stopped",
                uptime=int(time.time() - self.start_time),
                clients_count=len(clients),
                server_info={
                    "host": settings.server.host,
                    "port": settings.server.port,
                    "max_clients": settings.server.max_clients,
                    "gamepads_active": gamepad_count,
                    "max_gamepads": settings.max_gamepads
                }
            )
        
        @self.app.post("/connect", response_model=ConnectionResponse)
        async def connect_client(client_info: dict):
            """Подключение нового клиента"""
            try:
                # Генерируем ID клиента
                client_id = await self.client_manager.generate_client_id(
                    client_info.get("ip_address", "unknown")
                )
                
                # Создаем информацию о клиенте
                client = ClientInfo(
                    client_id=client_id,
                    ip_address=client_info.get("ip_address", "unknown"),
                    user_agent=client_info.get("user_agent", "unknown"),
                    connected_at=time.time(),
                    status=ClientStatus.CONNECTING
                )
                
                # Добавляем клиента
                if await self.client_manager.add_client(client):
                    # Создаем геймпад для клиента
                    gamepad_id = await self.gamepad_manager.create_gamepad(client_id)
                    
                    if gamepad_id:
                        await self.client_manager.assign_gamepad(client_id, gamepad_id)
                        
                        return ConnectionResponse(
                            success=True,
                            client_id=client_id,
                            gamepad_id=gamepad_id,
                            message="Connected successfully"
                        )
                    else:
                        await self.client_manager.remove_client(client_id)
                        raise HTTPException(
                            status_code=503, 
                            detail="Cannot create gamepad - limit reached"
                        )
                else:
                    raise HTTPException(
                        status_code=503,
                        detail="Cannot connect - server full"
                    )
                    
            except Exception as e:
                logger.error(f"Error connecting client: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/gamepad_data")
        async def handle_gamepad_data(data: GamepadInputData):
            """Обработка данных геймпада"""
            try:
                client_id = data.client_id
                if not client_id:
                    raise HTTPException(status_code=400, detail="Client ID required")
                
                # Получаем геймпад для клиента
                gamepad_id = await self.gamepad_manager.get_gamepad_for_client(client_id)
                if not gamepad_id:
                    raise HTTPException(status_code=404, detail="Gamepad not found for client")
                
                # Обрабатываем события осей
                if data.type == "axis" and data.axes:
                    axes_data = data.axes
                    
                    # Левый стик
                    if axes_data.left_stick:
                        for axis, value in axes_data.left_stick.items():
                            axis_name = f"AxisL{axis}"
                            event = GamepadEvent(
                                client_id=client_id,
                                event_type=GamepadEventType.AXIS_MOVE,
                                axis_name=axis_name,
                                value=float(value),
                                timestamp=time.time()
                            )
                            await self.gamepad_manager.send_event(gamepad_id, event)
                    
                    # Правый стик  
                    if axes_data.right_stick:
                        for axis, value in axes_data.right_stick.items():
                            axis_name = f"AxisR{axis}"
                            event = GamepadEvent(
                                client_id=client_id,
                                event_type=GamepadEventType.AXIS_MOVE,
                                axis_name=axis_name,
                                value=float(value),
                                timestamp=time.time()
                            )
                            await self.gamepad_manager.send_event(gamepad_id, event)
                
                # Обрабатываем события кнопок
                if data.buttons:
                    for button in data.buttons:
                        event_type = GamepadEventType.BUTTON_PRESS if button.pressed else GamepadEventType.BUTTON_RELEASE
                        event = GamepadEvent(
                            client_id=client_id,
                            event_type=event_type,
                            button_code=button.name,
                            value=button.value,
                            timestamp=time.time()
                        )
                        await self.gamepad_manager.send_event(gamepad_id, event)
                
                return {"status": "success"}
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error processing gamepad data: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/qr")
        async def generate_qr_code(request: QRCodeRequest = Depends()):
            """Генерация QR кода для подключения"""
            try:
                # Получаем локальный IP адрес
                import socket
                hostname = socket.gethostname()
                local_ip = socket.gethostbyname(hostname)
                
                # Формируем URL для подключения
                url = f"http://{local_ip}:{settings.server.port}"
                
                # Создаем QR код
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=10,
                    border=4,
                )
                qr.add_data(url)
                qr.make(fit=True)
                
                # Генерируем изображение
                img = qr.make_image(fill_color="black", back_color="white")
                
                # Конвертируем в base64
                buffer = io.BytesIO()
                img.save(buffer, format='PNG')
                img_str = base64.b64encode(buffer.getvalue()).decode()
                
                return {
                    "qr_code": f"data:image/png;base64,{img_str}",
                    "url": url,
                    "format": "png"
                }
                
            except Exception as e:
                logger.error(f"Error generating QR code: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.websocket("/ws/{client_id}")
        async def websocket_endpoint(websocket: WebSocket, client_id: str):
            """WebSocket эндпоинт для real-time коммуникации"""
            await self.connection_manager.connect(websocket, client_id)
            try:
                while True:
                    data = await websocket.receive_text()
                    message = json.loads(data)
                    
                    # Обрабатываем WebSocket сообщения
                    if message.get("type") == "ping":
                        await self.connection_manager.send_personal_message({
                            "type": "pong",
                            "timestamp": time.time()
                        }, client_id)
                    
                    # Другие типы сообщений...
                    
            except WebSocketDisconnect:
                self.connection_manager.disconnect(client_id)
                # Удаляем клиента
                await self.client_manager.remove_client(client_id)
    
    def _setup_event_handlers(self):
        """Настройка обработчиков событий"""
        
        async def on_client_connected(client_info: ClientInfo):
            """Обработчик подключения клиента"""
            await self.connection_manager.broadcast({
                "type": WebSocketMessageType.CLIENT_CONNECTED,
                "data": {
                    "client_id": client_info.client_id,
                    "ip_address": client_info.ip_address
                }
            })
        
        async def on_client_disconnected(client_info: ClientInfo):
            """Обработчик отключения клиента"""
            # Удаляем геймпад клиента
            gamepad_id = await self.gamepad_manager.get_gamepad_for_client(client_info.client_id)
            if gamepad_id:
                await self.gamepad_manager.remove_gamepad(gamepad_id)
            
            await self.connection_manager.broadcast({
                "type": WebSocketMessageType.CLIENT_DISCONNECTED,
                "data": {
                    "client_id": client_info.client_id
                }
            })
        
        self.event_bus.subscribe_client("client_connected", on_client_connected)
        self.event_bus.subscribe_client("client_disconnected", on_client_disconnected)
    
    async def start(self) -> bool:
        """Запуск сервера"""
        if self.is_running:
            logger.warning("Server is already running")
            return False
        
        try:
            config = uvicorn.Config(
                app=self.app,
                host=settings.server.host,
                port=settings.server.port,
                log_level=settings.server.log_level.lower(),
                access_log=settings.server.debug
            )
            
            self.server = uvicorn.Server(config)
            self.server_task = asyncio.create_task(self.server.serve())
            
            self.is_running = True
            self.start_time = time.time()
            
            logger.info(f"FastAPI server started on {settings.server.host}:{settings.server.port}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start server: {e}")
            self.is_running = False
            return False
    
    async def stop(self) -> bool:
        """Остановка сервера"""
        if not self.is_running:
            logger.warning("Server is not running")
            return False
        
        try:
            if self.server:
                self.server.should_exit = True
                
            if self.server_task:
                self.server_task.cancel()
                try:
                    await self.server_task
                except asyncio.CancelledError:
                    pass
            
            # Очищаем ресурсы
            await self.gamepad_manager.cleanup()
            
            self.is_running = False
            logger.info("FastAPI server stopped")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping server: {e}")
            return False
    
    @property
    def status(self) -> dict:
        """Статус сервера"""
        return {
            "is_running": self.is_running,
            "start_time": self.start_time,
            "uptime": time.time() - self.start_time if self.is_running else 0
        }