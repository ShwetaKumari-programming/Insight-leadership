
from fastapi import FastAPI, Request, HTTPException, WebSocket, WebSocketDisconnect, Body
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import os
import asyncio
from typing import Optional

app = FastAPI(
    title="Conversational Leadership Analytics",
)

# Dedicated route to always serve chat.html from the project root
@app.get("/chat.html")
async def get_chat_html():
    return FileResponse("chat.html")

STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
app.mount("/static", StaticFiles(directory=STATIC_DIR, html=True), name="static")


# ...existing code...

@app.post("/chat")
async def chat(request: Request):
    from chatgpt_connector import ask_chatgpt

    data = await request.json()
    user_message = data.get("message")
    context = data.get("context")

    if not user_message:
        return JSONResponse({"reply": "Please send a non-empty message."}, status_code=400)

    result = ask_chatgpt(user_message, context)
    if not result.get("success"):
        return JSONResponse({"reply": result.get("response", "Chat service unavailable.")}, status_code=503)

    return JSONResponse({
        "reply": result.get("response", ""),
        "model": result.get("model", "unknown")
    })

# Generic fallback route to serve any HTML file in the root directory (must be last)

# ...existing code...

@app.get("/{filename}")
async def serve_any_html(filename: str):
    # Serve HTML files from static directory if requested at root
    if filename.endswith('.html'):
        static_file_path = os.path.join(STATIC_DIR, filename)
        if os.path.exists(static_file_path):
            return FileResponse(static_file_path)
        # Also check root directory for legacy support
        root_file_path = os.path.join(os.path.dirname(__file__), filename)
        if os.path.exists(root_file_path):
            return FileResponse(root_file_path)
    return JSONResponse({"detail": "Not Found"}, status_code=404)
    return {"detail": "Not Found"}

 # ...existing code...

# Password reset endpoint (must be after app is defined)
@app.post("/api/reset-password", tags=["User"])
async def reset_password(
    username: str = Body(...),
    new_password: str = Body(...)
):
    users = load_users()
    found = False
    for user in users:
        if user["username"] == username:
            user["password"] = new_password
            found = True
            break
    if not found:
        return {"success": False, "detail": "User not found"}
    save_users(users)
    return {"success": True}
"""
Conversational Leadership Analytics - UPI Transaction Intelligence
No SQL. Pure Python + Pandas. Chat-first analytics.
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
# WebSocket endpoint for real-time chat streaming
import asyncio

# Initialize FastAPI app
app = FastAPI(
    title="Conversational Leadership Analytics",
)


# Streaming ChatGPT response generator
async def stream_chatgpt_response(question: str, context=None):
    import asyncio
    from chatgpt_connector import ask_chatgpt
    # Call ChatGPT for the answer
    result = ask_chatgpt(question, context)
    answer = result.get('response', 'Sorry, I could not get an answer.')
    # Stream word by word for effect
    for word in answer.split():
        yield word + " "
        await asyncio.sleep(0.02)  # Faster stream

@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            question = data
            context = None

            # Accept either plain text messages or JSON payloads from the frontend.
            try:
                payload = json.loads(data)
                question = (payload.get("message") or "").strip()
                history = payload.get("history", [])
                context = payload.get("context")

                if not context and isinstance(history, list) and history:
                    # Keep context compact to avoid token bloat while still enabling memory.
                    recent = history[-8:]
                    context_lines = []
                    for item in recent:
                        role = item.get("role", "user")
                        content = str(item.get("content", "")).strip()
                        if content:
                            context_lines.append(f"{role}: {content}")
                    if context_lines:
                        context = "\n".join(context_lines)
            except Exception:
                pass

            if not question:
                await websocket.send_text("Please send a non-empty message.")
                await websocket.send_text("__END__")
                continue

            # Use ChatGPT for all questions.
            async for chunk in stream_chatgpt_response(question, context):
                await websocket.send_text(chunk)
            await websocket.send_text("__END__")  # Signal end of message
    except WebSocketDisconnect:
        print("WebSocket disconnected")
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
import time
import os
import json
import pandas as pd
import numpy as np

from processor import processor
from analytics import analytics
from config import HOST, PORT, DEBUG
from explainability_layer import explainability_engine
from metrics import log_request, REQUEST_LOG
from chatgpt_connector import is_chatgpt_available, ask_chatgpt
from data_utils import load_transaction_data
from routers.metrics import router as metrics_router
from routers.weekend import router as weekend_router
from routers.trends import router as trends_router
from routers.performance import router as performance_router

# Helper function for insights
def get_recommended_actions(report: dict) -> list:
    """Generate recommended actions from analysis"""
    actions = []
    
    if 'summary' in report:
        summary = report['summary']
        
        if summary.get('increase_ratio', 0) > 2:
            actions.append({
                "priority": "CRITICAL",
                "action": "Investigate weekend-specific configurations",
                "reason": f"Failures are {summary['increase_ratio']}x higher on weekends"
            })
        
        if 'weekend_failure_rate' in summary:
            if summary['weekend_failure_rate'] > 10:
                actions.append({
                    "priority": "HIGH",
                    "action": "Add weekend monitoring and alerts",
                    "reason": f"Weekend failure rate is {summary['weekend_failure_rate']:.1f}%"
                })
    
    return actions

## Duplicate FastAPI app initialization removed. Only one app instance should exist, defined at the top of the file.

# Configure CORS to allow requests from frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get current directory for static files
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")

# Mount static files (CSS, JS)
app.mount("/static", StaticFiles(directory=STATIC_DIR, html=True), name="static")

# Include routers
app.include_router(metrics_router)
app.include_router(weekend_router)
app.include_router(trends_router)
app.include_router(performance_router)


@app.on_event("startup")
async def startup_message():
    print("Backend server started")
    # Auto-load UPI transaction data from CSV into analytics engine on startup
    try:
        from analytics_engine import analytics_engine
        df = load_transaction_data()
        analytics_engine.load_data(df)
        print(f"✅ Loaded {len(df):,} UPI transactions from CSV into analytics engine")
    except Exception as e:
        print(f"⚠️ Could not auto-load transaction data: {e}")


# Request/Response Models
class QuestionRequest(BaseModel):
    """Model for incoming question requests"""
    question: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None


class QuestionResponse(BaseModel):
    """Model for outgoing responses"""
    response: str
    success: bool
    processing_time: float
    question_type: str
    timestamp: str
    explanation_why: Optional[str] = None


class AnalyticsResponse(BaseModel):
    """Model for analytics data"""
    total_questions_processed: int
    total_responses_sent: int
    average_question_length: float
    total_characters_processed: int
    top_words: dict


# API Endpoints

# Serve signin.html directly
import os
import json

# User Registration/Login Models
class UserRegisterRequest(BaseModel):
    username: str
    password: str
    role: Optional[str] = "Viewer"

class UserLoginRequest(BaseModel):
    username: str
    password: str

# User DB file
USER_DB_PATH = os.path.join(os.path.dirname(__file__), "user_db.json")

def load_users():
    with open(USER_DB_PATH, "r") as f:
        return json.load(f)["users"]

def save_users(users):
    with open(USER_DB_PATH, "w") as f:
        json.dump({"users": users}, f, indent=2)

# Registration endpoint
@app.post("/api/register", tags=["User"])
async def register_user(user: UserRegisterRequest):
    users = load_users()
    if any(u["username"] == user.username for u in users):
        raise HTTPException(status_code=400, detail="Username already exists")
    users.append({"username": user.username, "password": user.password, "role": user.role})
    save_users(users)
    return {"success": True, "message": "User registered successfully"}

# Login endpoint
@app.post("/api/login", tags=["User"])
async def login_user(user: UserLoginRequest):
    users = load_users()
    found = next((u for u in users if u["username"] == user.username and u["password"] == user.password), None)
    if not found:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    return {"success": True, "role": found["role"]}

# Frontend Page Routes
@app.get("/", tags=["Frontend"])
async def serve_home():
    """Serve the dashboard as the default homepage for stable real-data experience."""
    return FileResponse("dashboard.html")

@app.get("/dashboard", tags=["Frontend"])
@app.get("/dashboard.html", tags=["Frontend"])
async def serve_dashboard_page():
    """Serve the dashboard page"""
    return FileResponse("dashboard.html")

@app.get("/failures", tags=["Frontend"])
@app.get("/failures.html", tags=["Frontend"])
async def serve_failures_page():
    """Serve the failure analysis page"""
    return FileResponse("failures.html")

@app.get("/weekend", tags=["Frontend"])
@app.get("/weekend.html", tags=["Frontend"])
async def serve_weekend_page():
    """Serve the weekend analysis page"""
    return FileResponse("weekend.html")

@app.get("/performance", tags=["Frontend"])
@app.get("/performance.html", tags=["Frontend"])
async def serve_performance_page():
    """Serve the performance metrics page"""
    return FileResponse("performance.html")

@app.get("/trends", tags=["Frontend"])
@app.get("/trends.html", tags=["Frontend"])
async def serve_trends_page():
    """Serve the trends & forecasting page"""
    return FileResponse("trends.html")

@app.get("/chat", tags=["Frontend"])
@app.get("/chat.html", tags=["Frontend"])
async def serve_chat_page():
    """Serve the chat interface page"""
    return FileResponse("chat.html")

@app.get("/home", tags=["Frontend"])
async def serve_home_page():
    """Serve stable home experience backed by real transaction dataset."""
    return FileResponse("dashboard.html")

# Add missing /login endpoint
@app.get("/login", tags=["Frontend"])
@app.get("/login.html", tags=["Frontend"])
async def serve_login_page():
    """Serve the login page"""
    return FileResponse("login.html")

# Add missing /logout endpoint
@app.get("/logout", tags=["Frontend"])
@app.get("/logout.html", tags=["Frontend"])
async def serve_logout_page():
    """Logout and redirect to login page"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/login")

