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
    fetch('/gamepad_data', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    }).then(response => {
        return response.json();
    }).then(result => {
        console.log('Response from server:', result);
        // После отправки данных снова проверяем состояние
        updateJoystickData(data)
        checkForChanges();
    }).catch(error => {
        console.error('Error:', error);
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

// Переключение темы
const themeToggle = document.getElementById('theme-toggle');
const body = document.body;

themeToggle.addEventListener('click', () => {
    body.classList.toggle('light-theme');
    body.classList.toggle('dark-theme');
});

// Сохранение ника пользователя
const nicknameInput = document.getElementById('nickname-input');
const nicknameDisplay = document.getElementById('nickname-display');
const saveNicknameButton = document.getElementById('save-nickname');

saveNicknameButton.addEventListener('click', () => {
    const nickname = nicknameInput.value.trim();
    if (nickname) {
        localStorage.setItem('nickname', nickname);  // Сохраняем ник в локальное хранилище
        nicknameDisplay.textContent = nickname;
        M.toast({html: 'Ник сохранён!'});
    }
});

// Загрузка ника из localStorage при загрузке страницы
window.addEventListener('load', () => {
    const savedNickname = localStorage.getItem('nickname');
    if (savedNickname) {
        nicknameDisplay.textContent = savedNickname;
    }
});

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
        li.textContent = `${button.name} ${button.pressed ? 'нажата' : 'отпущена'} (${button.value.toFixed(2)})`;
        buttonsList.appendChild(li);
    });
}


// Запускаем цикл обновления
requestAnimationFrame(update);

