# AI Resume Builder Backend

A complete Python FastAPI backend for an AI Resume Builder platform that provides REST APIs for user authentication, profile management, PDF processing, and session-based AI chat functionality.

## Features

- **User Authentication**: JWT-based authentication with registration and login
- **Profile Management**: CRUD operations for user profiles
- **PDF Processing**: LinkedIn PDF upload and AI-powered parsing using OpenAI
- **Search & Discovery**: User search with filtering capabilities
- **Session-based Chat**: AI chat without conversation persistence
- **Rate Limiting**: 10 requests per day per user
- **File Upload**: Profile pictures and PDF handling

## Tech Stack

- **Framework**: FastAPI with Python 3.9+
- **Database**: MongoDB with Motor (async driver)
- **Authentication**: JWT tokens
- **AI Integration**: OpenAI API (GPT-3.5-turbo)
- **PDF Processing**: PyPDF2 + pdfplumber
- **File Storage**: Local file system

## Setup Instructions

### 1. Environment Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Edit `.env` with your values:
- MongoDB connection string
- OpenAI API key
- JWT secret key

### 3. Database Setup

**MongoDB Atlas (Free Tier)**:
1. Create account at [mongodb.com](https://mongodb.com)
2. Create free M0 cluster
3. Get connection string
4. Add to `.env` file

### 4. Run Application

```bash
# Development
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 5. API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - User login

### Users
- `GET /api/v1/users/me` - Get current user profile
- `PUT /api/v1/users/me` - Update current user profile
- `GET /api/v1/users/{user_id}` - Get public user profile
- `GET /api/v1/users/` - Get featured users

### Onboarding
- `POST /api/v1/onboarding/upload-pdf` - Upload LinkedIn PDF
- `POST /api/v1/onboarding/complete` - Complete onboarding

### Chat
- `POST /api/v1/chat/{user_id}` - Chat with user profile
- `GET /api/v1/chat/suggestions/{user_id}` - Get chat suggestions

### Search
- `GET /api/v1/search/users` - Search users with filters

## Sample API Calls

### Register User
```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
-H "Content-Type: application/json" \
-d '{
  "email": "test@example.com",
  "password": "password123",
  "name": "John Doe"
}'
```

### Login
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
-H "Content-Type: application/json" \
-d '{
  "email": "test@example.com",
  "password": "password123"
}'
```

### Upload PDF
```bash
curl -X POST "http://localhost:8000/api/v1/onboarding/upload-pdf" \
-H "Authorization: Bearer YOUR_JWT_TOKEN" \
-F "file=@linkedin_profile.pdf"
```

### Chat with Profile
```bash
curl -X POST "http://localhost:8000/api/v1/chat/USER_ID" \
-H "Authorization: Bearer YOUR_JWT_TOKEN" \
-H "Content-Type: application/json" \
-d '{"message": "Tell me about their technical skills"}'
```

### Search Users
```bash
curl -X GET "http://localhost:8000/api/v1/search/users?q=developer&skills=python,javascript&limit=10"
```

## Project Structure

```
backend/
├── app/
│   ├── main.py                 # FastAPI application entry point
│   ├── config.py              # Configuration and environment variables
│   ├── database.py            # MongoDB connection and setup
│   ├── models/                # Pydantic models and MongoDB schemas
│   │   ├── user.py           # User-related models
│   │   ├── chat.py           # Chat-related models
│   │   └── onboarding.py     # Onboarding models
│   ├── routers/              # API route handlers
│   │   ├── auth.py           # Authentication endpoints
│   │   ├── users.py          # User profile endpoints
│   │   ├── onboarding.py     # Onboarding flow endpoints
│   │   ├── chat.py           # Chat functionality
│   │   └── search.py         # Search and discovery
│   ├── services/             # Business logic services
│   │   ├── auth_service.py   # Authentication logic
│   │   ├── user_service.py   # User management logic
│   │   ├── pdf_service.py    # PDF processing logic
│   │   ├── ai_service.py     # OpenAI integration
│   │   └── file_service.py   # File handling logic
│   └── utils/                # Utility functions
│       ├── security.py       # JWT and password hashing
│       ├── rate_limiter.py   # Rate limiting logic
│       └── helpers.py        # Common helper functions
├── uploads/                  # File storage directory
├── requirements.txt          # Python dependencies
├── .env.example             # Environment variables template
└── README.md               # This file
```

## Implementation Notes

### Rate Limiting
- Implemented at the user level
- Resets daily
- 10 requests per user per day for chat functionality

### File Storage
- Local file system for MVP
- Easy to switch to cloud storage later
- Automatic cleanup after PDF processing

### AI Integration
- Direct OpenAI API calls using GPT-3.5-turbo
- Cost-effective for MVP
- Response tokens limited to keep costs low

### Security
- JWT tokens for authentication
- Password hashing with bcrypt
- Input validation with Pydantic
- CORS enabled for frontend integration

### Database
- MongoDB for flexibility
- Proper indexing for performance
- Async operations with Motor

## Cost Optimization

### OpenAI Usage
- Use GPT-3.5-turbo (10x cheaper than GPT-4)
- Limited response tokens
- Session-based chat (no conversation storage)

### Database
- MongoDB Atlas free tier (512MB)
- Efficient indexing
- Clean up unused data

### File Storage
- Local storage for MVP
- File cleanup after processing
- Image compression for profile pictures

## Development Tips

1. Always test with frontend CORS settings
2. Monitor OpenAI API usage costs
3. Implement proper error handling
4. Use environment variables for all secrets
5. Test rate limiting thoroughly
6. Validate all file uploads

## Production Deployment

1. Set strong JWT secret key
2. Use production MongoDB cluster
3. Implement proper logging
4. Set up monitoring
5. Use environment-specific settings
6. Implement backup strategies

## Support

For issues and questions:
- Check the API documentation at `/docs`
- Review error responses for debugging
- Ensure all environment variables are set
- Verify MongoDB connection
- Check OpenAI API key validity# CVChatter
