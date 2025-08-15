"""
Система событий для RemoteGamepad
"""
import asyncio
import logging
from typing import Dict, List, Set, Callable, Any
from collections import defaultdict

from ..utils.types import GamepadEvent, ClientInfo, EventCallback, ClientCallback

logger = logging.getLogger(__name__)


class EventBus:
    """Асинхронная шина событий"""
    
    def __init__(self) -> None:
        self._gamepad_handlers: Dict[str, Set[EventCallback]] = defaultdict(set)
        self._client_handlers: Dict[str, Set[ClientCallback]] = defaultdict(set)
        self._global_handlers: Set[Callable[[str, Any], asyncio.Task[None]]] = set()
        self._running: bool = True
    
    def subscribe_gamepad(self, event_type: str, handler: EventCallback) -> None:
        """Подписка на события геймпада"""
        self._gamepad_handlers[event_type].add(handler)
        logger.debug(f"Subscribed to gamepad event: {event_type}")
    
    def subscribe_client(self, event_type: str, handler: ClientCallback) -> None:
        """Подписка на события клиентов"""
        self._client_handlers[event_type].add(handler)
        logger.debug(f"Subscribed to client event: {event_type}")
    
    def subscribe_all(self, handler: Callable[[str, Any], asyncio.Task[None]]) -> None:
        """Подписка на все события"""
        self._global_handlers.add(handler)
        logger.debug("Subscribed to all events")
    
    def unsubscribe_gamepad(self, event_type: str, handler: EventCallback) -> None:
        """Отписка от событий геймпада"""
        self._gamepad_handlers[event_type].discard(handler)
    
    def unsubscribe_client(self, event_type: str, handler: ClientCallback) -> None:
        """Отписка от событий клиентов"""
        self._client_handlers[event_type].discard(handler)
    
    def unsubscribe_all(self, handler: Callable[[str, Any], asyncio.Task[None]]) -> None:
        """Отписка от всех событий"""
        self._global_handlers.discard(handler)
    
    async def emit_gamepad(self, event_type: str, event: GamepadEvent) -> None:
        """Отправка события геймпада"""
        if not self._running:
            return
        
        # Вызываем специфичные обработчики
        handlers = self._gamepad_handlers.get(event_type, set())
        tasks = [self._safe_call_gamepad(handler, event) for handler in handlers]
        
        # Вызываем глобальные обработчики
        global_tasks = [self._safe_call_global(handler, event_type, event) 
                       for handler in self._global_handlers]
        
        if tasks or global_tasks:
            await asyncio.gather(*tasks, *global_tasks, return_exceptions=True)
    
    async def emit_client(self, event_type: str, client: ClientInfo) -> None:
        """Отправка события клиента"""
        if not self._running:
            return
        
        # Вызываем специфичные обработчики
        handlers = self._client_handlers.get(event_type, set())
        tasks = [self._safe_call_client(handler, client) for handler in handlers]
        
        # Вызываем глобальные обработчики
        global_tasks = [self._safe_call_global(handler, event_type, client)
                       for handler in self._global_handlers]
        
        if tasks or global_tasks:
            await asyncio.gather(*tasks, *global_tasks, return_exceptions=True)
    
    async def _safe_call_gamepad(self, handler: EventCallback, event: GamepadEvent) -> None:
        """Безопасный вызов обработчика события геймпада"""
        try:
            await handler(event)
        except Exception as e:
            logger.error(f"Error in gamepad event handler: {e}", exc_info=True)
    
    async def _safe_call_client(self, handler: ClientCallback, client: ClientInfo) -> None:
        """Безопасный вызов обработчика события клиента"""
        try:
            await handler(client)
        except Exception as e:
            logger.error(f"Error in client event handler: {e}", exc_info=True)
    
    async def _safe_call_global(self, handler: Callable, event_type: str, data: Any) -> None:
        """Безопасный вызов глобального обработчика"""
        try:
            await handler(event_type, data)
        except Exception as e:
            logger.error(f"Error in global event handler: {e}", exc_info=True)
    
    def stop(self) -> None:
        """Остановка шины событий"""
        self._running = False
        logger.info("EventBus stopped")
    
    def start(self) -> None:
        """Запуск шины событий"""
        self._running = True
        logger.info("EventBus started")
    
    @property
    def is_running(self) -> bool:
        """Проверка, запущена ли шина событий"""
        return self._running


# Декоратор для подписки на события
def on_gamepad_event(event_type: str, event_bus: EventBus):
    """Декоратор для автоматической подписки на события геймпада"""
    def decorator(func: EventCallback) -> EventCallback:
        event_bus.subscribe_gamepad(event_type, func)
        return func
    return decorator


def on_client_event(event_type: str, event_bus: EventBus):
    """Декоратор для автоматической подписки на события клиентов"""
    def decorator(func: ClientCallback) -> ClientCallback:
        event_bus.subscribe_client(event_type, func)
        return func
    return decorator