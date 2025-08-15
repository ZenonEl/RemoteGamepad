// Сопоставление индексов кнопок с их именами
const buttonMap = {
    0: 'BtnA',
    1: 'BtnB',
    2: 'BtnX',
    3: 'BtnY',
    8: 'BtnBack',
    9: 'BtnStart',
    10: 'BtnThumbL',
    11: 'BtnThumbR',
    4: 'BtnShoulderL',
    5: 'BtnShoulderR',
    12: 'Dpad_Up',
    13: 'Dpad_Down',
    14: 'Dpad_Left',
    15: 'Dpad_Right',
    6: 'TriggerL',
    7: 'TriggerR'
};

let lastData = null;
let lastSentTime = performance.now();
const sendDelay = 50;

function getGamepadData() {
    const gamepads = navigator.getGamepads();
    if (gamepads[0]) {
        const axes = {
            left_stick: {
                x: gamepads[0].axes[0],
                y: gamepads[0].axes[1]
            },
            right_stick: {
                x: gamepads[0].axes[2],
                y: gamepads[0].axes[3]
            }
        };
        const buttons = gamepads[0].buttons.map((button, index) => ({
            name: buttonMap[index] || `Button${index}`,
            pressed: button.pressed,
            value: button.value,
            index: index
        }));
        return { type: "axis", axes: axes, buttons: buttons };
    }
    return null;
}

function sendGamepadData(data) {
    // Добавляем client_id если есть
    const clientId = localStorage.getItem('client_id') || 'web_client';
    const gamepadData = {
        ...data,
        client_id: clientId,
        timestamp: Date.now()
    };
    
    fetch('/gamepad_data', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(gamepadData)
    }).then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    }).then(result => {
        console.log('Response from server:', result);
        // После отправки данных снова проверяем состояние
        updateJoystickData(data);
        checkForChanges();
    }).catch(error => {
        console.error('Error sending gamepad data:', error);
        // Показываем ошибку пользователю
        showStatusMessage('❌ Ошибка отправки', 'error');
    });
}

function checkForChanges() {
    const data = getGamepadData();
    const now = performance.now();

    if (data) {
        // Отправляем данные, если они изменились или если прошло достаточно времени
        if (JSON.stringify(data) !== JSON.stringify(lastData) || (now - lastSentTime >= sendDelay)) {
            lastData = data; // Обновляем последнее состояние
            sendGamepadData(data); // Отправляем данные
            lastSentTime = now; // Обновляем время последней отправки
        }
    }
}

// Используем requestAnimationFrame для проверки изменений
function update() {
    checkForChanges();
    requestAnimationFrame(update);
}

// Обновление данных джойстика на странице
function updateJoystickData(data) {
    document.getElementById('left-stick-x').textContent = data.axes.left_stick.x.toFixed(2);
    document.getElementById('left-stick-y').textContent = data.axes.left_stick.y.toFixed(2);
    document.getElementById('right-stick-x').textContent = data.axes.right_stick.x.toFixed(2);
    document.getElementById('right-stick-y').textContent = data.axes.right_stick.y.toFixed(2);

    const buttonsList = document.getElementById('buttons-list');
    buttonsList.innerHTML = ''; // Очищаем список кнопок

    data.buttons.forEach(button => {
        const li = document.createElement('li');
        li.textContent = `${button.name} ${button.pressed ? '⚡️' : '💤'} (${button.value.toFixed(2)})`;
        buttonsList.appendChild(li);
    });
}

// ================== Система тем ==================
const themeToggle = document.getElementById('theme-toggle');
const body = document.body;

function saveTheme() {
    localStorage.setItem('theme', body.classList.contains('light-theme') ? 'light' : 'dark');
}

themeToggle.addEventListener('click', () => {
    body.classList.toggle('light-theme');
    body.classList.toggle('dark-theme');
    saveTheme();
});

// ================== Работа с ником ==================
const nicknameInput = document.getElementById('nickname-input');
const nicknameDisplay = document.getElementById('nickname-display');
const saveNicknameButton = document.getElementById('save-nickname');