# Add missing /signin endpoint
@app.get("/signin", tags=["Frontend"])
@app.get("/signin.html", tags=["Frontend"])
async def serve_signin_page():
    """Serve the signin page for new user registration"""
    return FileResponse("signin.html")

# Add missing /reset_password endpoint
@app.get("/reset_password", tags=["Frontend"])
@app.get("/reset_password.html", tags=["Frontend"])
async def serve_reset_password_page():
    """Serve the password reset page"""
    return FileResponse("reset_password.html")



@app.get("/api/qa-stats", tags=["Q&A"])
async def get_qa_stats():
    """Live dataset statistics for the Judge Q&A page"""
    df = load_transaction_data()
    total = len(df)
    failures = df[df['transaction_status'] == 'Failure'] if 'transaction_status' in df.columns else df[df['transaction_status'] == 'Failed']
    weekend = df[df['is_weekend'] == 1] if 'is_weekend' in df.columns else pd.DataFrame()
    weekday = df[df['is_weekend'] == 0] if 'is_weekend' in df.columns else pd.DataFrame()
    we_fail = round(len(weekend[weekend['transaction_status'].isin(['Failure','Failed'])]) / max(len(weekend),1) * 100, 2) if len(weekend) > 0 else 0
    wd_fail = round(len(weekday[weekday['transaction_status'].isin(['Failure','Failed'])]) / max(len(weekday),1) * 100, 2) if len(weekday) > 0 else 0
    fraud = int(df['fraud_flag'].sum()) if 'fraud_flag' in df.columns else 0
    return {
        "total_transactions": total,
        "weekend_failure_rate": we_fail,
        "weekday_failure_rate": wd_fail,
        "fraud_count": fraud,
        "columns": 17,
        "technology": "Python + Pandas + NLP (No SQL)"
    }


@app.get("/api/scope", tags=["Scope"])
async def get_system_scope():
    """What the system deliberately does NOT attempt to do — aligned with leadership analytics focus"""
    df = load_transaction_data()
    total = len(df)
    return {
        "system": "Conversational Leadership Analytics",
        "dataset": f"{total:,} UPI transactions from upi_transactions_2024.csv",
        "total_transactions": total,
        "technology": "Python + Pandas + NLP (No SQL)",
        "deliberately_excludes": [
            {
                "id": 1,
                "title": "No Low-Level Debugging or Engineering Tools",
                "detail": "The system does not diagnose individual transaction errors or provide line-by-line technical root causes. It focuses on high-level patterns, trends, and risks that matter to leadership decisions."
            },
            {
                "id": 2,
                "title": "No SQL Queries or Raw Data Exposure",
                "detail": "No SQL queries, raw tables, or complex data schemas are exposed. All processing happens internally via Python + Pandas. Leaders interact only through natural language."
            },
            {
                "id": 3,
                "title": "No Definitive Causation Claims",
                "detail": "The system explains contributing factors and strong patterns but avoids overpromising certainty beyond what the dataset reliably shows. Correlation is not claimed as causation."
            },
            {
                "id": 4,
                "title": "No Automated Decision Enforcement",
                "detail": "The system provides recommendations and guidance, but final judgment and action remain with leadership, supported by their domain knowledge and organizational context."
            },
            {
                "id": 5,
                "title": "Not a Generic BI Dashboard",
                "detail": "Dashboards are optional drill-downs only. The core product is conversational insight delivery — chat leads the exploration, dashboards support it."
            }
        ]
    }


# Metrics API Endpoints for Dashboard
@app.get("/api/metrics/dashboard", tags=["Metrics"])
async def get_dashboard_metrics():
    """Get all key metrics for dashboard"""
    try:
        from analytics_engine import analytics_engine
        from weekend_analyzer import WeekendAnalyzer
        from metrics_calculator import MetricsCalculator

        # Always use real transaction data from CSV
        df = load_transaction_data()
        analytics_engine.transactions_df = df
        
        # Calculate all metrics
        all_metrics = MetricsCalculator.calculate_all_metrics(df)
        
        # Weekend comparison
        comparison = WeekendAnalyzer.compare_failure_rates(df)
        
        return {
            "metrics": {
                "failure_rate": all_metrics.get('failure_rate', 0),
                "avg_latency": all_metrics.get('avg_latency', 0),
                "total_transactions": all_metrics.get('total_transactions', 0),
                "weekend_ratio": comparison['comparison']['weekend_vs_weekday_ratio'],
                "p95_latency": all_metrics.get('p95_latency', 0),
                "success_rate": all_metrics.get('success_rate', 0),
                "mtbf": all_metrics.get('mtbf', 0),
                "mttr": all_metrics.get('mttr', 0),
            }
        }
    except Exception as e:
        return {"error": str(e), "metrics": {}}




