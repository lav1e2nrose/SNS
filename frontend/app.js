// SNS Chat Application Frontend
// Modern and feature-rich chat application with sentiment analysis

const API_BASE = window.location.origin + '/api/v1';
const RANKING_DAYS = 7;
const FALLBACK_SENTIMENT_LIMIT = 50;
const FALLBACK_SENTIMENT_BATCH_SIZE = 5;
const MIN_TREND_BAR_HEIGHT = 6;
const MAX_TREND_HEIGHT_PERCENTAGE = 100;
const RADAR_LABEL_WRAP_THRESHOLD = 3;
const INSIGHTS_REFRESH_DELAY = 400;
const HTML_ESCAPE_MAP = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' };
let token = null;
let currentUserId = null;
let currentFriendId = null;
let currentFriendName = null;
let ws = null;
let wordCloudData = [];
let analysisData = null;
let rankingsCache = [];
let insightsRefreshTimer = null;
const EMPTY_ANALYSIS_DATA = Object.freeze({
    intimacy_score: 0,
    sentiment_factor: 0,
    frequency_factor: 0,
    flow_factor: 0,
    consecutive_factor: 0
});

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
        loadRankings();
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
                loadRankings();
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
            loadRankings();
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
    
    // Refresh insights and rankings for the selected friend
    scheduleInsightsRefresh(true);
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
            scheduleInsightsRefresh();
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
    scheduleInsightsRefresh();
}

function buildEmptyAnalysisData() {
    return { ...EMPTY_ANALYSIS_DATA };
}

function renderAnalysisSummary(data) {
    const scoreCircle = document.getElementById('intimacy-score');
    const sentimentEl = document.getElementById('sentiment-factor');
    const frequencyEl = document.getElementById('frequency-factor');
    if (!scoreCircle || !sentimentEl || !frequencyEl) return;
    
    if (!data) {
        scoreCircle.innerHTML = `
            <span class="score-value">--</span>
            <span class="score-label">分</span>
        `;
        sentimentEl.textContent = '--';
        frequencyEl.textContent = '--';
        return;
    }
    
    scoreCircle.innerHTML = `
        <span class="score-value">${Number(data.intimacy_score || 0).toFixed(1)}</span>
        <span class="score-label">分</span>
    `;
    sentimentEl.textContent = Number(data.sentiment_factor || 0).toFixed(1);
    frequencyEl.textContent = Number(data.frequency_factor || 0).toFixed(1);
}

function scheduleInsightsRefresh(immediate = false) {
    if (!currentFriendId) return;
    if (insightsRefreshTimer) {
        clearTimeout(insightsRefreshTimer);
    }
    const delay = immediate ? 0 : INSIGHTS_REFRESH_DELAY;
    insightsRefreshTimer = setTimeout(() => {
        refreshInsightsForCurrentFriend().catch(err => console.error('Refresh insights failed:', err));
    }, delay);
}

async function refreshInsightsForCurrentFriend() {
    if (!currentFriendId) return;
    await analyzeChat({ silent: true });
    if (token) {
        await loadRankings(true);
    }
}