function handleNicknameSave() {
    const nickname = nicknameInput.value.trim();
    if (!nickname) return;
    
    localStorage.setItem('nickname', nickname);
    nicknameDisplay.textContent = nickname;
    M.toast({html: 'Ник сохранён!'});
}

saveNicknameButton.addEventListener('click', handleNicknameSave);

// ================== Инициализация при загрузке ==================
window.addEventListener('load', async () => {
    // Загрузка темы
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'light') body.classList.add('light-theme');
    
    // Загрузка ника
    const savedNickname = localStorage.getItem('nickname');
    if (savedNickname) nicknameDisplay.textContent = savedNickname;
    
    // Загрузка языка
    const lang = localStorage.getItem('language') || 'ru';
    if (lang) loadTranslations(lang);
    
    // Подключаемся к серверу
    await connectToServer();
    
    // Запуск геймпада
    requestAnimationFrame(update);
});

// ================== Подключение к серверу ==================
async function connectToServer() {
    try {
        const response = await fetch('/connect', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                ip_address: window.location.hostname,
                user_agent: navigator.userAgent
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            if (data.success) {
                localStorage.setItem('client_id', data.client_id);
                console.log('Connected to server with ID:', data.client_id);
                showStatusMessage('✅ Подключен к серверу', 'success');
            } else {
                throw new Error(data.message || 'Connection failed');
            }
        } else {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
    } catch (error) {
        console.error('Error connecting to server:', error);
        showStatusMessage('❌ Ошибка подключения', 'error');
    }
}

// ================== Система переводов ==================
async function loadTranslations(lang) {
    try {
        const response = await fetch(`/lang/${lang}.json`);
        const translations = await response.json();
        
        document.querySelectorAll('[data-i18n]').forEach(el => {
            const key = el.dataset.i18n;
            if (translations[key]) el.textContent = translations[key];
        });
        
        localStorage.setItem('language', lang);
    } catch (error) {
        console.error('Ошибка загрузки переводов:', error);
    }
}

document.body.addEventListener('htmx:beforeSwap', function(evt) {
    const main = document.getElementById('translatable-content');
    main.classList.add('fade-out');
});

document.body.addEventListener('htmx:afterSwap', function(evt) {
    const main = document.getElementById('translatable-content');
    main.classList.remove('fade-out');
    main.classList.add('fade-in');

    setTimeout(() => main.classList.remove('fade-in'), 500);
});

// ================== Проверка соединения ==================
const testConnectionButton = document.getElementById('test-connection');
const connectionStatus = document.getElementById('connection-status');
const statusMessage = document.getElementById('status-message');

async function checkServerConnection() {
    try {
        const response = await fetch('/status', { method: 'GET' });
        if (response.ok) {
            const data = await response.json();
            if (data.status === 'running') {
                showStatusMessage('⚡️ Сервер работает', 'success');
            } else {
                showStatusMessage('💤 Сервер остановлен', 'error');
            }
        } else {
            showStatusMessage('💤 Сервер недоступен', 'error');
        }
    } catch (error) {
        showStatusMessage('💤 Ошибка соединения', 'error');
    }
}

function showStatusMessage(message, statusClass) {
    // Устанавливаем текст и класс для уведомления
    statusMessage.textContent = message;
    connectionStatus.className = ''; // Очищаем предыдущие классы
    connectionStatus.classList.add(statusClass, 'visible');

    // Скрываем уведомление через 3 секунды
    setTimeout(() => {
        connectionStatus.classList.remove('visible');
    }, 3000);
}

// Назначаем обработчик на кнопку Wi-Fi
testConnectionButton.addEventListener('click', checkServerConnection);

// ================== Всплывающее меню ==================
document.addEventListener('DOMContentLoaded', () => {
    const fab = document.querySelector('.fixed-action-btn');
    M.FloatingActionButton.init(fab, {});
});