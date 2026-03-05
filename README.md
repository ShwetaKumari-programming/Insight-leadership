
# UPI Analytics Conversational Website

This project is a conversational analytics platform for UPI transactions, built with FastAPI and Python. It provides interactive dashboards, chat-based analytics, and multiple frontend pages for performance, trends, failures, and more.

## Features
- Conversational analytics powered by ChatGPT
- Real-time chat interface
- Dashboard for transaction metrics
- Performance, trends, weekend, and failure analysis
- User authentication (login, registration, password reset)
- Static frontend pages served via FastAPI

## Project Structure
```
conversation/
├── main.py                # FastAPI backend
├── static/                # Static frontend files (HTML, JS, CSS)
│   ├── login.html
│   ├── signin.html
│   ├── dashboard.js
│   ├── styles.css
│   └── ...
├── routers/               # API routers for metrics, performance, trends, weekend
├── analytics_engine.py    # Analytics logic
├── chatgpt_connector.py   # ChatGPT integration
├── requirements.txt       # Python dependencies
├── user_db.json           # User database
└── ...
```

## How to Run
0. Configure local environment variables (never commit secrets):
   ```bash
   copy .env.example .env
   ```
   Then set `OPENAI_API_KEY` in `.env` with your own key.

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Start the server:
   ```bash
   python -m uvicorn main:app --host 127.0.0.1 --port 8001 --reload
   ```
3. Open the website in your browser:
   - Main page: [http://127.0.0.1:8001/](http://127.0.0.1:8001/)
   - Login: [http://127.0.0.1:8001/login](http://127.0.0.1:8001/login)
   - Dashboard: [http://127.0.0.1:8001/dashboard](http://127.0.0.1:8001/dashboard)
   - Chat: [http://127.0.0.1:8001/chat](http://127.0.0.1:8001/chat)

## API Endpoints
- `/api/login` - User login
- `/api/register` - User registration
- `/api/reset-password` - Password reset
- `/api/metrics/dashboard` - Dashboard metrics
- `/api/ask` - ChatGPT analytics
- `/api/qa-stats` - Q&A statistics

## Customization
- Edit HTML files in `static/` for frontend changes
- Add new API routes in `routers/`
- Update analytics logic in `analytics_engine.py`

## Security Notes
- Keep real API keys only in `.env` (already ignored by Git).
- `.env.example` is safe to commit because it only contains placeholders.
- Before pushing, scan for accidental keys:
   ```bash
   git grep -n "sk-proj-\|OPENAI_API_KEY="
   ```

## License
MIT License
"# Leadership-analytics"  
