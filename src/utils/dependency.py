"""
Dependency Injection контейнер
"""
from typing import Dict, Any, TypeVar, Type, Optional, Callable
import inspect

T = TypeVar('T')


class DIContainer:
    """Простой DI контейнер для инъекции зависимостей"""
    
    def __init__(self) -> None:
        self._services: Dict[str, Any] = {}
        self._factories: Dict[str, Callable[[], Any]] = {}
        self._singletons: Dict[str, Any] = {}
    
    def register_singleton(self, interface: Type[T], implementation: T) -> None:
        """Регистрация singleton сервиса"""
        key = self._get_key(interface)
        self._singletons[key] = implementation
    
    def register_factory(self, interface: Type[T], factory: Callable[[], T]) -> None:
        """Регистрация factory для создания сервисов"""
        key = self._get_key(interface)
        self._factories[key] = factory
    
    def register_instance(self, interface: Type[T], instance: T) -> None:
        """Регистрация конкретного экземпляра"""
        key = self._get_key(interface)
        self._services[key] = instance
    
    def resolve(self, interface: Type[T]) -> T:
        """Получение сервиса по интерфейсу"""
        key = self._get_key(interface)
        
        # Проверяем singleton
        if key in self._singletons:
            return self._singletons[key]
        
        # Проверяем зарегистрированные экземпляры
        if key in self._services:
            return self._services[key]
        
        # Создаем через factory
        if key in self._factories:
            return self._factories[key]()
        
        raise ValueError(f"Service {interface.__name__} not registered")
    
    def get_optional(self, interface: Type[T]) -> Optional[T]:
        """Получение сервиса с возможностью None"""
        try:
            return self.resolve(interface)
        except ValueError:
            return None
    
    @staticmethod
    def _get_key(interface: Type) -> str:
        """Получение ключа для интерфейса"""
        return f"{interface.__module__}.{interface.__name__}"


# Глобальный контейнер
container = DIContainer()


def inject(interface: Type[T]) -> T:
    """Хелпер для инъекции зависимостей"""
    return container.resolve(interface)


def register_singleton(interface: Type[T]) -> Callable[[T], T]:
    """Декоратор для регистрации singleton"""
    def decorator(implementation: T) -> T:
        container.register_singleton(interface, implementation)
        return implementation
    return decorator


def auto_inject(func: Callable) -> Callable:
    """
    Декоратор для автоматической инъекции зависимостей в функцию
    Анализирует type hints и инжектит соответствующие сервисы
    """
    sig = inspect.signature(func)
    
    async def wrapper(*args, **kwargs):
        # Получаем параметры функции с их типами
        bound_args = sig.bind_partial(*args, **kwargs)
        
        for param_name, param in sig.parameters.items():
            if param_name not in bound_args.arguments and param.annotation != inspect.Parameter.empty:
                # Пытаемся инжектить зависимость
                try:
                    service = container.resolve(param.annotation)
                    bound_args.arguments[param_name] = service
                except ValueError:
                    # Если сервис не найден и нет default значения, пропускаем
                    if param.default == inspect.Parameter.empty:
                        continue
        
        if inspect.iscoroutinefunction(func):
            return await func(*bound_args.args, **bound_args.kwargs)
        else:
            return func(*bound_args.args, **bound_args.kwargs)
    
    return wrapper