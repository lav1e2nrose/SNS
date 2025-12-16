# SNS - Sentiment Analysis Chat Application

A modern chat application with real-time sentiment analysis and relationship tracking features.

## Overview

SNS (Sentiment Analysis Chat) is a sophisticated chat platform that analyzes the emotional tone of conversations in real-time and tracks relationship intimacy between users. The application uses Natural Language Processing (NLP) to provide insights into communication patterns and relationship dynamics.

## Features

- **User Management**: User registration, authentication (JWT), and profile management
- **Real-time Chat**: Send and receive messages between users via WebSocket
- **Read/Unread Status**: Track message read status for better communication
- **Friend Management**: Add, accept, remove friends with full CRUD operations
- **Sentiment Analysis**: Automatic sentiment analysis of chat messages using LLM (DashScope/Qwen)
- **Word Cloud Generation**: Analyze word frequency in conversations using Jieba
- **Relationship Tracking**: Monitor friendship intimacy scores based on interaction patterns
- **Friend Rankings**: Leaderboard showing friends ranked by intimacy score
- **Chinese Language Support**: Native support for Chinese text processing using Jieba

## Technology Stack

### Backend
- **FastAPI**: Modern, fast web framework for building APIs
- **SQLAlchemy**: SQL toolkit and ORM for database operations
- **Pydantic**: Data validation using Python type annotations
- **Uvicorn**: ASGI server for running the application
- **Jieba**: Chinese text segmentation library for NLP
- **DashScope**: LLM API for sentiment analysis (optional)
- **WebSockets**: Real-time communication
- **JWT**: Secure token-based authentication

### Frontend
- **HTML5/CSS3/JavaScript**: Modern web frontend
- **WebSocket API**: Real-time chat functionality

### Database
- **SQLite**: Default database (easily switchable to PostgreSQL/MySQL)

## Project Structure

```
SNS/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── api_v1/
│   │   │   │   ├── endpoints/
│   │   │   │   │   ├── auth.py         # Authentication endpoints
│   │   │   │   │   ├── chat.py         # Chat and messaging endpoints
│   │   │   │   │   ├── friends.py      # Friend management endpoints
│   │   │   │   │   ├── analysis.py     # Analysis endpoints
│   │   │   │   │   └── rankings.py     # Rankings endpoints
│   │   │   │   └── api.py              # API router
│   │   │   └── deps.py                 # API dependencies
│   │   ├── core/
│   │   │   ├── config.py               # Configuration and settings
│   │   │   └── security.py             # JWT and password utilities
│   │   ├── db/
│   │   │   ├── base.py                 # Base class for ORM models
│   │   │   └── session.py              # Database session handling
│   │   ├── models/
│   │   │   ├── user.py                 # User model
│   │   │   ├── message.py              # Message model with sentiment fields
│   │   │   └── friendship.py           # Friendship model with intimacy tracking
│   │   ├── schemas/
│   │   │   ├── user.py                 # User schemas
│   │   │   ├── message.py              # Message schemas
│   │   │   ├── friendship.py           # Friendship schemas
│   │   │   ├── analysis.py             # Analysis schemas
│   │   │   ├── ranking.py              # Ranking schemas
│   │   │   └── token.py                # Token schemas
│   │   ├── services/
│   │   │   ├── analysis_service.py     # Word cloud, sentiment, intimacy
│   │   │   └── connection_manager.py   # WebSocket connection manager
│   │   └── main.py                     # Application entry point
│   ├── tests/
│   │   ├── conftest.py                 # Test fixtures
│   │   ├── test_auth.py                # Authentication tests
│   │   ├── test_chat.py                # Chat tests
│   │   ├── test_friends.py             # Friend management tests
│   │   ├── test_analysis.py            # Analysis tests
│   │   └── test_rankings.py            # Rankings tests
│   └── requirements.txt                # Python dependencies
├── frontend/
│   ├── index.html                      # Main HTML page
│   ├── styles.css                      # CSS styles
│   └── app.js                          # JavaScript application
└── README.md
```

## Getting Started

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/lav1e2nrose/SNS.git
   cd SNS
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

4. **Configure environment variables (optional)**
   
   Create a `.env` file in the `backend/` directory:
   ```env
   DATABASE_URL=sqlite:///./sns.db
   DEBUG=True
   HOST=0.0.0.0
   PORT=8000
   SECRET_KEY=your-secret-key-here
   DASHSCOPE_API_KEY=your-dashscope-api-key  # Required for LLM sentiment analysis
   ```

### Using Qwen API for Sentiment Scoring

The application uses Alibaba's Qwen (通义千问) API through DashScope for intelligent sentiment analysis. Here's how to set it up:

#### Step 1: Get Your API Key

