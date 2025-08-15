"""
Менеджер клиентов
"""
import time
import asyncio
import logging
from typing import Dict, List, Optional
from uuid import uuid4

from ..utils.types import ClientInfo, ClientStatus, ClientManager as IClientManager
from ..core.events import EventBus

logger = logging.getLogger(__name__)


class ClientManagerImpl(IClientManager):
    """Реализация менеджера клиентов"""
    
    def __init__(self, event_bus: EventBus, max_clients: int = 4) -> None:
        self._clients: Dict[str, ClientInfo] = {}
        self._event_bus = event_bus
        self._max_clients = max_clients
        self._lock = asyncio.Lock()
        
        logger.info(f"ClientManager initialized with max_clients={max_clients}")
    
    async def add_client(self, client_info: ClientInfo) -> bool:
        """Добавление нового клиента"""
        async with self._lock:
            # Проверяем лимит клиентов
            if len(self._clients) >= self._max_clients:
                logger.warning(f"Cannot add client {client_info.client_id}: max clients reached")
                return False
            
            # Проверяем, что клиент еще не подключен
            if client_info.client_id in self._clients:
                logger.warning(f"Client {client_info.client_id} already connected")
                return False
            
            # Добавляем клиента
            client_info.connected_at = time.time()
            client_info.status = ClientStatus.CONNECTED
            self._clients[client_info.client_id] = client_info
            
            logger.info(f"Client connected: {client_info.client_id} from {client_info.ip_address}")
            logger.info(f"Client profile_name: {getattr(client_info, 'profile_name', 'NOT SET')}")
            logger.info(f"Client full info: {client_info}")
            
            # Отправляем событие
            await self._event_bus.emit_client("client_connected", client_info)
            
            return True
    
    async def remove_client(self, client_id: str) -> bool:
        """Удаление клиента"""
        async with self._lock:
            if client_id not in self._clients:
                logger.warning(f"Cannot remove client {client_id}: not found")
                return False
            
            client_info = self._clients[client_id]
            client_info.status = ClientStatus.DISCONNECTED
            
            # Отправляем событие перед удалением
            await self._event_bus.emit_client("client_disconnected", client_info)
            
            del self._clients[client_id]
            
            logger.info(f"Client {client_id} removed from {client_info.ip_address}")
            return True
    
    async def get_clients(self) -> List[ClientInfo]:
        """Получение списка всех клиентов"""
        async with self._lock:
            return list(self._clients.values())
    
    async def get_client(self, client_id: str) -> Optional[ClientInfo]:
        """Получение информации о конкретном клиенте"""
        async with self._lock:
            return self._clients.get(client_id)
    
    async def update_client_status(self, client_id: str, status: ClientStatus) -> bool:
        """Обновление статуса клиента"""
        async with self._lock:
            if client_id not in self._clients:
                return False
            
            old_status = self._clients[client_id].status
            self._clients[client_id].status = status
            
            if old_status != status:
                logger.debug(f"Client {client_id} status changed: {old_status} -> {status}")
                await self._event_bus.emit_client("client_status_changed", self._clients[client_id])
            
            return True
    
    async def assign_gamepad(self, client_id: str, gamepad_id: int) -> bool:
        """Привязка геймпада к клиенту"""
        async with self._lock:
            if client_id not in self._clients:
                return False
            
            self._clients[client_id].gamepad_id = gamepad_id
            logger.info(f"Client {client_id} assigned to gamepad {gamepad_id}")
            
            await self._event_bus.emit_client("client_gamepad_assigned", self._clients[client_id])
            return True
    
    async def update_client_profile(self, client_id: str, profile_name: str) -> bool:
        """Обновление профиля клиента"""
        async with self._lock:
            if client_id not in self._clients:
                logger.warning(f"Cannot update profile: client {client_id} not found")
                return False
            
            old_name = getattr(self._clients[client_id], 'profile_name', None)
            self._clients[client_id].profile_name = profile_name
            
            logger.info(f"Profile updated for client {client_id}: {old_name} -> {profile_name}")
            
            if old_name != profile_name:
                logger.info(f"Client {client_id} profile name changed: {old_name} -> {profile_name}")
                await self._event_bus.emit_client("client_profile_updated", self._clients[client_id])
            
            return True
    
    async def get_client_count(self) -> int:
        """Получение количества подключенных клиентов"""
        async with self._lock:
            return len(self._clients)
    
    async def get_clients_by_status(self, status: ClientStatus) -> List[ClientInfo]:
        """Получение клиентов по статусу"""
        async with self._lock:
            return [client for client in self._clients.values() if client.status == status]
    
    async def cleanup_inactive_clients(self, timeout_seconds: int = 300) -> int:
        """Очистка неактивных клиентов"""
        current_time = time.time()
        removed_count = 0
        
        async with self._lock:
            inactive_clients = []
            
            for client_info in self._clients.values():
                if (current_time - client_info.connected_at) > timeout_seconds:
                    if client_info.status in [ClientStatus.DISCONNECTED, ClientStatus.ERROR]:
                        inactive_clients.append(client_info.client_id)
            
            for client_id in inactive_clients:
                if await self.remove_client(client_id):
                    removed_count += 1
        
        if removed_count > 0:
            logger.info(f"Cleaned up {removed_count} inactive clients")
        
        return removed_count
    
    async def cleanup_all_clients(self) -> int:
        """Очистка всех клиентов (при остановке сервера)"""
        async with self._lock:
            client_count = len(self._clients)
            self._clients.clear()
            logger.info(f"All {client_count} clients removed")
            return client_count
    
    async def generate_client_id(self, ip_address: str) -> str:
        """Генерация уникального ID для клиента"""
        # Простая генерация ID на основе UUID
        base_id = str(uuid4())[:8]
        
        # Проверяем уникальность
        async with self._lock:
            while base_id in self._clients:
                base_id = str(uuid4())[:8]
        
        return f"client_{base_id}"
    
    def get_stats(self) -> Dict[str, int]:
        """Получение статистики клиентов"""
        stats = {
            "total": len(self._clients),
            "connected": 0,
            "active": 0,
            "disconnected": 0,
            "error": 0
        }
        
        for client in self._clients.values():
            if client.status == ClientStatus.CONNECTED:
                stats["connected"] += 1
            elif client.status == ClientStatus.ACTIVE:
                stats["active"] += 1
            elif client.status == ClientStatus.DISCONNECTED:
                stats["disconnected"] += 1
            elif client.status == ClientStatus.ERROR:
                stats["error"] += 1
        
        return stats