@app.get("/api/metrics/weekend", tags=["Metrics"])
async def get_weekend_metrics():
    """Get weekend vs weekday comparison metrics"""
    try:
        from analytics_engine import analytics_engine
        from weekend_analyzer import WeekendAnalyzer

        # Always use real transaction data from CSV
        df = load_transaction_data()
        analytics_engine.transactions_df = df
        # Get detailed report for root cause analysis and recommendations
        detailed_report = WeekendAnalyzer.detailed_weekend_failure_report(df)
        comparison = detailed_report.get('failure_comparison', {})
        metrics = {
            "weekend_failure_rate": float(comparison.get('weekend', {}).get('failure_rate_percent', 0)),
            "weekday_failure_rate": float(comparison.get('weekday', {}).get('failure_rate_percent', 0)),
            "weekend_transactions": int(comparison.get('weekend', {}).get('total_transactions', 0)),
            "weekday_transactions": int(comparison.get('weekday', {}).get('total_transactions', 0)),
            "weekend_failures": int(comparison.get('weekend', {}).get('failed_count', 0)),
            "weekday_failures": int(comparison.get('weekday', {}).get('failed_count', 0)),
            "weekend_ratio": float(comparison.get('comparison', {}).get('weekend_vs_weekday_ratio', 0)),
        }
        # Error distributions
        root_cause_comparison = detailed_report.get('root_cause_comparison', {})
        weekend_errors = root_cause_comparison.get('weekend', {}).get('root_causes', {})
        weekday_errors = root_cause_comparison.get('weekday', {}).get('root_causes', {})
        weekend_errors = {str(k): int(v) for k, v in (weekend_errors or {}).items()}
        weekday_errors = {str(k): int(v) for k, v in (weekday_errors or {}).items()}
        total_weekend = sum(weekend_errors.values()) if weekend_errors else 1
        total_weekday = sum(weekday_errors.values()) if weekday_errors else 1
        metrics["weekend_error_dist"] = sorted([(code, float((count/total_weekend)*100)) for code, count in weekend_errors.items()], key=lambda x: x[1], reverse=True)[:5]
        metrics["weekday_error_dist"] = sorted([(code, float((count/total_weekday)*100)) for code, count in weekday_errors.items()], key=lambda x: x[1], reverse=True)[:5]

        # Root cause analysis and recommendations
        insights = detailed_report.get('insights', [])
        summary = detailed_report.get('summary', {})
        return {
            "metrics": metrics,
            "root_cause_analysis": {
                "insights": insights,
                "summary": summary
            }
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e), "metrics": {}}


# NOTE: /api/metrics/trends is handled by routers/trends.py (trends_router)
# which provides comprehensive volume analysis from the UPI dataset.


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": time.time()
    }


# NOTE: /api/performance is handled by routers/performance.py (performance_router)


@app.post("/ask", tags=["Test"])
def ask_question_simple(data: dict):
    """Simple test endpoint for debugging"""
    start_time = time.time()
    try:
        print("📩 Question received:", data.get("question", "<no question>"))
        log_request(start_time, success=True)
        return {"answer": "Test response"}
    except Exception:
        log_request(start_time, success=False)
        raise