// Analyze chat
async function analyzeChat(options = {}) {
    const { silent = false } = options;
    if (!currentFriendId) {
        if (!silent) {
            alert('请先选择一个好友');
        }
        return;
    }
    
    try {
        // Get chat history
        const historyResponse = await fetch(`${API_BASE}/chat/${currentFriendId}?limit=100`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!historyResponse.ok) {
            if (!silent) {
                alert('无法获取聊天记录');
            }
            return;
        }
        
        let messages = [];
        try {
            messages = await historyResponse.json();
        } catch (parseErr) {
            console.error('Failed to parse chat history:', parseErr);
            messages = [];
        }
        
        if (messages.length === 0) {
            wordCloudData = [];
            renderWordCloud(wordCloudData);
            updateWordcloudChart();
            analysisData = buildEmptyAnalysisData();
            renderAnalysisSummary(analysisData);
            updateRadarChart();
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
        } else {
            wordCloudData = [];
        }
        renderWordCloud(wordCloudData);
        updateWordcloudChart();
        
        // Calculate intimacy score
        let sentimentScores = messages
            .filter(m => typeof m.sentiment_score === 'number')
            .map(m => m.sentiment_score);

        // Fallback: call sentiment analysis when no stored scores are available
        if (sentimentScores.length === 0) {
            const fallbackMessages = messageContents.slice(-FALLBACK_SENTIMENT_LIMIT);
            try {
                const fallbackScores = [];
                for (let i = 0; i < fallbackMessages.length; i += FALLBACK_SENTIMENT_BATCH_SIZE) {
                    const batchMessages = fallbackMessages.slice(i, i + FALLBACK_SENTIMENT_BATCH_SIZE);
                    const batchPromises = batchMessages.map(async (text) => {
                        const trimmed = (text || '').trim();
                        if (!trimmed) return null;
                        try {
                            const response = await fetch(`${API_BASE}/analysis/sentiment`, {
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/json',
                                    'Authorization': `Bearer ${token}`
                                },
                                body: JSON.stringify({ text: trimmed })
                            });
                            if (!response.ok) {
                                console.error('Sentiment analysis fallback failed with status:', response.status);
                                return null;
                            }
                            const result = await response.json();
                            return typeof result.sentiment_score === 'number' ? result.sentiment_score : null;
                        } catch (innerError) {
                            console.error('Sentiment analysis fallback failed:', innerError);
                            return null;
                        }
                    });
                    const results = await Promise.all(batchPromises);
                    results.forEach(score => {
                        if (typeof score === 'number') {
                            fallbackScores.push(score);
                        }
                    });
                }
                sentimentScores = fallbackScores;
            } catch (error) {
                console.error('Sentiment analysis fallback failed:', error);
            }
        }
        
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
        } else {
            analysisData = buildEmptyAnalysisData();
        }
        renderAnalysisSummary(analysisData);
        updateRadarChart();
        
    } catch (err) {
        console.error('Analysis failed:', err);
        analysisData = buildEmptyAnalysisData();
        renderAnalysisSummary(analysisData);
        updateRadarChart();
        if (!silent) {
            alert('分析失败，请重试');
        }
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

// Load rankings with better UX states
async function loadRankings(silent = false, limit = 0) {
    const container = document.getElementById('rankings-list');
    const button = document.getElementById('rankings-refresh');
    
    if (!token) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-sign-in-alt"></i>
                <span>请先登录后再查看排行榜</span>
            </div>
        `;
        updateRankingsStatus('请先登录后再查看排行榜', 'error');
        return;
    }
    
    if (!silent) {
        setRankingsLoading(button, true);
        renderRankingsSkeleton(container);
    }
    updateRankingsStatus('正在刷新最新排行...', 'loading');
    
    try {
        const response = await fetch(`${API_BASE}/rankings/top-friends?limit=${limit}&days=${RANKING_DAYS}`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ detail: '加载失败' }));
            throw new Error(errorData.detail || '加载排行榜失败');
        }
        
        const rankings = await response.json();
        rankingsCache = Array.isArray(rankings) ? rankings : [];
        renderRankings(rankingsCache);
        
        const updatedAt = new Date().toLocaleTimeString('zh-CN', { hour12: false });
        updateRankingsStatus(`已更新 · ${rankingsCache.length} 位好友 · ${updatedAt}`, 'success');
    } catch (err) {
        console.error('Failed to load rankings:', err);
        if (rankingsCache.length > 0) {
            renderRankings(rankingsCache, true);
            updateRankingsStatus('网络异常，已显示缓存数据', 'error');
        } else if (!silent) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-exclamation-triangle"></i>
                    <span>${escapeHtml(err.message || '排行榜加载失败')}</span>
                </div>
            `;
            updateRankingsStatus('加载失败，请稍后重试', 'error');
        } else {
            updateRankingsStatus('排行榜加载失败', 'error');
        }
    } finally {
        if (!silent) {
            setRankingsLoading(button, false);
        }
    }
}

