// SNS Chat Application Frontend

const API_BASE = 'http://localhost:8000/api/v1';
let token = null;
let currentUserId = null;
let currentFriendId = null;
let ws = null;

// Initialize the app
document.addEventListener('DOMContentLoaded', () => {
    // Check for stored token
    token = localStorage.getItem('token');
    if (token) {
        showMainSection();
        loadFriends();
    }
    
    // Setup form handlers
    document.getElementById('login-form').addEventListener('submit', handleLogin);
    document.getElementById('register-form').addEventListener('submit', handleRegister);
    
    // Setup message input
    document.getElementById('message-input').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
});

// Tab switching
function showTab(tab) {
    const tabs = document.querySelectorAll('.tab-btn');
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');
    
    tabs.forEach(t => t.classList.remove('active'));
    
    if (tab === 'login') {
        tabs[0].classList.add('active');
        loginForm.classList.remove('hidden');
        registerForm.classList.add('hidden');
    } else {
        tabs[1].classList.add('active');
        loginForm.classList.add('hidden');
        registerForm.classList.remove('hidden');
    }
}

// Login handler
async function handleLogin(e) {
    e.preventDefault();
    const username = document.getElementById('login-username').value;
    const password = document.getElementById('login-password').value;
    
    try {
        const formData = new FormData();
        formData.append('username', username);
        formData.append('password', password);
        
        const response = await fetch(`${API_BASE}/auth/login`, {
            method: 'POST',
            body: formData
        });
        
        if (response.ok) {
            const data = await response.json();
            token = data.access_token;
            localStorage.setItem('token', token);
            
            // Decode user ID from token
            const payload = JSON.parse(atob(token.split('.')[1]));
            currentUserId = parseInt(payload.sub);
            
            showMessage('auth-message', '登录成功！', 'success');
            setTimeout(() => {
                showMainSection();
                loadFriends();
            }, 1000);
        } else {
            const error = await response.json();
            showMessage('auth-message', error.detail || '登录失败', 'error');
        }
    } catch (err) {
        showMessage('auth-message', '网络错误，请重试', 'error');
    }
}