@app.post("/api/ask", response_model=QuestionResponse, tags=["Chat"])
async def ask_question(request: QuestionRequest):
    """
    UNIFIED AUTO-ROUTING PIPELINE
    
    Automatically processes ANY question through the complete system:
    1. Chat UI receives question
    2. NLP understands intent + entities
    3. Business logic selects analysis type
    4. Pandas filters and analyzes data
    5. Calculates relevant metrics
    6. Explainability layer generates insight
    7. Answer shown to user
    
    Supported question types:
    - Failure Analysis: "Why did failures increase?"
    - Weekend Analysis: "What happened last weekend?"
    - Error Patterns: "What errors are we seeing?"
    - Performance Trends: "Is our system getting slower?"
    - Root Cause Analysis: "Why did X happen?"
    - Comparison Analysis: "Compare weekends vs weekdays"
    """
    
    # ===== STEP 1: VALIDATION =====
    if not request.question or len(request.question.strip()) == 0:
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    
    if len(request.question) > 1000:
        raise HTTPException(status_code=400, detail="Question is too long (max 1000 characters)")
    
    start_time = time.time()
    question_lower_pre = request.question.lower()
    
    # ===== JUDGE Q&A DETECTION =====
    qa_keywords = ['judge question', 'evaluation question', 'what are you building',
                   'leadership question', 'three questions', '3 questions',
                   'data computation', 'how do you compute', 'how is it computed',
                   'assumptions and limitation', 'explain to non-technical',
                   'without sql', 'no sql approach', 'explain insight',
                   'problem understanding', 'what insights']
    if any(kw in question_lower_pre for kw in qa_keywords):
        df = load_transaction_data()
        total = len(df)
        processing_time = time.time() - start_time
        log_request(start_time, success=True)
        qa_response = (
            f"\u2753 **Judge Q&A — System Design & Approach**\n\n"
            f"Our Conversational Leadership Analytics system analyzes {total:,} UPI transactions "
            f"using Python + Pandas + NLP — no SQL.\n\n"
            f"**Three leadership questions we answer:**\n"
            f"1\ufe0f\u20e3 Are UPI failures worse on weekends vs weekdays?\n"
            f"2\ufe0f\u20e3 Which banks have the highest failure rates?\n"
            f"3\ufe0f\u20e3 How many transactions are flagged for fraud?\n\n"
            f"**How we compute (no SQL):** We load the CSV into a Pandas DataFrame, "
            f"filter by `is_weekend` and `transaction_status` columns, then calculate "
            f"failure ratios using `.groupby()` and `.value_counts()`. "
            f"The explainability layer translates these computations into plain-English insights.\n\n"
            f"**Assumptions:** Data is a representative sample; timestamps are IST; "
            f"\"Failed\" status is authoritative; fraud_flag is pre-labeled.\n\n"
            f"\U0001f449 See full Q&A details on the Home page: /home (Q&A tab)"
        )
        return QuestionResponse(
            response=qa_response,
            success=True,
            processing_time=round(processing_time, 3),
            question_type="judge_qa",
            timestamp=str(time.time()),
            explanation_why=None
        )

    # ===== SCOPE / LIMITATIONS DETECTION =====
    scope_keywords = ['not attempt', 'deliberately', 'limitation', 'scope', 'not do', 'exclude',
                      'won\'t do', 'will not do', 'does not do', 'restraint', 'out of scope',
                      'what system will not', 'what it won\'t']
    if any(kw in question_lower_pre for kw in scope_keywords):
        df = load_transaction_data()
        total = len(df)
        processing_time = time.time() - start_time
        log_request(start_time, success=True)
        
        scope_response = (
            f"\U0001f3af **What Our System Deliberately Does NOT Attempt**\n\n"
            f"Our Conversational Leadership Analytics system analyzes {total:,} UPI transactions "
            f"from upi_transactions_2024.csv using Python + Pandas — no SQL. "
            f"It is intentionally focused on leadership-level insights and decision support. "
            f"Here is what it deliberately avoids:\n\n"
            f"1\ufe0f\u20e3 **No Low-Level Debugging** — We don't diagnose individual transaction errors "
            f"or provide line-by-line technical root causes. We focus on high-level patterns, trends, "
            f"and risks that matter to leadership decisions.\n\n"
            f"2\ufe0f\u20e3 **No SQL or Raw Data Exposure** — No SQL queries, raw tables, or complex schemas "
            f"are exposed. All data processing happens internally via Python + Pandas. Leaders interact "
            f"only through natural language.\n\n"
            f"3\ufe0f\u20e3 **No Definitive Causation Claims** — We explain contributing factors and strong "
            f"patterns, but avoid overpromising certainty beyond what our {total:,}-row dataset "
            f"reliably shows. Correlation \u2260 causation.\n\n"
            f"4\ufe0f\u20e3 **No Automated Decision Enforcement** — We provide recommendations and guidance, "
            f"but final judgment remains with leadership, supported by their domain knowledge "
            f"and organizational context.\n\n"
            f"5\ufe0f\u20e3 **Not a Generic BI Dashboard** — Dashboards are optional drill-downs. The core "
            f"product is conversational insight delivery — chat leads the exploration, dashboards support it.\n\n"
            f"By clearly defining what the system does NOT do, we ensure it remains focused, "
            f"trustworthy, and aligned with the core objective of Conversational Leadership Analytics.\n\n"
            f"\U0001f449 See full Scope details on the Home page: /home (Scope tab)"
        )
        
        return QuestionResponse(
            response=scope_response,
            success=True,
            processing_time=round(processing_time, 3),
            question_type="scope_limitations",
            timestamp=str(time.time()),
            explanation_why=None
        )
    
    try:
        # ===== TRY CHATGPT FIRST =====
        if is_chatgpt_available():
            # Get detailed transaction data context
            df = load_transaction_data()
            
            total = len(df)
            successes = len(df[df['transaction_status'] == 'Success'])
            failures = df[df['transaction_status'] == 'Failure']
            
            # Get error type breakdown with codes
            error_summary = ""
            if 'error_type' in failures.columns and len(failures) > 0:
                error_info = []
                for error_type in failures['error_type'].value_counts().head(3).index:
                    sample = failures[failures['error_type'] == error_type].iloc[0]
                    count = len(failures[failures['error_type'] == error_type])
                    code = sample.get('error_code', 'N/A')
                    desc = sample.get('error_description', error_type)
                    error_info.append(f"{desc} ({code}): {count}")
                error_summary = "\n- Top Errors: " + ", ".join(error_info)
            
            context = f"""System Analytics Context:
            - Total Transactions: {total:,}
            - Success Rate: {(successes / total * 100):.1f}%
            - Failure Rate: {(len(failures) / total * 100):.1f}%
            - Failed Transactions: {len(failures):,}{error_summary}"""
            
            chatgpt_result = ask_chatgpt(request.question, context)
            
            if chatgpt_result['success']:
                processing_time = time.time() - start_time
                log_request(start_time, success=True)
                
                return QuestionResponse(
                    response=chatgpt_result['response'],
                    success=True,
                    processing_time=round(processing_time, 3),
                    question_type="chatgpt",
                    timestamp=str(time.time()),
                    explanation_why=None
                )
        
        # ===== STEP 2: NLP PROCESSING (FALLBACK) =====
        from nlp_layer import nlp_engine
        from analytics_engine import analytics_engine
        from weekend_analyzer import WeekendAnalyzer
        from metrics_calculator import MetricsCalculator
        from trend_analyzer import TrendAnalyzer
        
        nlp_result = nlp_engine.process(request.question)
        question_lower = request.question.lower()
        intent = nlp_result.intent
        confidence = nlp_result.confidence
        
        # ===== STEP 3: AUTO-LOAD DATA IF NEEDED =====
        if analytics_engine.transactions_df is None:
            analytics_engine.transactions_df = load_transaction_data()
        
        df = analytics_engine.transactions_df
        
        # ===== STEP 4-6: BUSINESS LOGIC + PANDAS + EXPLAINABILITY =====
        response_text = ""
        question_type = "general"
        explanation_why = None
        
        # ===== ROUTE 1: FAILURE ANALYSIS =====
        if intent == 'failure_analysis':
            question_type = "failure_analysis"
            
            # Load real transaction data with error types
            df_real = load_transaction_data()
            failures = df_real[df_real['transaction_status'] == 'Failure']
            
            # Sub-route: Weekend comparison
            if 'weekend' in question_lower or 'last weekend' in question_lower:
                question_type = "weekend_failure_analysis"
                comparison = WeekendAnalyzer.compare_failure_rates(df)
                causes = WeekendAnalyzer.analyze_weekend_vs_weekday_causes(df)
                
                comparison_explanation = explainability_engine.explain_failure_comparison(comparison)
                causes_explanation = explainability_engine.explain_root_causes(causes)
                response_text = f"{comparison_explanation}\n\n{causes_explanation}"
                
                # Store the comparison explanation as the "why" explanation
                explanation_why = comparison_explanation
            
            # Sub-route: Overall failure analysis with error types
            else:
                question_type = "failure_metrics"
                
                failure_count = len(failures)
                total_count = len(df_real)
                failure_rate = (failure_count / total_count * 100) if total_count > 0 else 0
                
                # Analyze error types with codes and descriptions
                error_type_counts = failures['error_type'].value_counts().to_dict()
                
                # Create detailed error mapping
                error_details = {}
                for error_type in error_type_counts.keys():
                    sample = failures[failures['error_type'] == error_type].iloc[0]
                    error_details[error_type] = {
                        'count': error_type_counts[error_type],
                        'code': sample.get('error_code', 'N/A'),
                        'description': sample.get('error_description', error_type)
                    }
                
                response_text = f"📊 **Failure Analysis Report**\n\n"
                response_text += f"**Overall Status:**\n"
                response_text += f"- Total Transactions: {total_count:,}\n"
                response_text += f"- Failed Transactions: {failure_count:,}\n"
                response_text += f"- Failure Rate: {failure_rate:.2f}%\n\n"
                
                if error_details:
                    response_text += f"**Error Breakdown:**\n"
                    emojis = {
                        'timeout': '⏱️',
                        'payment_error': '💳',
                        'auth_failed': '🔐',
                        'server_error': '🔴',
                        'db_error': '💾'
                    }
                    
                    for error_type, details in sorted(error_details.items(), key=lambda x: x[1]['count'], reverse=True):
                        count = details['count']
                        percentage = (count / failure_count * 100) if failure_count > 0 else 0
                        emoji = emojis.get(error_type, '❌')
                        code = details['code']
                        desc = details['description']
                        
                        response_text += f"{emoji} **{desc}** (`{code}`)\n"
                        response_text += f"   Count: {count} ({percentage:.1f}%)\n\n"
                    
                    # Add recommendations based on top error
                    top_error = max(error_details.items(), key=lambda x: x[1]['count'])[0]
                    top_desc = error_details[top_error]['description']
                    
                    response_text += f"**🚨  Issue:** {top_desc}\n\n"
                    
                    recommendations = {
                        'timeout': 'Improve retry logic',
                        'payment_error': 'Check payment gateway',
                        'auth_failed': 'Fix token handling',
                        'server_error': 'Inspect server logs',
                        'db_error': 'Check DB connections'
                    }
                    response_text += f"**💡 Recommendation:** {recommendations.get(top_error, 'Investigate and monitor this error type.')}"
        
        # ===== ROUTE 2: ROOT CAUSE ANALYSIS =====
        elif intent == 'root_cause_analysis':
            question_type = "root_cause_analysis"
            
            # Analyze failures using real transaction data
            df_real = load_transaction_data()
            failures = df_real[df_real['transaction_status'] == 'Failure']
            if len(failures) > 0:
                error_dist = failures['error_type'].value_counts().to_dict()
                causes = {
                    'error_distribution': error_dist,
                    'total_failures': len(failures),
                    'failure_rate': (len(failures) / len(df_real)) * 100
                }
                
                # Build detailed root cause response
                response_text = f"🔍 **Root Cause Analysis**\n\n"
                response_text += f"Total Failures: {len(failures):,} out of {len(df_real):,} transactions ({causes['failure_rate']:.2f}%)\n\n"
                response_text += f"**Error Distribution:**\n"
                error_map = {
                    'timeout': ('NET_TIMEOUT', 'Network Timeout'),
                    'payment_error': ('PAY_FAILED', 'Payment Gateway Failure'),
                    'auth_failed': ('AUTH_ERR', 'Authentication Error'),
                    'server_error': ('SERVER_ERR', 'Internal Server Error'),
                    'db_error': ('DB_CONN', 'Database Connection Failure')
                }
                for error_type, count in sorted(error_dist.items(), key=lambda x: x[1], reverse=True):
                    code, desc = error_map.get(error_type, ('UNKNOWN', error_type))
                    pct = (count / len(failures) * 100)
                    response_text += f"- **{desc}** (`{code}`): {count:,} ({pct:.1f}%)\n"
            else:
                response_text = "✅ Great news! No significant failures detected in the recent data. Your system is running smoothly."
        
        # ===== ROUTE 3: TREND ANALYSIS =====
        elif intent == 'trend_analysis':
            question_type = "trend_analysis"
            
            # Calculate trends over time using real data
            try:
                df_real = load_transaction_data()
                df_real['date'] = df_real['transaction_time'].dt.date
                daily_stats = df_real.groupby('date').apply(
                    lambda x: (x['transaction_status'].eq('Failure').sum() / len(x)) * 100
                ).reset_index(name='failure_rate')
                
                # Determine trend
                if len(daily_stats) > 1:
                    first_half_avg = daily_stats['failure_rate'].head(len(daily_stats)//2).mean()
                    second_half_avg = daily_stats['failure_rate'].tail(len(daily_stats)//2).mean()
                    
                    if second_half_avg > first_half_avg * 1.1:
                        trend = 'increasing'
                    elif second_half_avg < first_half_avg * 0.9:
                        trend = 'decreasing'
                    else:
                        trend = 'stable'
                else:
                    trend = 'stable'
                
                trend_data = {
                    'trend_direction': trend,
                    'forecast': 'Normal operations expected' if trend == 'stable' else 'Changes expected',
                    'daily_rates': daily_stats['failure_rate'].tolist()
                }
                
                explanation = explainability_engine.explain_trends(trend_data)
            except Exception as e:
                explanation = explainability_engine.explain_trends({
                    'trend_direction': 'stable',
                    'forecast': 'Unable to determine trend'
                })
            
            response_text = explanation
        
        # ===== ROUTE 4: PERFORMANCE ANALYSIS =====
        elif intent == 'performance_analysis':
            question_type = "performance_analysis"
            
            # Calculate performance metrics
            metrics = MetricsCalculator.calculate_all_metrics(df)
            avg_latency = metrics.get('avg_latency', 0)
            p95_latency = metrics.get('p95_latency', 0)
            
            explanation = explainability_engine.explain_performance({
                'avg_latency': avg_latency,
                'p95_latency': p95_latency,
                'metrics': metrics
            })
            response_text = explanation
        
        # ===== ROUTE 5: COMPARISON ANALYSIS =====
        elif intent == 'comparison':
            question_type = "comparison_analysis"
            
            # Default to weekend vs weekday
            comparison = WeekendAnalyzer.compare_failure_rates(df)
            explanation = explainability_engine.explain_failure_comparison(comparison)
            response_text = explanation
        
        # ===== ROUTE 6: GENERAL QUESTIONS =====
        else:
            question_type = "general_inquiry"
            
            # Load real transaction data for context
            df_real = load_transaction_data()
            
            # Check if asking about errors/failures
            if any(word in question_lower for word in ['error', 'timeout', 'payment', 'auth', 'server', 'database', 'db', 'fail']):
                failures = df_real[df_real['transaction_status'] == 'Failure']
                
                if 'error_type' in failures.columns and len(failures) > 0:
                    error_counts = failures['error_type'].value_counts().to_dict()
                    total_failures = len(failures)
                    
                    # Get error details with codes and descriptions
                    error_info = {}
                    for error_type in error_counts.keys():
                        sample = failures[failures['error_type'] == error_type].iloc[0]
                        error_info[error_type] = {
                            'count': error_counts[error_type],
                            'code': sample.get('error_code', 'N/A'),
                            'description': sample.get('error_description', error_type)
                        }
                    
                    response_text = f"📊 **System Error Summary**\n\n"
                    response_text += f"**Error Breakdown ({total_failures} total failures):**\n\n"
                    
                    emojis = {
                        'timeout': '⏱️',
                        'payment_error': '💳',
                        'auth_failed': '🔐',
                        'server_error': '🔴',
                        'db_error': '💾'
                    }
                    
                    for error_type, info in sorted(error_info.items(), key=lambda x: x[1]['count'], reverse=True):
                        count = info['count']
                        percentage = (count / total_failures * 100) if total_failures > 0 else 0
                        emoji = emojis.get(error_type, '❌')
                        code = info['code']
                        desc = info['description']
                        
                        response_text += f"{emoji} **{desc}** (`{code}`): {count} ({percentage:.1f}%)\n"
                    
                    question_type = "error_summary"
                else:
                    # Provide system summary
                    total = len(df_real)
                    successes = len(df_real[df_real['transaction_status'] == 'Success'])
                    failures_count = len(df_real[df_real['transaction_status'] == 'Failure'])
                    success_rate = (successes / total * 100) if total > 0 else 0
                    
                    response_text = f"📊 **System Health Overview**\n\n"
                    response_text += f"- Total Transactions: {total:,}\n"
                    response_text += f"- Successful: {successes:,} ({success_rate:.1f}%)\n"
                    response_text += f"- Failed: {failures_count:,}\n"
            else:
                # Check if asking for comparisons
                if any(word in question_lower for word in ['compare', 'comparison', 'vs', 'versus', 'latency', 'peak', 'network', 'weekend', 'weekday']):
                    # Load real data with comparison columns
                    df_comp = load_transaction_data()
                    
                    response_text = "📊 **Comparative Analysis Report**\n\n"
                    
                    # Comparison 1: Latency Failed vs Success
                    if 'latency_ms' in df_comp.columns:
                        success_latency = df_comp[df_comp['transaction_status'] == 'Success']['latency_ms'].mean()
                        failure_latency = df_comp[df_comp['transaction_status'] == 'Failure']['latency_ms'].mean()
                        latency_diff = failure_latency - success_latency
                        latency_ratio = (failure_latency / success_latency) if success_latency > 0 else 0
                        
                        response_text += f"**⏱️ Latency Comparison:**\n"
                        response_text += f"Failed transactions take **{latency_diff:.0f}ms longer** on average ({failure_latency:.0f}ms vs {success_latency:.0f}ms). "
                        response_text += f"Failed transactions are **{latency_ratio:.1f}x slower** than successful ones.\n\n"
                    
                    # Comparison 2: Peak Hours vs Non-Peak
                    if 'is_peak_hour' in df_comp.columns:
                        peak_failures = df_comp[(df_comp['is_peak_hour'] == True) & (df_comp['transaction_status'] == 'Failure')]
                        non_peak_failures = df_comp[(df_comp['is_peak_hour'] == False) & (df_comp['transaction_status'] == 'Failure')]
                        peak_total = len(df_comp[df_comp['is_peak_hour'] == True])
                        non_peak_total = len(df_comp[df_comp['is_peak_hour'] == False])
                        
                        peak_rate = (len(peak_failures) / peak_total * 100) if peak_total > 0 else 0
                        non_peak_rate = (len(non_peak_failures) / non_peak_total * 100) if non_peak_total > 0 else 0
                        
                        response_text += f"**🕐 Peak Hours Analysis:**\n"
                        if peak_rate > non_peak_rate:
                            diff_pct = peak_rate - non_peak_rate
                            response_text += f"Peak hours (9 AM - 6 PM) have **{diff_pct:.1f}% higher** failure rate ({peak_rate:.1f}%) compared to non-peak hours ({non_peak_rate:.1f}%). "
                            response_text += f"System is under more stress during business hours.\n\n"
                        else:
                            diff_pct = non_peak_rate - peak_rate
                            response_text += f"Non-peak hours have **{diff_pct:.1f}% higher** failure rate ({non_peak_rate:.1f}%) compared to peak hours ({peak_rate:.1f}%). "
                            response_text += f"Off-hours issues may need investigation.\n\n"
                    
                    # Comparison 3: Failures by Network
                    if 'network_type' in df_comp.columns:
                        network_failures = df_comp[df_comp['transaction_status'] == 'Failure'].groupby('network_type').size()
                        network_totals = df_comp.groupby('network_type').size()
                        network_rates = (network_failures / network_totals * 100).sort_values(ascending=False)
                        
                        response_text += f"**📡 Network Comparison:**\n"
                        worst_network = network_rates.index[0]
                        best_network = network_rates.index[-1]
                        response_text += f"**{worst_network}** has the highest failure rate (**{network_rates[worst_network]:.1f}%**), "
                        response_text += f"while **{best_network}** performs best (**{network_rates[best_network]:.1f}%**). "
                        diff = network_rates[worst_network] - network_rates[best_network]
                        response_text += f"That's a **{diff:.1f}% difference**.\n\n"
                    
                    # Comparison 4: Weekday vs Weekend
                    if 'is_weekend' in df_comp.columns:
                        weekend_failures = df_comp[(df_comp['is_weekend'] == True) & (df_comp['transaction_status'] == 'Failure')]
                        weekday_failures = df_comp[(df_comp['is_weekend'] == False) & (df_comp['transaction_status'] == 'Failure')]
                        weekend_total = len(df_comp[df_comp['is_weekend'] == True])
                        weekday_total = len(df_comp[df_comp['is_weekend'] == False])
                        
                        weekend_rate = (len(weekend_failures) / weekend_total * 100) if weekend_total > 0 else 0
                        weekday_rate = (len(weekday_failures) / weekday_total * 100) if weekday_total > 0 else 0
                        
                        response_text += f"**📅 Weekend vs Weekday:**\n"
                        if weekend_rate > weekday_rate:
                            ratio = weekend_rate / weekday_rate if weekday_rate > 0 else 0
                            response_text += f"Weekends show **{ratio:.1f}x higher** failure rate ({weekend_rate:.1f}%) compared to weekdays ({weekday_rate:.1f}%). "
                            response_text += f"Weekend infrastructure may need scaling or maintenance schedules should be reviewed.\n"
                        else:
                            ratio = weekday_rate / weekend_rate if weekend_rate > 0 else 0
                            response_text += f"Weekdays show **{ratio:.1f}x higher** failure rate ({weekday_rate:.1f}%) compared to weekends ({weekend_rate:.1f}%). "
                            response_text += f"Business day traffic is causing more failures.\n"
                    
                    question_type = "comparative_analysis"
                else:
                    # Provide general system summary
                    metrics = MetricsCalculator.calculate_all_metrics(df)
                    explanation = explainability_engine.explain_system_health({
                        'total_transactions': len(df),
                        'metrics': metrics,
                        'question': request.question
                    })
                    response_text = explanation if explanation else processor.process(request.question)['response']
        
        # ===== STEP 7: RETURN RESPONSE =====
        processing_time = time.time() - start_time
        log_request(start_time, success=True)
        
        return QuestionResponse(
            response=response_text,
            success=True,
            processing_time=round(processing_time, 3),
            question_type=question_type,
            timestamp=str(time.time()),
            explanation_why=explanation_why
        )
    
    except Exception as e:
        import traceback
        print(f"Error in auto-routing: {e}")
        print(traceback.format_exc())
        
        # Fallback: Use processor
        try:
            result = processor.process(request.question)
            log_request(start_time, success=True)
            return QuestionResponse(
                response=result['response'],
                success=result['success'],
                processing_time=round(time.time() - start_time, 3),
                question_type="fallback",
                timestamp=str(time.time()),
                explanation_why=result.get('explanation_why')
            )
        except:
            log_request(start_time, success=False)
            raise HTTPException(
                status_code=500,
                detail=f"Error processing question: {str(e)}"
            )


@app.get("/api/analytics", response_model=AnalyticsResponse, tags=["Analytics"])
async def get_analytics():
    """
    Get current analytics and statistics
    
    Returns:
    - Total questions processed
    - Total responses sent
    - Average question length
    - Top words used
    """
    stats = analytics.get_stats()
    
    return AnalyticsResponse(
        total_questions_processed=stats['total_questions_processed'],
        total_responses_sent=stats['total_responses_sent'],
        average_question_length=stats['average_question_length'],
        total_characters_processed=stats['total_characters_processed'],
        top_words=stats['top_words']
    )


@app.get("/api/recent", tags=["Analytics"])
async def get_recent_questions(limit: int = 10):
    """
    Get recent questions and responses
    
    - **limit**: Number of recent questions to retrieve (default: 10)
    """
    
    if limit < 1 or limit > 100:
        raise HTTPException(
            status_code=400,
            detail="Limit must be between 1 and 100"
        )
    
    recent = analytics.get_recent_questions(limit)
    
    return {
        "count": len(recent),
        "questions": recent
    }


@app.get("/api/stats", tags=["Analytics"])
async def get_detailed_stats():
    """Get detailed statistics about the backend"""
    stats = analytics.get_stats()
    
    return {
        "summary": stats,
        "server": {
            "host": HOST,
            "port": PORT,
            "debug": DEBUG
        },
        "uptime_info": "Server is running and processing requests"
    }


@app.post("/api/feedback", tags=["Chat"])
async def submit_feedback(feedback: dict):
    """
    Submit feedback about a response
    
    - **question**: The original question
    - **response**: The given response
    - **rating**: Rating from 1-5
    - **comment**: Optional feedback comment
    """
    try:
        # You could store this feedback for improvement
        return {
            "status": "received",
            "message": "Thank you for your feedback!"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Error storing feedback"
        )


@app.post("/api/nlp/understand", tags=["NLP"])
async def understand_query(request: QuestionRequest):
    """
    Perform NLP analysis on a query without generating a response
    
    - **question**: The user's query
    
    Returns:
    - Intent classification
    - Entity extraction
    - Time references
    - Key metrics
    """
    from nlp_layer import nlp_engine
    
    if not request.question or len(request.question.strip()) == 0:
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty"
        )
    
    try:
        nlp_result = nlp_engine.process(request.question)
        
        return {
            "query": request.question,
            "understanding": nlp_result.to_dict(),
            "processing_method": nlp_result.processing_method,
            "success": True
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing query: {str(e)}"
        )


@app.get("/api/nlp/capabilities", tags=["NLP"])
async def nlp_capabilities():
    """Get NLP engine capabilities and configuration"""
    from nlp_layer import nlp_engine
    from intent_classifier import IntentClassifier
    
    classifier = IntentClassifier()
    
    return {
        "engine": "NLP Layer",
        "version": "1.0",
        "processing_method": "rule-based" if not nlp_engine.use_llm else "llm",
        "supported_intents": [
            "trend_analysis",
            "comparison",
            "failure_analysis",
            "performance_analysis",
            "root_cause_analysis",
            "forecasting",
            "summary",
            "anomaly_detection",
            "distribution_analysis",
            "correlation_analysis"
        ],
        "supported_metrics": [
            "latency", "throughput", "cpu_usage", "memory_usage", "disk_usage",
            "error_rate", "availability", "success_rate", "revenue", "users",
            "conversion", "churn"
        ],
        "supported_components": [
            "database", "api", "frontend", "backend", "cache", "queue", "network"
        ],
        "time_references": [
            "today", "yesterday", "last week", "last weekend", "last month",
            "past 24 hours", "past week", "past month"
        ],
        "features": [
            "Intent classification",
            "Entity extraction",
            "Time reference detection",
            "Metric identification",
            "Component recognition",
            "Comparison detection",
            "Context building"
        ]
    }


@app.post("/api/nlp/test", tags=["NLP"])
async def test_nlp_query(request: QuestionRequest):
    """
    Test NLP understanding with example and explanation
    Useful for debugging and understanding what the NLP layer understands
    """
    from nlp_layer import nlp_engine, QueryUnderstanding
    from intent_classifier import IntentClassifier
    
    if not request.question or len(request.question.strip()) == 0:
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty"
        )
    
    try:
        nlp_result = nlp_engine.process(request.question)
        classifier = IntentClassifier()
        
        return {
            "query": request.question,
            "nlp_understanding": {
                "intent": nlp_result.intent,
                "intent_description": classifier.get_intent_description(nlp_result.intent),
                "confidence": f"{nlp_result.confidence * 100:.1f}%",
                "entities": nlp_result.entities,
                "time_reference": nlp_result.time_reference,
                "metrics": nlp_result.metrics,
                "context": nlp_result.context,
                "suggested_followups": classifier.get_followup_questions(nlp_result.intent),
                "suggested_actions": nlp_result.context.get('suggested_actions', [])
            },
            "human_explanation": QueryUnderstanding.get_nlp_explanation(nlp_result),
            "processing_method": nlp_result.processing_method,
            "success": True
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing query: {str(e)}"
        )


