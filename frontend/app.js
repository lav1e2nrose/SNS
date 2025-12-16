// SNS Chat Application Frontend
// Modern and feature-rich chat application with sentiment analysis

const API_BASE = window.location.origin + '/api/v1';
let token = null;
let currentUserId = null;
let currentFriendId = null;
let currentFriendName = null;
let ws = null;
let wordCloudData = [];
let analysisData = null;

// ECharts instances
let wordcloudChart = null;
let radarChart = null;

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
    
    // Initialize charts when modal opens
    window.addEventListener('resize', () => {
        if (wordcloudChart) wordcloudChart.resize();
        if (radarChart) radarChart.resize();
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
    currentFriendName = null;
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
            // Fetch unread counts for each friend
            const friendsWithUnread = await Promise.all(
                friends.map(async (friend) => {
                    try {
                        const unreadResponse = await fetch(`${API_BASE}/chat/${friend.id}/unread`, {
                            headers: {
                                'Authorization': `Bearer ${token}`
                            }
                        });
                        if (unreadResponse.ok) {
                            const unreadData = await unreadResponse.json();
                            return { ...friend, unread_count: unreadData.unread_count };
                        }
                    } catch (e) {
                        console.error('Failed to get unread count:', e);
                    }
                    return { ...friend, unread_count: 0 };
                })
            );
            renderFriendsList(friendsWithUnread);
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
        container.innerHTML = `
            <div class="empty-state" style="padding: 20px; text-align: center;">
                <i class="fas fa-user-friends" style="font-size: 32px; opacity: 0.3; margin-bottom: 8px;"></i>
                <p style="color: var(--text-muted); font-size: 12px;">暂无好友</p>
            </div>
        `;
        return;
    }
    
    friends.forEach(friend => {
        const div = document.createElement('div');
        div.className = 'friend-item';
        if (friend.id === currentFriendId) {
            div.classList.add('active');
        }
        
        // Build unread badge HTML if there are unread messages
        const unreadBadge = friend.unread_count > 0 
            ? `<span class="unread-badge">${friend.unread_count}</span>` 
            : '';
        
        // Get first character of username for avatar
        const avatarChar = friend.username.charAt(0).toUpperCase();
        
        div.innerHTML = `
            <div class="friend-info">
                <div class="friend-avatar">${avatarChar}</div>
                <div>
                    <div class="username">${escapeHtml(friend.username)}</div>
                    <div class="status">${friend.status === 'accepted' ? '已接受' : friend.status === 'pending' ? '待确认' : friend.status}</div>
                </div>
            </div>
            ${unreadBadge}
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
    currentFriendName = username;
    
    // Get first character of username for avatar
    const avatarChar = username.charAt(0).toUpperCase();
    
    // Update UI
    document.getElementById('chat-header').innerHTML = `
        <div class="chat-header-info">
            <div class="chat-avatar">${avatarChar}</div>
            <div class="chat-header-text">
                <h3>与 ${escapeHtml(username)} 聊天</h3>
                <span class="chat-status online">在线</span>
            </div>
        </div>
        <div class="chat-header-actions">
            <button class="btn-icon" onclick="openVisualization()" title="查看词云和雷达图" id="viz-btn">
                <i class="fas fa-chart-pie"></i>
            </button>
        </div>
    `;
    document.getElementById('message-input').disabled = false;
    document.getElementById('send-btn').disabled = false;
    
    // Update active friend
    const friends = document.querySelectorAll('.friend-item');
    friends.forEach(f => f.classList.remove('active'));
    if (event && event.currentTarget) {
        event.currentTarget.classList.add('active');
    }
    
    // Load chat history
    await loadChatHistory(friendId);
    
    // Mark messages as read
    await markAsRead(friendId);
    
    // Reload friends to update unread counts
    loadFriends();
    
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
    
    if (messages.length === 0) {
        container.innerHTML = `
            <div class="messages-empty">
                <i class="fas fa-comments"></i>
                <p>开始你们的对话吧！</p>
            </div>
        `;
        return;
    }
    
    messages.forEach(msg => {
        appendMessage(msg);
    });
    
    // Scroll to bottom
    container.scrollTop = container.scrollHeight;
}

// Append a single message
function appendMessage(msg) {
    const container = document.getElementById('messages');
    
    // Remove empty state if exists
    const emptyState = container.querySelector('.messages-empty');
    if (emptyState) {
        emptyState.remove();
    }
    
    const div = document.createElement('div');
    const isSent = msg.sender_id === currentUserId;
    div.className = `message-item ${isSent ? 'sent' : 'received'}`;
    
    const time = new Date(msg.created_at).toLocaleTimeString('zh-CN', {
        hour: '2-digit',
        minute: '2-digit'
    });
    
    let readStatus = '';
    if (isSent) {
        readStatus = `<span class="read-status"><i class="fas fa-${msg.is_read ? 'check-double' : 'check'}"></i> ${msg.is_read ? '已读' : '未读'}</span>`;
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
    
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${wsProtocol}//${window.location.host}/api/v1/ws/${friendId}?token=${token}`;
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
                top_n: 50
            })
        });
        
        if (wordCloudResponse.ok) {
            wordCloudData = await wordCloudResponse.json();
            renderWordCloud(wordCloudData);
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
            analysisData = await intimacyResponse.json();
            
            // Update score circle
            const scoreCircle = document.getElementById('intimacy-score');
            scoreCircle.innerHTML = `
                <span class="score-value">${analysisData.intimacy_score.toFixed(1)}</span>
                <span class="score-label">分</span>
            `;
            
            document.getElementById('sentiment-factor').textContent = analysisData.sentiment_factor.toFixed(1);
            document.getElementById('frequency-factor').textContent = analysisData.frequency_factor.toFixed(1);
        }
        
    } catch (err) {
        console.error('Analysis failed:', err);
        alert('分析失败，请重试');
    }
}

