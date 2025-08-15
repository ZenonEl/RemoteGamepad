# Настройка RemoteGamepad на Arch Linux

## Быстрый старт

1. **Установка зависимостей:**
   ```bash
   # Установка Python и pip (если еще не установлены)
   sudo pacman -S python python-pip
   
   # Создание виртуального окружения
   python -m venv venv
   source venv/bin/activate
   
   # Установка зависимостей проекта
   pip install -r requirements.txt
   ```

2. **Настройка прав доступа для evdev:**
   
   Для работы с устройствами ввода ваш пользователь должен быть в группе `input`:
   ```bash
   # Добавление пользователя в группу input
   sudo usermod -a -G input $USER
   
   # Перелогинивайтесь или выполните:
   newgrp input
   ```

3. **Запуск приложения:**
   ```bash
   # Активация venv для fish shell
   # ВАЖНО: Для fish используйте прямой путь к python:
   venv/bin/python main.py
   
   # Или напрямую через server.py:
   venv/bin/python server.py
   
   # Для bash/zsh можно использовать:
   # source venv/bin/activate
   # python main.py
   ```

## Проверка совместимости

### Тестирование evdev:
```bash
python -c "import evdev; print('evdev работает!')"
```

### Проверка доступа к устройствам:
```bash
ls -la /dev/input/
# Устройства должны иметь права чтения для группы input
```

### Список доступных устройств:
```python
import evdev
devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
for device in devices:
    print(f"{device.path}: {device.name}")
```

## Возможные проблемы

### 1. ImportError: cannot import name 'url_decode' from 'werkzeug.urls'
**Решение:** Обновлены зависимости в requirements.txt, конфликт версий исправлен.

### 2. Permission denied при доступе к /dev/input/
**Решение:** Добавьте пользователя в группу `input` (см. выше).

### 3. Проблемы с Python 3.13
Все зависимости совместимы с Python 3.13. Если возникают проблемы:
- Убедитесь что используете последние версии пакетов
- Проверьте что система обновлена: `sudo pacman -Syu`

## Дополнительная информация

- **Порт по умолчанию:** 5002
- **IP по умолчанию:** 0.0.0.0 (все интерфейсы)
- **Конфигурация:** config/default_settings.py

## Arch Linux специфичные пакеты

Если нужны дополнительные возможности:
```bash
# Для разработки
sudo pacman -S base-devel

# Для GUI (если планируете использовать flet)
sudo pacman -S gtk3
```