# ===== Analytics Endpoints =====

def _ensure_analytics_engine_loaded():
    """Auto-load UPI transaction data into analytics engine if not already loaded"""
    from analytics_engine import analytics_engine
    if analytics_engine.transactions_df is None:
        df = load_transaction_data()
        analytics_engine.load_data(df)
    return analytics_engine


@app.get("/api/analytics/status", tags=["Analytics"])
async def analytics_status():
    """Get status of analytics engine"""
    from analytics_engine import analytics_engine
    
    return {
        "status": "ready",
        "engine": "Pandas-based in-memory analytics",
        "data_loaded": analytics_engine.transactions_df is not None,
        "last_loaded": str(analytics_engine.last_loaded) if analytics_engine.last_loaded else None,
        "data_records": len(analytics_engine.transactions_df) if analytics_engine.transactions_df is not None else 0,
        "processing_method": "No SQL - Pure Python",
        "available_operations": [
            "trend_analysis",
            "comparison",
            "aggregation",
            "anomaly_detection",
            "failure_analysis",
            "performance_metrics"
        ]
    }


@app.post("/api/analytics/load-sample-data", tags=["Analytics"])
async def load_sample_data():
    """
    Load real UPI transaction data from CSV into analytics engine
    """
    try:
        from analytics_engine import analytics_engine
        
        # Load real UPI transaction data from CSV
        transactions_df = load_transaction_data()
        analytics_engine.load_data(transactions_df)
        
        return {
            "status": "success",
            "message": f"Loaded {len(transactions_df):,} real UPI transactions from CSV",
            "data_summary": {
                "total_transactions": len(transactions_df),
                "total_failures": int(len(transactions_df[transactions_df['transaction_status'] == 'Failure'])),
                "failure_rate": round((len(transactions_df[transactions_df['transaction_status'] == 'Failure']) / len(transactions_df)) * 100, 2),
                "date_range": f"{transactions_df['transaction_time'].min()} to {transactions_df['transaction_time'].max()}",
                "source": "upi_transactions_2024 (1).csv"
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error loading data: {str(e)}"
        )


@app.post("/api/analytics/trend-analysis", tags=["Analytics"])
async def analyze_trend(metric: str = "latency_ms", bucket: str = "D"):
    """
    Analyze trend for a metric
    
    Args:
        metric: Metric to analyze (latency_ms, success, etc.)
        bucket: Time bucket (H=hourly, D=daily, W=weekly, M=monthly)
    """
    try:
        from analytics_engine import analytics_engine
        
        if analytics_engine.transactions_df is None:
            analytics_engine.transactions_df = load_transaction_data()
        
        trend_df = analytics_engine.calculate_trend(analytics_engine.transactions_df, metric, bucket)
        
        return {
            "status": "success",
            "metric": metric,
            "bucket": bucket,
            "data": trend_df.to_dict('records'),
            "summary": {
                "current_value": trend_df[metric].iloc[-1] if metric in trend_df.columns else None,
                "trend": analytics_engine.detect_trend_direction(trend_df[metric].dropna().tolist()),
                "average": trend_df[metric].mean() if metric in trend_df.columns else None,
                "min": trend_df[metric].min() if metric in trend_df.columns else None,
                "max": trend_df[metric].max() if metric in trend_df.columns else None
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing trend: {str(e)}")


@app.post("/api/analytics/compare-periods", tags=["Analytics"])
async def compare_periods(metric: str = "latency_ms", period1_days: int = 7, period2_days: int = 7):
    """
    Compare a metric between two recent periods
    
    Args:
        metric: Metric to compare
        period1_days: Days in first period (most recent)
        period2_days: Days in second period (before first period)
    """
    try:
        from analytics_engine import analytics_engine
        from datetime import datetime, timedelta
        
        if analytics_engine.transactions_df is None:
            analytics_engine.transactions_df = load_transaction_data()
        
        now = datetime.now()
        
        # Recent period
        p1_end = now
        p1_start = now - timedelta(days=period1_days)
        
        # Previous period
        p2_end = p1_start
        p2_start = p2_end - timedelta(days=period2_days)
        
        comparison = analytics_engine.compare_periods(
            analytics_engine.transactions_df,
            metric,
            p2_start, p2_end,
            p1_start, p1_end
        )
        
        return {
            "status": "success",
            "metric": metric,
            "periods": {
                "period1": {
                    "start": str(p1_start),
                    "end": str(p1_end),
                    "days": period1_days
                },
                "period2": {
                    "start": str(p2_start),
                    "end": str(p2_end),
                    "days": period2_days
                }
            },
            "comparison": comparison
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error comparing periods: {str(e)}")


@app.post("/api/analytics/failure-analysis", tags=["Analytics"])
async def failure_analysis_endpoint():
    """Analyze failures in the data"""
    try:
        from analytics_engine import analytics_engine
        
        if analytics_engine.transactions_df is None:
            analytics_engine.transactions_df = load_transaction_data()
        
        failure_rates = analytics_engine.failure_rate_analysis(analytics_engine.transactions_df)
        root_causes = analytics_engine.failure_root_causes(analytics_engine.transactions_df)
        
        return {
            "status": "success",
            "failure_trend": failure_rates.to_dict('records'),
            "root_causes": root_causes,
            "total_failures": len(analytics_engine.filter_failures(analytics_engine.transactions_df)),
            "failure_rate": (1 - analytics_engine.transactions_df['success'].mean()) * 100
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing failures: {str(e)}")


@app.post("/api/analytics/distribution", tags=["Analytics"])
async def distribution_analysis(metric: str = "latency_ms"):
    """Analyze distribution of a metric"""
    try:
        from analytics_engine import analytics_engine
        
        if analytics_engine.transactions_df is None:
            analytics_engine.transactions_df = load_transaction_data()
        
        distribution = analytics_engine.distribution_analysis(analytics_engine.transactions_df, metric)
        
        return {
            "status": "success",
            "metric": metric,
            "distribution": distribution
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing distribution: {str(e)}")


@app.post("/api/analytics/performance-metrics", tags=["Analytics"])
async def get_performance_metrics():
    """Calculate key performance metrics"""
    try:
        from metrics_calculator import metrics_calculator
        from analytics_engine import analytics_engine
        
        if analytics_engine.transactions_df is None:
            analytics_engine.transactions_df = load_transaction_data()
        
        error_rate = metrics_calculator.calculate_error_rate(analytics_engine.transactions_df)
        latency_percentiles = metrics_calculator.calculate_latency_percentiles(analytics_engine.transactions_df)
        availability = metrics_calculator.calculate_availability(analytics_engine.transactions_df)
        apdex = metrics_calculator.calculate_apdex(analytics_engine.transactions_df)
        mtbf = metrics_calculator.calculate_mtbf(analytics_engine.transactions_df)
        mttr = metrics_calculator.calculate_mttr(analytics_engine.transactions_df)
        
        return {
            "status": "success",
            "metrics": {
                "error_rate": error_rate.to_dict('records') if error_rate is not None else [],
                "latency_percentiles": latency_percentiles.to_dict('records') if latency_percentiles is not None else [],
                "availability": availability.to_dict('records') if availability is not None else [],
                "apdex_score": apdex.to_dict('records') if apdex is not None else [],
                "mtbf_seconds": mtbf,
                "mttr_seconds": mttr
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating metrics: {str(e)}")


@app.post("/api/analytics/anomalies", tags=["Analytics"])
async def detect_anomalies(metric: str = "latency_ms", threshold_std: float = 2.0):
    """Detect anomalies in a metric"""
    try:
        from analytics_engine import analytics_engine
        
        if analytics_engine.transactions_df is None:
            analytics_engine.transactions_df = load_transaction_data()
        
        anomalies_df = analytics_engine.detect_anomalies(
            analytics_engine.transactions_df,
            metric,
            threshold_std
        )
        
        anomaly_records = anomalies_df[anomalies_df['is_anomaly']].to_dict('records')
        
        return {
            "status": "success",
            "metric": metric,
            "threshold_std": threshold_std,
            "anomaly_count": len(anomaly_records),
            "anomalies": anomaly_records[:100]  # Return first 100
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error detecting anomalies: {str(e)}")


@app.post("/api/analytics/weekly-pattern", tags=["Analytics"])
async def analyze_weekly_pattern(metric: str = "latency_ms"):
    """Analyze how a metric varies by day of week"""
    try:
        from trend_analyzer import trend_analyzer
        from analytics_engine import analytics_engine
        
        if analytics_engine.transactions_df is None:
            analytics_engine.transactions_df = load_transaction_data()
        
        pattern = trend_analyzer.analyze_weekly_pattern(analytics_engine.transactions_df, metric)
        
        return {
            "status": "success",
            "metric": metric,
            "pattern": pattern
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing weekly pattern: {str(e)}")


# ===== Weekend Analysis Endpoints =====

@app.post("/api/analytics/weekend-analysis", tags=["Weekend Analysis"])
async def weekend_analysis():
    """
    Complete weekend vs weekday analysis
    
    Filter → weekend data
    Compare → weekday vs weekend failure rates
    Calculate → root causes by error code
    """
    try:
        from weekend_analyzer import WeekendAnalyzer
        from analytics_engine import analytics_engine
        
        if analytics_engine.transactions_df is None:
            analytics_engine.transactions_df = load_transaction_data()
        
        report = WeekendAnalyzer.detailed_weekend_failure_report(analytics_engine.transactions_df)
        
        return {
            "status": "success",
            "analysis_type": "weekend_vs_weekday_failure_analysis",
            "query_pattern": [
                "Filter → weekend data",
                "Compare → weekday vs weekend failure rates",
                "Calculate → root causes by error code"
            ],
            "report": report
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in weekend analysis: {str(e)}")


@app.post("/api/analytics/filter-weekend", tags=["Weekend Analysis"])
async def filter_weekend_data():
    """Filter and return only weekend transaction data"""
    try:
        from weekend_analyzer import WeekendAnalyzer
        from analytics_engine import analytics_engine
        
        if analytics_engine.transactions_df is None:
            analytics_engine.transactions_df = load_transaction_data()
        
        weekend_df = WeekendAnalyzer.filter_weekend_data(analytics_engine.transactions_df)
        
        return {
            "status": "success",
            "operation": "Filter → weekend data",
            "total_weekend_transactions": len(weekend_df),
            "date_range": {
                "start": str(weekend_df['timestamp'].min()),
                "end": str(weekend_df['timestamp'].max())
            },
            "weekend_summary": {
                "total": len(weekend_df),
                "by_type": weekend_df['type'].value_counts().to_dict() if 'type' in weekend_df.columns else {},
                "by_component": weekend_df['component'].value_counts().to_dict() if 'component' in weekend_df.columns else {},
                "success_rate": (weekend_df['success'].mean() * 100) if 'success' in weekend_df.columns else None
            },
            "sample_records": weekend_df.head(10).to_dict('records')
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error filtering weekend data: {str(e)}")


@app.post("/api/analytics/compare-failure-rates", tags=["Weekend Analysis"])
async def compare_failure_rates():
    """Compare failure rates between weekend and weekday"""
    try:
        from weekend_analyzer import WeekendAnalyzer
        from analytics_engine import analytics_engine
        
        if analytics_engine.transactions_df is None:
            analytics_engine.transactions_df = load_transaction_data()
        
        comparison = WeekendAnalyzer.compare_failure_rates(analytics_engine.transactions_df)
        
        # Generate human-readable explanation
        explanation = explainability_engine.explain_failure_comparison(comparison)
        
        return {
            "status": "success",
            "operation": "Compare → weekday vs weekend failure rates",
            "comparison": comparison,
            "explanation": explanation,
            "visualization_data": {
                "weekend_failure_rate": comparison['weekend']['failure_rate_percent'],
                "weekday_failure_rate": comparison['weekday']['failure_rate_percent'],
                "difference": comparison['comparison']['absolute_difference_percent'],
                "ratio": comparison['comparison']['weekend_vs_weekday_ratio']
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error comparing failure rates: {str(e)}")


@app.post("/api/analytics/root-causes", tags=["Weekend Analysis"])
async def analyze_root_causes():
    """Analyze root causes of failures with breakdown by error code"""
    try:
        from weekend_analyzer import WeekendAnalyzer
        from analytics_engine import analytics_engine
        
        if analytics_engine.transactions_df is None:
            analytics_engine.transactions_df = load_transaction_data()
        
        causes = WeekendAnalyzer.analyze_weekend_vs_weekday_causes(analytics_engine.transactions_df)
        
        # Generate human-readable explanation
        explanation = explainability_engine.explain_root_causes(causes)
        
        return {
            "status": "success",
            "operation": "Calculate → root causes by error code",
            "root_cause_analysis": causes,
            "explanation": explanation,
            "summary": {
                "weekend_top_error": causes['weekend']['top_cause'],
                "weekday_top_error": causes['weekday']['top_cause'],
                "weekend_specific_errors": causes['differences']['errors_unique_to_weekend'],
                "weekday_specific_errors": causes['differences']['errors_unique_to_weekday']
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing root causes: {str(e)}")


@app.post("/api/analytics/weekend-insights", tags=["Weekend Analysis"])
async def weekend_insights():
    """Get actionable insights from weekend analysis"""
    try:
        from weekend_analyzer import WeekendAnalyzer
        from analytics_engine import analytics_engine
        
        if analytics_engine.transactions_df is None:
            analytics_engine.transactions_df = load_transaction_data()
        
        report = WeekendAnalyzer.detailed_weekend_failure_report(analytics_engine.transactions_df)
        
        return {
            "status": "success",
            "insights": report.get('insights', []),
            "summary": report.get('summary', {}),
            "recommended_actions": get_recommended_actions(report),
            "full_report": report
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating insights: {str(e)}")


# Error handling (commented out as it's causing issues)
# @app.exception_handler(404)
# async def not_found_handler(request, exc):
#     return {
#         "error": "Endpoint not found",
#         "available_endpoints": [
#             "/api/ask",
#             "/api/analytics",
#             "/api/recent",
#             "/api/stats",
#             "/health"
#         ]
#     }


# Run the server
if __name__ == "__main__":
    import uvicorn
    
    print(f"""
    🚀 Conversational Leadership Analytics Starting...
    📍 Server: http://{HOST}:{PORT}
    📚 API Docs: http://{HOST}:{PORT}/docs
    🔌 WebSocket: ws://{HOST}:{PORT}
    """)
    
    uvicorn.run(
        app,
        host=HOST,
        port=PORT,
        reload=DEBUG,
        log_level="info"
    )