// Render word cloud (simple version for panel)
function renderWordCloud(words) {
    const container = document.getElementById('word-cloud');
    container.innerHTML = '';
    
    if (!words || words.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-cloud"></i>
                <span>暂无数据</span>
            </div>
        `;
        return;
    }
    
    const maxFreq = Math.max(...words.map(w => w.frequency));
    const displayWords = words.slice(0, 15); // Show top 15 in panel
    
    displayWords.forEach(word => {
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
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-crown"></i>
                <span>暂无排行数据</span>
            </div>
        `;
        return;
    }
    
    rankings.forEach((friend, index) => {
        const div = document.createElement('div');
        div.className = 'ranking-item';
        div.innerHTML = `
            <span class="rank">${index + 1}</span>
            <span class="name">${escapeHtml(friend.username)}</span>
            <span class="score">${friend.intimacy_score.toFixed(1)}</span>
        `;
        container.appendChild(div);
    });
}

// ===============================================
// Visualization Modal Functions
// ===============================================

function openVisualization() {
    if (!currentFriendId) {
        alert('请先选择一个好友');
        return;
    }
    
    const modal = document.getElementById('viz-modal');
    modal.classList.remove('hidden');
    
    // Initialize charts
    setTimeout(() => {
        initWordcloudChart();
        initRadarChart();
        
        // Refresh data if available
        if (wordCloudData.length > 0) {
            updateWordcloudChart();
        } else {
            refreshVisualization();
        }
        if (analysisData) {
            updateRadarChart();
        }
    }, 100);
}

function closeVisualization() {
    const modal = document.getElementById('viz-modal');
    modal.classList.add('hidden');
}

function switchVizTab(tab) {
    const tabs = document.querySelectorAll('.viz-tab');
    const wordcloudPanel = document.getElementById('viz-wordcloud');
    const radarPanel = document.getElementById('viz-radar');
    
    tabs.forEach(t => t.classList.remove('active'));
    
    if (tab === 'wordcloud') {
        tabs[0].classList.add('active');
        wordcloudPanel.classList.remove('hidden');
        radarPanel.classList.add('hidden');
        if (wordcloudChart) wordcloudChart.resize();
    } else {
        tabs[1].classList.add('active');
        wordcloudPanel.classList.add('hidden');
        radarPanel.classList.remove('hidden');
        if (radarChart) radarChart.resize();
    }
}

async function refreshVisualization() {
    await analyzeChat();
    updateWordcloudChart();
    updateRadarChart();
}

