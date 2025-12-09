# SNS - Sentiment Analysis Chat Application

A modern chat application with real-time sentiment analysis and relationship tracking features.

## Overview

SNS (Sentiment Analysis Chat) is a sophisticated chat platform that analyzes the emotional tone of conversations in real-time and tracks relationship intimacy between users. The application uses Natural Language Processing (NLP) to provide insights into communication patterns and relationship dynamics.

## Features

- **User Management**: User registration, authentication, and profile management
- **Real-time Chat**: Send and receive messages between users
- **Sentiment Analysis**: Automatic sentiment analysis of chat messages using NLP
- **Relationship Tracking**: Monitor friendship intimacy scores based on interaction patterns
- **Chinese Language Support**: Native support for Chinese text processing using Jieba

## Technology Stack

### Backend
- **FastAPI**: Modern, fast web framework for building APIs
- **SQLAlchemy**: SQL toolkit and ORM for database operations
- **Pydantic**: Data validation using Python type annotations
- **Uvicorn**: ASGI server for running the application
- **Jieba**: Chinese text segmentation library for NLP

### Database
- **SQLite**: Default database (easily switchable to PostgreSQL/MySQL)

## Project Structure

```
SNS/
├── backend/
│   ├── app/
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   └── config.py          # Configuration and settings
│   │   ├── db/
│   │   │   ├── __init__.py
│   │   │   ├── base.py            # Base class for ORM models
│   │   │   └── session.py         # Database session handling
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── user.py            # User model
│   │   │   ├── message.py         # Message model with sentiment fields
│   │   │   └── friendship.py      # Friendship model with intimacy tracking
│   │   ├── __init__.py
│   │   └── main.py                # Application entry point
│   ├── __init__.py
│   └── requirements.txt           # Python dependencies
└── README.md
```

## Getting Started

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
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
   ```

5. **Run the application**
   ```bash
   # From the backend directory
   python -m backend.app.main
   
   # Or using uvicorn directly
   uvicorn backend.app.main:app --reload
   ```

6. **Access the API**
   - API: http://localhost:8000
   - Interactive API docs: http://localhost:8000/docs
   - Alternative API docs: http://localhost:8000/redoc

## Database Models

### User
- Stores user account information
- Fields: id, username, email, hashed_password, full_name, created_at, updated_at

### Message
- Stores chat messages with sentiment analysis results
- Fields: id, sender_id, receiver_id, content, sentiment_score, positive_score, negative_score, neutral_score, created_at

### Friendship
- Tracks relationships between users with intimacy metrics
- Fields: id, user_id, friend_id, intimacy_score, interaction_count, positive_interactions, negative_interactions, status, created_at, updated_at

## API Endpoints

### Root
- `GET /` - Returns application information
- `GET /health` - Health check endpoint

*More endpoints will be added in subsequent phases*

## Development Roadmap

### Phase 1: Project Initialization ✓
- [x] Set up project structure
- [x] Create database models
- [x] Configure FastAPI application
- [x] Add documentation

### Phase 2: Chat Functionality (Upcoming)
- [ ] Implement user authentication
- [ ] Create chat message endpoints
- [ ] Add WebSocket support for real-time messaging
- [ ] Implement friend management

### Phase 3: NLP and Analysis (Upcoming)
- [ ] Integrate sentiment analysis
- [ ] Implement intimacy score calculation
- [ ] Add conversation insights
- [ ] Create analytics dashboard

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License.

## Contact

For questions or feedback, please open an issue on GitHub.
