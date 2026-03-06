// WebSocket Client Logic
const buttonMap = {
    0: 'BtnA', 1: 'BtnB', 2: 'BtnX', 3: 'BtnY',
    4: 'BtnShoulderL', 5: 'BtnShoulderR',
    6: 'TriggerL', 7: 'TriggerR',
    8: 'BtnBack', 9: 'BtnStart',
    10: 'BtnThumbL', 11: 'BtnThumbR',
    12: 'Dpad_Up', 13: 'Dpad_Down', 14: 'Dpad_Left', 15: 'Dpad_Right',
    16: 'BtnMode'
};

let socket = null;
let isConnected = false;
let lastStateJSON = "";


// Инициализация WebSocket
function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws`;
    
    console.log(`🔌 Connecting to ${wsUrl}...`);
    socket = new WebSocket(wsUrl);

    socket.onopen = () => {
        console.log("✅ WebSocket Connected");
        isConnected = true;
        showStatusMessage('⚡️ Подключено к ПК', 'success');
        startLoop();
    };

    socket.onclose = () => {
        console.log("❌ WebSocket Disconnected");
        isConnected = false;
        showStatusMessage('💤 Связь потеряна. Реконнект...', 'error');
        setTimeout(connectWebSocket, 3000); // Реконнект через 3 сек
    };

    socket.onerror = (err) => {
        console.error("WebSocket Error:", err);
    };
}

// Считывание данных (упрощено и оптимизировано)
function getGamepadState() {
    const gamepads = navigator.getGamepads();
    const gp = gamepads[0]; // Берем первый геймпад

    if (!gp) return null;

    // Формируем чистый объект данных (без триггеров в осях)
    const state = {
        axes: {
            left_stick: { x: gp.axes[0] || 0, y: gp.axes[1] || 0 },
            right_stick: { x: gp.axes[2] || 0, y: gp.axes[3] || 0 }
        },
        buttons: gp.buttons.map((btn, idx) => ({
            name: buttonMap[idx] || `Unknown_${idx}`,
            pressed: btn.pressed,
            value: btn.value
        }))
    };

    // НАША ХИТРОСТЬ: Если триггеры на телефоне висят на осях 4 и 5,
    // мы насильно переписываем их значения внутри массива buttons,
    // чтобы бэкенд обработал их именно там (как в старом коде).
    const tlIndex = state.buttons.findIndex(b => b.name === 'TriggerL');
    if (tlIndex !== -1 && state.buttons[tlIndex].value === 0 && gp.axes[4] !== undefined) {
        let val = gp.axes[4];
        let lt = 0;
        if (val > 0.01) lt = val;
        else if (val < -0.01 || (val > -0.99 && val < 0)) lt = (val + 1) / 2;
        
        state.buttons[tlIndex].value = lt;
        state.buttons[tlIndex].pressed = lt > 0.1;
    }

    const trIndex = state.buttons.findIndex(b => b.name === 'TriggerR');
    if (trIndex !== -1 && state.buttons[trIndex].value === 0 && gp.axes[5] !== undefined) {
        let val = gp.axes[5];
        let rt = 0;
        if (val > 0.01) rt = val;
        else if (val < -0.01 || (val > -0.99 && val < 0)) rt = (val + 1) / 2;
        
        state.buttons[trIndex].value = rt;
        state.buttons[trIndex].pressed = rt > 0.1;
    }

    return state;
}

// Главный цикл (60 FPS)
function gameLoop() {
    if (!isConnected) return;

    const state = getGamepadState();
    if (state) {
        // Оптимизация: отправляем только если данные изменились
        const stateJSON = JSON.stringify(state);
        
        if (stateJSON !== lastStateJSON) {
            socket.send(stateJSON);
            lastStateJSON = stateJSON;
            
            // Обновляем UI
            updateUI(state);
        }
    }
    
    requestAnimationFrame(gameLoop);
}

function startLoop() {
    gameLoop();
}

// Полноценный UI апдейтер
function updateUI(data) {
    try {
        // Оси
        document.getElementById('left-stick-x').textContent = data.axes.left_stick.x.toFixed(2);
        document.getElementById('left-stick-y').textContent = data.axes.left_stick.y.toFixed(2);
        document.getElementById('right-stick-x').textContent = data.axes.right_stick.x.toFixed(2);
        document.getElementById('right-stick-y').textContent = data.axes.right_stick.y.toFixed(2);

        // Кнопки и Триггеры
        const buttonsList = document.getElementById('buttons-list');
        buttonsList.innerHTML = ''; 

        // Выводим все кнопки (Триггеры теперь снова здесь)
        data.buttons.forEach(button => {
            // Если это неизвестная кнопка и она не нажата - скрываем, чтобы не мусорить UI
            if (button.name.startsWith('Unknown_') && !button.pressed) return;

            const li = document.createElement('li');
            li.innerHTML = `<strong>${button.name}:</strong> ${button.pressed ? '⚡️' : '💤'} (${button.value.toFixed(2)})`;
            buttonsList.appendChild(li);
        });
    } catch (e) {
        console.error("UI Update Error:", e);
    }
}

// Запуск при загрузке
window.addEventListener('load', () => {
    connectWebSocket();
});

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

async function handleNicknameSave() {
    const nickname = nicknameInput.value.trim();
    if (!nickname) return;
    
    localStorage.setItem('nickname', nickname);
    nicknameDisplay.textContent = nickname;
    
    // Обновляем имя на сервере
    try {
        const clientId = localStorage.getItem('client_id');
        if (clientId) {
            await fetch('/update_profile', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    client_id: clientId,
                    profile_name: nickname
                })
            });
        }
    } catch (error) {
        console.error('Error updating profile:', error);
    }
    
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

// ================== Обработка геймпада ==================
window.addEventListener('gamepadconnected', (e) => {
    console.log('🎮 Gamepad connected:', e.gamepad);
    showStatusMessage('🎮 Геймпад подключен', 'success');
});

window.addEventListener('gamepaddisconnected', (e) => {
    console.log('🎮 Gamepad disconnected:', e.gamepad);
    showStatusMessage('🎮 Геймпад отключен', 'error');
});

// ================== Обработка отключения ==================
window.addEventListener('beforeunload', async () => {
    await disconnectFromServer();
});

window.addEventListener('pagehide', async () => {
    await disconnectFromServer();
});

// Обработка потери фокуса (мобильные устройства)
document.addEventListener('visibilitychange', async () => {
    if (document.visibilityState === 'hidden') {
        await disconnectFromServer();
    }
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
                user_agent: navigator.userAgent,
                profile_name: localStorage.getItem('nickname') || 'Guest'
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

async function disconnectFromServer() {
    try {
        const clientId = localStorage.getItem('client_id');
        if (clientId) {
            await fetch('/disconnect', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    client_id: clientId
                })
            });
            localStorage.removeItem('client_id');
            console.log('Disconnected from server');
        }
    } catch (error) {
        console.error('Error disconnecting from server:', error);
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