function setRankingsLoading(button, isLoading) {
    if (!button) return;
    button.disabled = isLoading;
    if (isLoading) {
        button.innerHTML = `<i class="fas fa-sync-alt fa-spin"></i> 刷新中...`;
    } else {
        button.innerHTML = `<i class="fas fa-sync-alt"></i> 刷新排行榜`;
    }
}

function updateRankingsStatus(text, state = 'idle') {
    const statusEl = document.getElementById('rankings-status');
    if (!statusEl) return;
    
    const labelEl = statusEl.querySelector('.status-label');
    const dotEl = statusEl.querySelector('.status-dot');
    
    if (labelEl) {
        labelEl.textContent = text;
    }
    if (dotEl) {
        dotEl.classList.remove('status-idle', 'status-loading', 'status-success', 'status-error');
        dotEl.classList.add(`status-${state}`);
    }
}

function renderRankingsSkeleton(container) {
    container.innerHTML = `
        <div class="ranking-skeleton">
            <div class="skeleton-row"></div>
            <div class="skeleton-row"></div>
            <div class="skeleton-row"></div>
        </div>
    `;
}

/**
 * Generate a compact bar sparkline HTML from trend data.
 * @param {Array<{date?: string, [key: string]: number}>} trend - ordered trend points
 * @param {string} valueKey - key to read numeric value (e.g., 'count' or 'score')
 * @returns {string} HTML string for sparkline
 */
function buildTrendSparkline(trend = [], valueKey = 'count') {
    if (!Array.isArray(trend) || trend.length === 0) {
        return '<div class="trend-sparkline empty">--</div>';
    }
    const values = trend.map(point => toNumericTrendValue(point, valueKey));
    const max = Math.max(...values);
    if (!Number.isFinite(max) || max === 0) {
        return '<div class="trend-sparkline empty">--</div>';
    }
    const bars = values.map((value, idx) => {
        const height = calculateTrendHeight(value, max);
        const label = trend[idx] && trend[idx].date ? `${trend[idx].date}` : '';
        const displayValue = formatTrendValue(value, valueKey);
        return `<div class="trend-bar" style="height:${height}%;" title="${escapeHtml(label)}：${escapeHtml(displayValue)}"></div>`;
    }).join('');
    return `<div class="trend-sparkline">${bars}</div>`;
}

function getLastTrendValue(trend = [], key, fallback = 0) {
    if (!Array.isArray(trend) || trend.length === 0) return fallback;
    const last = trend[trend.length - 1];
    const value = last && typeof last[key] !== 'undefined' ? last[key] : fallback;
    return Number.isFinite(value) ? value : fallback;
}

function calculateTrendHeight(value, max) {
    if (max <= 0) return MIN_TREND_BAR_HEIGHT;
    if (!Number.isFinite(value)) return 0;
    return Math.max(MIN_TREND_BAR_HEIGHT, Math.round((value / max) * MAX_TREND_HEIGHT_PERCENTAGE));
}

function formatTrendValue(value, valueKey) {
    if (valueKey === 'score' && Number.isFinite(value)) return value.toFixed(1);
    return value;
}

function toNumericTrendValue(point, key) {
    const raw = point && typeof point[key] !== 'undefined' ? point[key] : 0;
    return Number.isFinite(raw) ? Number(raw) : 0;
}