// Register handler
async function handleRegister(e) {
    e.preventDefault();
    const username = document.getElementById('register-username').value;
    const email = document.getElementById('register-email').value;
    const password = document.getElementById('register-password').value;
    const fullName = document.getElementById('register-fullname').value;
    
    try {
        const response = await fetch(`${API_BASE}/auth/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                username,
                email,
                password,
                full_name: fullName || null
            })
        });
        
        if (response.ok) {
            showMessage('auth-message', '注册成功！请登录', 'success');
            showTab('login');
        } else {
            const error = await response.json();
            showMessage('auth-message', error.detail || '注册失败', 'error');
        }
    } catch (err) {
        showMessage('auth-message', '网络错误，请重试', 'error');
    }
}

// Show message
function showMessage(elementId, text, type) {
    const element = document.getElementById(elementId);
    element.textContent = text;
    element.className = `message ${type}`;
}

// Show main section
function showMainSection() {
    document.getElementById('auth-section').classList.add('hidden');
    document.getElementById('main-section').classList.remove('hidden');
    
    // Decode user ID from token
    if (token) {
        const payload = JSON.parse(atob(token.split('.')[1]));
        currentUserId = parseInt(payload.sub);
    }
}

// Logout
function logout() {
    token = null;
    currentUserId = null;
    currentFriendId = null;
    localStorage.removeItem('token');
    
    if (ws) {
        ws.close();
        ws = null;
    }
    
    document.getElementById('main-section').classList.add('hidden');
    document.getElementById('auth-section').classList.remove('hidden');
}

// Load friends list
async function loadFriends() {
    try {
        const response = await fetch(`${API_BASE}/friends/`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
            const friends = await response.json();
            renderFriendsList(friends);
        }
    } catch (err) {
        console.error('Failed to load friends:', err);
    }
}

// Render friends list
function renderFriendsList(friends) {
    const container = document.getElementById('friends-list');
    container.innerHTML = '';
    
    if (friends.length === 0) {
        container.innerHTML = '<p style="padding: 20px; color: #bdc3c7;">暂无好友</p>';
        return;
    }
    
    friends.forEach(friend => {
        const div = document.createElement('div');
        div.className = 'friend-item';
        if (friend.id === currentFriendId) {
            div.classList.add('active');
        }
        div.innerHTML = `
            <div>
                <div class="username">${friend.username}</div>
                <div class="status">${friend.status === 'accepted' ? '已接受' : friend.status === 'pending' ? '待确认' : friend.status}</div>
            </div>
        `;
        div.onclick = (e) => selectFriend(e, friend.id, friend.username);
        container.appendChild(div);
    });
}

// Add friend
async function addFriend() {
    const friendId = document.getElementById('add-friend-id').value;
    if (!friendId) return;
    
    try {
        const response = await fetch(`${API_BASE}/friends/`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ friend_id: parseInt(friendId) })
        });
        
        if (response.ok) {
            document.getElementById('add-friend-id').value = '';
            loadFriends();
        } else {
            const error = await response.json();
            alert(error.detail || '添加好友失败');
        }
    } catch (err) {
        alert('网络错误');
    }
}

// Select a friend to chat with
async function selectFriend(event, friendId, username) {
    currentFriendId = friendId;
    
    // Update UI
    document.getElementById('chat-header').innerHTML = `<h3>与 ${username} 聊天</h3>`;
    document.getElementById('message-input').disabled = false;
    document.getElementById('send-btn').disabled = false;
    
    // Update active friend
    const friends = document.querySelectorAll('.friend-item');
    friends.forEach(f => f.classList.remove('active'));
    event.currentTarget.classList.add('active');
    
    // Load chat history
    await loadChatHistory(friendId);
    
    // Mark messages as read
    await markAsRead(friendId);
    
    // Connect WebSocket
    connectWebSocket(friendId);
}

// Load chat history
async function loadChatHistory(friendId) {
    try {
        const response = await fetch(`${API_BASE}/chat/${friendId}`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
            const messages = await response.json();
            renderMessages(messages);
        }
    } catch (err) {
        console.error('Failed to load chat history:', err);
    }
}

// Render messages
function renderMessages(messages) {
    const container = document.getElementById('messages');
    container.innerHTML = '';
    
    messages.forEach(msg => {
        appendMessage(msg);
    });
    
    // Scroll to bottom
    container.scrollTop = container.scrollHeight;
}

// Append a single message
function appendMessage(msg) {
    const container = document.getElementById('messages');
    const div = document.createElement('div');
    const isSent = msg.sender_id === currentUserId;
    div.className = `message-item ${isSent ? 'sent' : 'received'}`;
    
    const time = new Date(msg.created_at).toLocaleTimeString('zh-CN', {
        hour: '2-digit',
        minute: '2-digit'
    });
    
    let readStatus = '';
    if (isSent) {
        readStatus = `<span class="read-status">${msg.is_read ? '已读' : '未读'}</span>`;
    }
    
    div.innerHTML = `
        <div class="content">${escapeHtml(msg.content)}</div>
        <div class="meta">${time}${readStatus}</div>
    `;
    
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
}

// Mark messages as read
async function markAsRead(friendId) {
    try {
        await fetch(`${API_BASE}/chat/${friendId}/read`, {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
    } catch (err) {
        console.error('Failed to mark as read:', err);
    }
}

// Connect WebSocket
function connectWebSocket(friendId) {
    if (ws) {
        ws.close();
    }
    
    const wsUrl = `ws://localhost:8000/api/v1/ws/${friendId}?token=${token}`;
    ws = new WebSocket(wsUrl);
    
    ws.onopen = () => {
        console.log('WebSocket connected');
    };
    
    ws.onmessage = (event) => {
        const msg = JSON.parse(event.data);
        // Avoid duplicates - only append if it's from the other user
        if (msg.sender_id !== currentUserId) {
            appendMessage(msg);
        }
    };
    
    ws.onclose = () => {
        console.log('WebSocket disconnected');
    };
    
    ws.onerror = (err) => {
        console.error('WebSocket error:', err);
    };
}

// Send message
function sendMessage() {
    const input = document.getElementById('message-input');
    const content = input.value.trim();
    
    if (!content || !ws || ws.readyState !== WebSocket.OPEN) {
        return;
    }
    
    // Send via WebSocket
    ws.send(JSON.stringify({ content }));
    
    // Append to UI immediately
    const msg = {
        sender_id: currentUserId,
        receiver_id: currentFriendId,
        content: content,
        is_read: false,
        created_at: new Date().toISOString()
    };
    appendMessage(msg);
    
    input.value = '';
}

// Analyze chat
async function analyzeChat() {
    if (!currentFriendId) {
        alert('请先选择一个好友');
        return;
    }
    
    try {
        // Get chat history
        const historyResponse = await fetch(`${API_BASE}/chat/${currentFriendId}?limit=100`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!historyResponse.ok) return;
        
        const messages = await historyResponse.json();
        
        if (messages.length === 0) {
            alert('没有足够的消息进行分析');
            return;
        }
        
        // Extract message contents for word cloud
        const messageContents = messages.map(m => m.content);
        
        // Generate word cloud
        const wordCloudResponse = await fetch(`${API_BASE}/analysis/wordcloud`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                messages: messageContents,
                top_n: 15
            })
        });
        
        if (wordCloudResponse.ok) {
            const wordCloud = await wordCloudResponse.json();
            renderWordCloud(wordCloud);
        }
        
        // Calculate intimacy score
        const sentimentScores = messages
            .filter(m => m.sentiment_score !== null)
            .map(m => m.sentiment_score);
        
        // Count consecutive messages
        const consecutiveMessages = {};
        let currentSender = null;
        let currentCount = 0;
        
        messages.forEach(msg => {
            if (msg.sender_id === currentSender) {
                currentCount++;
            } else {
                if (currentSender !== null) {
                    consecutiveMessages[currentSender] = Math.max(
                        consecutiveMessages[currentSender] || 0,
                        currentCount
                    );
                }
                currentSender = msg.sender_id;
                currentCount = 1;
            }
        });
        if (currentSender !== null) {
            consecutiveMessages[currentSender] = Math.max(
                consecutiveMessages[currentSender] || 0,
                currentCount
            );
        }
        
        const lastMessage = messages[messages.length - 1];
        
        const intimacyResponse = await fetch(`${API_BASE}/analysis/intimacy`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                sentiment_scores: sentimentScores.length > 0 ? sentimentScores : [0],
                message_count: messages.length,
                last_sender_id: lastMessage.sender_id,
                current_user_id: currentUserId,
                consecutive_messages: consecutiveMessages
            })
        });
        
        if (intimacyResponse.ok) {
            const intimacy = await intimacyResponse.json();
            document.getElementById('intimacy-score').textContent = intimacy.intimacy_score.toFixed(1);
            document.getElementById('sentiment-factor').textContent = intimacy.sentiment_factor.toFixed(1);
            document.getElementById('frequency-factor').textContent = intimacy.frequency_factor.toFixed(1);
        }
        
    } catch (err) {
        console.error('Analysis failed:', err);
        alert('分析失败，请重试');
    }
}