1. Visit [阿里云DashScope控制台](https://dashscope.console.aliyun.com/)
2. Register or log in to your Alibaba Cloud account
3. Navigate to "API-KEY管理" (API Key Management)
4. Create a new API key and copy it

#### Step 2: Configure the API Key

Set the `DASHSCOPE_API_KEY` environment variable:

**Option A: Using .env file (Recommended)**
```bash
# Create/edit backend/.env file
echo "DASHSCOPE_API_KEY=sk-your-api-key-here" >> backend/.env
```

**Option B: Using environment variable**
```bash
# Linux/macOS
export DASHSCOPE_API_KEY=sk-your-api-key-here

# Windows (PowerShell)
$env:DASHSCOPE_API_KEY="sk-your-api-key-here"
```

#### Step 3: Use the Sentiment Analysis API

Once configured, you can use the sentiment analysis endpoint:

```bash
# Analyze sentiment of a text message
curl -X POST "http://localhost:8000/api/v1/analysis/sentiment" \
  -H "Content-Type: application/json" \
  -d '{"text": "今天天气真好，我很开心！"}'
```

**Response Example:**
```json
{
  "sentiment_score": 0.85,
  "positive_score": 0.80,
  "negative_score": 0.05,
  "neutral_score": 0.15
}
```

- `sentiment_score`: Overall sentiment from -1 (very negative) to 1 (very positive)
- `positive_score`: Probability of positive sentiment (0-1)
- `negative_score`: Probability of negative sentiment (0-1)
- `neutral_score`: Probability of neutral sentiment (0-1)

#### Automatic Message Scoring

When users send chat messages through WebSocket, the system automatically analyzes sentiment and stores scores with each message. These scores are then used to calculate intimacy ratings between users.

5. **Run the application**
   ```bash
   # From the project root directory
   cd ..
   python -m uvicorn backend.app.main:app --reload
   ```

6. **Access the application**
   - Web Interface: http://localhost:8000
   - Interactive API docs: http://localhost:8000/docs
   - Alternative API docs: http://localhost:8000/redoc

### Running Tests

```bash
cd SNS
python -m pytest backend/tests/ -v
```

## Database Models

### User
- Stores user account information
- Fields: id, username, email, hashed_password, full_name, created_at, updated_at

### Message
- Stores chat messages with sentiment analysis results and read status
- Fields: id, sender_id, receiver_id, content, is_read, sentiment_score, positive_score, negative_score, neutral_score, created_at

### Friendship
- Tracks relationships between users with intimacy metrics
- Fields: id, user_id, friend_id, intimacy_score, interaction_count, positive_interactions, negative_interactions, status, created_at, updated_at

## API Endpoints

### Authentication (`/api/v1/auth`)
- `POST /register` - Register a new user
- `POST /login` - Login and get JWT token

### Friends (`/api/v1/friends`)
- `GET /` - Get list of friends
- `POST /` - Send friend request
- `PUT /{friend_id}` - Update friendship status (accept, block)
- `DELETE /{friend_id}` - Remove friend

### Chat (`/api/v1`)
- `GET /chat/{friend_id}` - Get chat history
- `PUT /chat/{friend_id}/read` - Mark messages as read
- `GET /chat/{friend_id}/unread` - Get unread message count
- `WebSocket /ws/{friend_id}` - Real-time chat connection

### Analysis (`/api/v1/analysis`)
- `POST /sentiment` - Analyze text sentiment
- `POST /wordcloud` - Generate word cloud data
- `POST /intimacy` - Calculate intimacy score

### Rankings (`/api/v1/rankings`)
- `GET /top-friends` - Get friends ranked by intimacy score

### System
- `GET /` - Serve frontend or return API info
- `GET /health` - Health check endpoint

## Development Roadmap

### Phase 1: 基础框架搭建 ✓
- [x] 初始化 GitHub 仓库
- [x] 搭建 FastAPI 后端架子，配置数据库连接
- [x] 实现用户注册/登录 (JWT Auth)

### Phase 2: 聊天功能实现 ✓
- [x] 实现 WebSocket 实时通讯
- [x] 实现 RESTful API 发送消息、获取历史
- [x] 实现已读/未读状态
- [x] 实现好友管理 (添加/删除/接受好友)
- [x] 编写 Web 前端页面测试聊天

### Phase 3: 数据分析引擎 ✓
- [x] 集成 jieba 进行分词和词频统计
- [x] 集成 LLM API 进行情感打分
- [x] 实现"亲密值"计算逻辑

### Phase 4: 排行榜与可视化 ✓
- [x] 后端实现排行榜 API
- [x] 前端页面开发：好友列表、聊天窗口、数据分析面板

### Phase 5: 测试与交付 ✓
- [x] 编写单元测试 (Pytest) - 30 tests
- [x] 集成测试聊天流程

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License.

## Contact

For questions or feedback, please open an issue on GitHub.