// Initialize ECharts Word Cloud
function initWordcloudChart() {
    const chartDom = document.getElementById('wordcloud-chart');
    if (!chartDom) return;
    
    if (wordcloudChart) {
        wordcloudChart.dispose();
    }
    
    wordcloudChart = echarts.init(chartDom, 'dark');
    
    // Set initial empty state
    const option = {
        backgroundColor: 'transparent',
        title: {
            text: '词语云图',
            left: 'center',
            textStyle: {
                color: '#f8fafc',
                fontSize: 18,
                fontWeight: 600
            }
        },
        series: [{
            type: 'wordCloud',
            shape: 'circle',
            left: 'center',
            top: 'center',
            width: '90%',
            height: '80%',
            sizeRange: [14, 60],
            rotationRange: [-45, 45],
            rotationStep: 15,
            gridSize: 8,
            drawOutOfBound: false,
            textStyle: {
                fontFamily: 'Inter, Noto Sans SC, sans-serif',
                fontWeight: 'bold',
                color: function () {
                    const colors = ['#6366f1', '#8b5cf6', '#10b981', '#f59e0b', '#ef4444', '#3b82f6', '#ec4899', '#14b8a6'];
                    return colors[Math.floor(Math.random() * colors.length)];
                }
            },
            emphasis: {
                focus: 'self',
                textStyle: {
                    textShadowBlur: 10,
                    textShadowColor: '#333'
                }
            },
            data: []
        }]
    };
    
    wordcloudChart.setOption(option);
}

// Update Word Cloud Chart with data
function updateWordcloudChart() {
    if (!wordcloudChart || !wordCloudData.length) return;
    
    const data = wordCloudData.map(item => ({
        name: item.word,
        value: item.frequency
    }));
    
    wordcloudChart.setOption({
        series: [{
            data: data
        }]
    });
}

// Initialize Radar Chart
function initRadarChart() {
    const chartDom = document.getElementById('radar-chart');
    if (!chartDom) return;
    
    if (radarChart) {
        radarChart.dispose();
    }
    
    radarChart = echarts.init(chartDom, 'dark');
    
    const option = {
        backgroundColor: 'transparent',
        title: {
            text: '亲密度雷达图',
            left: 'center',
            textStyle: {
                color: '#f8fafc',
                fontSize: 18,
                fontWeight: 600
            }
        },
        legend: {
            data: ['亲密度分析'],
            bottom: 20,
            textStyle: {
                color: '#94a3b8'
            }
        },
        radar: {
            indicator: [
                { name: '情感因素', max: 40 },
                { name: '互动频率', max: 30 },
                { name: '对话流畅', max: 20 },
                { name: '消息均衡', max: 10 }
            ],
            center: ['50%', '55%'],
            radius: '65%',
            axisName: {
                color: '#94a3b8',
                fontSize: 12
            },
            splitArea: {
                areaStyle: {
                    color: ['rgba(99, 102, 241, 0.1)', 'rgba(99, 102, 241, 0.05)'],
                    shadowColor: 'rgba(0, 0, 0, 0.2)',
                    shadowBlur: 10
                }
            },
            axisLine: {
                lineStyle: {
                    color: 'rgba(255, 255, 255, 0.1)'
                }
            },
            splitLine: {
                lineStyle: {
                    color: 'rgba(255, 255, 255, 0.1)'
                }
            }
        },
        series: [{
            name: '亲密度分析',
            type: 'radar',
            data: [{
                value: [0, 0, 0, 0],
                name: '亲密度分析',
                areaStyle: {
                    color: {
                        type: 'radial',
                        x: 0.5,
                        y: 0.5,
                        r: 0.5,
                        colorStops: [
                            { offset: 0, color: 'rgba(99, 102, 241, 0.8)' },
                            { offset: 1, color: 'rgba(139, 92, 246, 0.3)' }
                        ]
                    }
                },
                lineStyle: {
                    color: '#6366f1',
                    width: 2
                },
                itemStyle: {
                    color: '#6366f1'
                }
            }]
        }]
    };
    
    radarChart.setOption(option);
}

// Update Radar Chart with data
function updateRadarChart() {
    if (!radarChart || !analysisData) return;
    
    radarChart.setOption({
        series: [{
            data: [{
                value: [
                    analysisData.sentiment_factor,
                    analysisData.frequency_factor,
                    analysisData.flow_factor,
                    analysisData.consecutive_factor
                ],
                name: '亲密度分析'
            }]
        }]
    });
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