// Render rankings with richer details
function renderRankings(rankings, fromCache = false) {
    const container = document.getElementById('rankings-list');
    container.innerHTML = '';
    
    if (!rankings || rankings.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-crown"></i>
                <span>暂无排行数据</span>
            </div>
        `;
        return;
    }
    
    if (fromCache) {
        const cachedHint = document.createElement('div');
        cachedHint.className = 'ranking-hint';
        cachedHint.innerHTML = `<i class="fas fa-database"></i> 显示缓存数据（请稍后重试刷新）`;
        container.appendChild(cachedHint);
    }
    
    rankings.forEach((friend, index) => {
        const div = document.createElement('div');
        div.className = 'ranking-item';
        
        const activityText = friend.last_interaction
            ? formatRelativeTime(friend.last_interaction)
            : '暂无互动记录';
        const interactionCount = friend.interaction_count || 0;
        
        const positiveTotal = (friend.positive_interactions || 0) + (friend.negative_interactions || 0);
        const positiveRate = positiveTotal > 0 ? Math.round((friend.positive_interactions || 0) / positiveTotal * 100) : null;
        const scorePercent = Math.min(100, Math.max(0, Math.round(friend.intimacy_score)));
        const avatarChar = (friend.username || '?').charAt(0).toUpperCase();
        const sentimentText = positiveRate !== null ? `情感正向 ${positiveRate}%` : '暂无情感数据';
        const lastActivity = getLastTrendValue(friend.activity_trend, 'count', 0);
        const lastScore = getLastTrendValue(friend.score_trend, 'score', friend.intimacy_score);
        const activityTrendHtml = buildTrendSparkline(friend.activity_trend, 'count');
        const scoreTrendHtml = buildTrendSparkline(friend.score_trend, 'score');
        
        div.innerHTML = `
            <div class="ranking-left">
                <span class="rank ${index < 3 ? 'rank-top' : ''}">${index + 1}</span>
                <div class="ranking-avatar">${avatarChar}</div>
                <div class="name-block">
                    <div class="name">${escapeHtml(friend.username || '未命名')}</div>
                    <div class="meta">
                        <span><i class="fas fa-clock"></i> ${activityText}</span>
                        <span><i class="fas fa-comments"></i> 互动 ${interactionCount}</span>
                        <span class="${positiveRate !== null ? 'chip chip-positive' : 'chip chip-muted'}">
                            <i class="fas fa-smile"></i> ${sentimentText}
                        </span>
                    </div>
                </div>
            </div>
            <div class="ranking-right">
                <div class="score-chip">
                    <div class="score">${friend.intimacy_score.toFixed(1)}</div>
                    <div class="score-label">亲密度</div>
                </div>
                <div class="score-bar">
                    <div class="score-fill" style="width: ${scorePercent}%;"></div>
                </div>
                <div class="ranking-meta-row">
                    <span><i class="fas fa-heart"></i> ${sentimentText}</span>
                    <span><i class="fas fa-clock"></i> ${activityText}</span>
                </div>
                <div class="ranking-trends">
                    <div class="trend-row">
                        <div class="trend-label"><i class="fas fa-chart-line"></i> 近${RANKING_DAYS}天频率</div>
                        ${activityTrendHtml}
                        <span class="trend-value">${lastActivity} 条/天</span>
                    </div>
                    <div class="trend-row">
                        <div class="trend-label"><i class="fas fa-heart"></i> 近${RANKING_DAYS}天得分</div>
                        ${scoreTrendHtml}
                        <span class="trend-value">${Number(lastScore || 0).toFixed(1)}</span>
                    </div>
                </div>
            </div>
        `;
        container.appendChild(div);
    });
}

function formatRelativeTime(timestamp) {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now - date;
    if (isNaN(diffMs)) return '时间未知';
    
    const minutes = Math.floor(diffMs / (1000 * 60));
    if (minutes < 1) return '刚刚';
    if (minutes < 60) return `${minutes} 分钟前`;
    
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours} 小时前`;
    
    const days = Math.floor(hours / 24);
    if (days < 30) return `${days} 天前`;
    
    const months = Math.floor(days / 30);
    if (months < 12) return `${months} 个月前`;
    
    const years = Math.floor(months / 12);
    return `${years} 年前`;
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

function formatRadarLabel(name = '') {
    const text = String(name ?? '').trim();
    if (text.length <= RADAR_LABEL_WRAP_THRESHOLD) return text;
    const parts = text.split(/\s+/).filter(Boolean);
    if (parts.length > 1) {
        const mid = Math.ceil(parts.length / 2);
        return `${parts.slice(0, mid).join(' ')}\n${parts.slice(mid).join(' ')}`;
    }
    const midpoint = Math.ceil(text.length / 2);
    return `${text.slice(0, midpoint)}\n${text.slice(midpoint)}`;
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
        tooltip: {
            trigger: 'item',
            borderRadius: 8,
            backgroundColor: 'rgba(15,23,42,0.9)',
            borderColor: 'rgba(99,102,241,0.4)',
            textStyle: { color: '#e2e8f0' }
        },
        radar: {
            shape: 'circle',
            splitNumber: 5,
            indicator: [
                { name: '情感因素', max: 100 },
                { name: '互动频率', max: 100 },
                { name: '对话流畅', max: 100 },
                { name: '消息均衡', max: 100 }
            ],
            center: ['50%', '55%'],
            radius: '68%',
            axisName: {
                color: '#e2e8f0',
                fontSize: 13,
                fontWeight: 500,
                lineHeight: 18,
                distance: 10,
                formatter: formatRadarLabel
            },
            splitArea: {
                areaStyle: {
                    color: ['rgba(99, 102, 241, 0.12)', 'rgba(99, 102, 241, 0.06)'],
                    shadowColor: 'rgba(0, 0, 0, 0.25)',
                    shadowBlur: 14
                }
            },
            axisLine: {
                lineStyle: {
                    color: 'rgba(255, 255, 255, 0.12)'
                }
            },
            splitLine: {
                lineStyle: {
                    color: 'rgba(255, 255, 255, 0.12)'
                }
            }
        },
        series: [{
            name: '亲密度分析',
            type: 'radar',
            symbol: 'circle',
            symbolSize: 6,
            areaStyle: {
                color: {
                    type: 'radial',
                    x: 0.5,
                    y: 0.5,
                    r: 0.8,
                    colorStops: [
                        { offset: 0, color: 'rgba(99, 102, 241, 0.8)' },
                        { offset: 1, color: 'rgba(20, 184, 166, 0.25)' }
                    ]
                }
            },
            lineStyle: {
                color: '#22d3ee',
                width: 2.5
            },
            itemStyle: {
                color: '#22d3ee',
                shadowBlur: 8,
                shadowColor: 'rgba(34, 211, 238, 0.6)'
            },
            data: [{
                value: [0, 0, 0, 0],
                name: '亲密度分析'
            }]
        }]
    };
    
    radarChart.setOption(option);
}

// Update Radar Chart with data
function updateRadarChart() {
    if (!radarChart || !analysisData) return;
    
    const factors = [
        { name: '情感因素', value: analysisData.sentiment_factor, max: 40 },
        { name: '互动频率', value: analysisData.frequency_factor, max: 30 },
        { name: '对话流畅', value: analysisData.flow_factor, max: 20 },
        { name: '消息均衡', value: analysisData.consecutive_factor, max: 10 }
    ];
    
    const normalizedValues = factors.map(f => Math.min(100, Math.max(0, (f.value / f.max) * 100)));
    
    radarChart.setOption({
        tooltip: {
            formatter: () => {
                return factors.map(f => `${f.name}: ${f.value.toFixed(1)} / ${f.max}`).join('<br/>');
            }
        },
        radar: {
            indicator: factors.map(f => ({ name: f.name, max: 100 })),
            axisName: {
                formatter: formatRadarLabel,
                color: '#e2e8f0',
                fontSize: 13,
                fontWeight: 500,
                lineHeight: 18,
                distance: 10
            },
            radius: '68%',
            center: ['50%', '55%']
        },
        series: [{
            data: [{
                value: normalizedValues,
                name: '亲密度分析'
            }]
        }]
    });
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    return String(text ?? '').replace(/[&<>"']/g, (m) => HTML_ESCAPE_MAP[m] || m);
}
