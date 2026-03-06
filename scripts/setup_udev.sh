#!/bin/bash
# Скрипт настройки прав доступа для evdev (uinput) в Linux
# Выдаёт текущему пользователю права на создание виртуальных геймпадов без sudo.

echo "🎮 Настройка прав доступа для RemoteGamepad (uinput)..."

# Проверка, что скрипт запущен с правами sudo для создания файлов
if [ "$EUID" -ne 0 ]; then
  echo "⚠️ Пожалуйста, запустите скрипт через sudo: sudo bash scripts/setup_udev.sh"
  exit 1
fi

# 1. Получаем имя реального пользователя, который вызвал sudo
REAL_USER=${SUDO_USER:-$USER}

# 2. Создаем правило udev
UDEV_RULE_FILE="/etc/udev/rules.d/99-uinput-remotegamepad.rules"

echo "📝 Создаем правило udev в $UDEV_RULE_FILE..."
cat << EOF > $UDEV_RULE_FILE
# Разрешить группе 'input' доступ к uinput (создание виртуальных устройств)
KERNEL=="uinput", MODE="0660", GROUP="input"
EOF

# 3. Добавляем пользователя в группу input
echo "👥 Добавляем пользователя $REAL_USER в группу 'input'..."
usermod -aG input $REAL_USER

# 4. Применяем правила udev
echo "🔄 Перезагружаем правила udev..."
udevadm control --reload-rules
udevadm trigger

# 5. Загружаем модуль ядра, если он еще не загружен
echo "⚙️ Проверка модуля uinput..."
modprobe uinput
echo "uinput" > /etc/modules-load.d/uinput.conf

echo ""
echo "✅ Готово! Устройство /dev/uinput теперь доступно для группы input."
echo "❗️ ВАЖНО: Чтобы изменения групп применились, вам нужно ПЕРЕЗАЙТИ в систему (Log out / Log in)"
echo "Или выполните команду 'su - $REAL_USER' в текущем терминале."