// Render word cloud
function renderWordCloud(words) {
    const container = document.getElementById('word-cloud');
    container.innerHTML = '';
    
    if (words.length === 0) {
        container.innerHTML = '<span style="color: #999;">暂无数据</span>';
        return;
    }
    
    const maxFreq = Math.max(...words.map(w => w.frequency));
    
    words.forEach(word => {
        const span = document.createElement('span');
        span.className = 'word-item';
        
        const ratio = word.frequency / maxFreq;
        if (ratio > 0.7) {
            span.classList.add('freq-high');
        } else if (ratio > 0.4) {
            span.classList.add('freq-medium');
        }
        
        span.textContent = `${word.word}(${word.frequency})`;
        container.appendChild(span);
    });
}

// Load rankings
async function loadRankings() {
    try {
        const response = await fetch(`${API_BASE}/rankings/top-friends?limit=10`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
            const rankings = await response.json();
            renderRankings(rankings);
        }
    } catch (err) {
        console.error('Failed to load rankings:', err);
    }
}

// Render rankings
function renderRankings(rankings) {
    const container = document.getElementById('rankings-list');
    container.innerHTML = '';
    
    if (rankings.length === 0) {
        container.innerHTML = '<p style="padding: 10px; color: #999;">暂无排行数据</p>';
        return;
    }
    
    rankings.forEach((friend, index) => {
        const div = document.createElement('div');
        div.className = 'ranking-item';
        div.innerHTML = `
            <span class="rank">#${index + 1}</span>
            <span class="name">${friend.username}</span>
            <span class="score">${friend.intimacy_score.toFixed(1)}</span>
        `;
        container.appendChild(div);
    });
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
