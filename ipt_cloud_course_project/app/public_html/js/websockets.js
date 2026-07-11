// websockets.js — Enhanced with session-aware reconnection & user tracking

const senderColors = {};
const predefinedColors = [
    '#FF5733', '#FFC300', '#00AF91', '#00ADB5', '#FFD700', '#FF8C00', '#9932CC', '#FF4500',
    '#48D1CC', '#FF1493', '#1E90FF', '#FF69B4', '#DC143C', '#00FF7F', '#6B8E23', '#B22222'
];

function getColor(senderId) {
    if (!senderColors[senderId]) {
        const colorIndex = parseInt(senderId) % predefinedColors.length;
        senderColors[senderId] = predefinedColors[colorIndex];
    }
    return senderColors[senderId];
}

// DOM elements
const messageForm = document.getElementById('messageForm');
const messageInput = document.getElementById('messageInput');
const statusDiv = document.getElementById('statusDiv');
const notificationDiv = document.getElementById('notificationDiv');
const onlineCountSpan = document.getElementById('onlineCount');

let socket = null;
let reconnectAttempts = 0;
const maxReconnectDelay = 30000;

// ─── WebSocket Connection (with user_id in query string) ───
function connectWebSocket() {
    const wsUrl = ws_uri + '?user_id=' + encodeURIComponent(typeof user_id !== 'undefined' ? user_id : 'anon');

    socket = new WebSocket(wsUrl);

    socket.onopen = function() {
        console.log('WebSocket connected');
        reconnectAttempts = 0;
        statusDiv.classList.remove('alert-warning', 'alert-danger');
        statusDiv.classList.add('alert-success');
        statusDiv.innerHTML = '🟢 Connected to WebSocket server.' + statusDiv.querySelector('.btn-close').outerHTML;
    };

    socket.onmessage = function(event) {
        const data = JSON.parse(event.data);

        // System messages (user joined/left, online count, connected)
        if (data.type === 'system') {
            if (data.event === 'connected') {
                return; // already handled by onopen
            }
            const sysMsg = document.createElement('div');
            sysMsg.className = 'alert alert-info alert-dismissible fade show py-1';
            sysMsg.innerHTML = (data.event === 'user_joined' ? '👤 ' : '👋 ') +
                '<strong>' + data.user_id + '</strong> ' +
                (data.event === 'user_joined' ? 'joined' : 'left') +
                ' · Online: ' + data.online_count +
                '<button type="button" class="btn-close btn-sm" data-bs-dismiss="alert"></button>';
            notificationDiv.appendChild(sysMsg);
            if (data.online_count !== undefined && onlineCountSpan) {
                onlineCountSpan.textContent = data.online_count;
            }
            return;
        }

        // Regular chat message
        const msgDiv = document.createElement('div');
        const messageSpan = document.createElement('span');
        messageSpan.innerText = data.message;
        const timestampSpan = document.createElement('span');
        timestampSpan.innerText = ' (' + data.timestamp + ')';
        const senderSpan = document.createElement('span');
        const senderLabel = data.sender_user_id || ('Sender ' + data.sender_resourceId);
        senderSpan.innerText = ' by ' + senderLabel;

        messageSpan.classList.add('message-text');
        timestampSpan.classList.add('timestamp');
        senderSpan.classList.add('sender-id');
        msgDiv.appendChild(messageSpan);
        msgDiv.appendChild(timestampSpan);
        msgDiv.appendChild(senderSpan);

        const senderKey = data.sender_user_id || data.sender_resourceId;
        msgDiv.classList.add('notification', 'recipient-message');
        msgDiv.style.backgroundColor = getColor(senderKey);
        notificationDiv.appendChild(msgDiv);
        notificationDiv.scrollTop = notificationDiv.scrollHeight;
    };

    socket.onclose = function() {
        console.log('WebSocket disconnected');
        statusDiv.classList.remove('alert-success', 'alert-warning');
        statusDiv.classList.add('alert-danger');
        statusDiv.innerHTML = '🔴 Disconnected. Reconnecting...' + statusDiv.querySelector('.btn-close').outerHTML;

        const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), maxReconnectDelay);
        reconnectAttempts++;
        setTimeout(connectWebSocket, delay);
    };

    socket.onerror = function(error) {
        console.error('WebSocket error:', error);
    };
}

// ─── Send Message ───
function sendMessage(message) {
    if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({ message: message }));
    }
}

// ─── Form handler ───
if (messageForm) {
    messageForm.addEventListener('submit', function(event) {
        event.preventDefault();
        const message = messageInput.value.trim();
        if (message) {
            sendMessage(message);
            messageInput.value = '';
        }
    });
}

// ─── Start connection ───
connectWebSocket();
