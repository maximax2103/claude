"""
Alisha Psychology Bot — FastAPI Backend
Serves the Web App and provides API endpoints.
"""
import os
import json
import hmac
import hashlib
import time
from datetime import date, datetime, timedelta
from typing import Optional
from urllib.parse import unquote

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Alisha API")

# CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── CONFIG ───────────────────────────────────────────────────────────────────
SUPABASE_URL  = os.getenv("SUPABASE_URL", "https://hwqyzftaevrwxtblszoz.supabase.co")
SUPABASE_KEY  = os.getenv("SUPABASE_SERVICE_KEY", "")  # service role key
SUPABASE_ANON = os.getenv("SUPABASE_ANON_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imh3cXl6ZnRhZXZyd3h0Ymxzem96Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzM0ODMwMTcsImV4cCI6MjA4OTA1OTAxN30.9zZgfLRF6LeYinGqfMQyo8NRdwi_fzwyIWk44dOEeMc")
BOT_TOKEN     = os.getenv("BOT_TOKEN", "")

# Use service key if available, else anon
SB_KEY = SUPABASE_KEY or SUPABASE_ANON

# ─── SUPABASE HELPERS ─────────────────────────────────────────────────────────
def sb_headers():
    return {
        "apikey": SB_KEY,
        "Authorization": f"Bearer {SB_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }

async def sb_get(path: str, params: dict = None):
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{SUPABASE_URL}/rest/v1{path}", headers=sb_headers(), params=params)
        r.raise_for_status()
        return r.json()

async def sb_post(path: str, data: dict):
    async with httpx.AsyncClient() as client:
        r = await client.post(f"{SUPABASE_URL}/rest/v1{path}", headers=sb_headers(), json=data)
        r.raise_for_status()
        return r.json()

async def sb_patch(path: str, data: dict, params: dict = None):
    async with httpx.AsyncClient() as client:
        r = await client.patch(f"{SUPABASE_URL}/rest/v1{path}", headers=sb_headers(), json=data, params=params)
        r.raise_for_status()
        return r.json()

# ─── TELEGRAM INIT DATA VALIDATION ───────────────────────────────────────────
def validate_telegram_init_data(init_data: str) -> bool:
    """Validate Telegram Web App init data."""
    if not BOT_TOKEN or not init_data:
        return True  # Skip validation in dev mode
    try:
        parsed = dict(x.split("=", 1) for x in init_data.split("&"))
        received_hash = parsed.pop("hash", "")
        check_string = "\n".join(f"{k}={unquote(v)}" for k, v in sorted(parsed.items()))
        secret = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
        expected = hmac.new(secret, check_string.encode(), hashlib.sha256).hexdigest()
        return hmac.compare_digest(received_hash, expected)
    except Exception:
        return True  # Allow in dev

# ─── MODELS ───────────────────────────────────────────────────────────────────
class UpsertUserRequest(BaseModel):
    telegram_id: int
    username: Optional[str] = None
    display_name: str = "Друг"

class StartSessionRequest(BaseModel):
    user_id: int

class Answer(BaseModel):
    question_id: int
    value_numeric: Optional[float] = None
    value_text: Optional[str] = None

class CompleteSessionRequest(BaseModel):
    session_id: int
    answers: list[Answer]
    scores: dict

class CheckAchievementsRequest(BaseModel):
    user_id: int

# ─── ACHIEVEMENTS DEFINITIONS ─────────────────────────────────────────────────
ACHIEVEMENTS = [
    {"id": 1, "name": "Первый шаг",          "icon": "🌱", "req_type": "sessions_total", "req_value": 1},
    {"id": 2, "name": "Открытая душа",        "icon": "🌺", "req_type": "sessions_total", "req_value": 5},
    {"id": 3, "name": "Путь к свету",         "icon": "✨", "req_type": "sessions_total", "req_value": 10},
    {"id": 4, "name": "Неделя осознанности",  "icon": "🧘", "req_type": "streak_days",    "req_value": 7},
    {"id": 5, "name": "Кристальное сердце",   "icon": "💎", "req_type": "streak_days",    "req_value": 14},
    {"id": 6, "name": "Несломимый дух",       "icon": "🏆", "req_type": "streak_days",    "req_value": 30},
    {"id": 7, "name": "Мастер сна",           "icon": "🌙", "req_type": "score_sleep",    "req_value": 80},
    {"id": 8, "name": "Эмоц. интеллект",      "icon": "🧠", "req_type": "score_emotions", "req_value": 80},
    {"id": 9, "name": "Гармония",             "icon": "☯️", "req_type": "score_wellbeing","req_value": 75},
    {"id": 10,"name": "Здоровые привычки",    "icon": "🌿", "req_type": "score_habits",   "req_value": 80},
]

# ─── API ROUTES ───────────────────────────────────────────────────────────────

@app.post("/api/users/upsert")
async def upsert_user(req: UpsertUserRequest):
    """Get or create user by Telegram ID."""
    # Check if user exists
    existing = await sb_get("/users", {"telegram_id": f"eq.{req.telegram_id}", "limit": "1"})

    if existing:
        user = existing[0]
        # Update display_name if changed
        if req.display_name and req.display_name != user.get("display_name"):
            await sb_patch("/users", {"display_name": req.display_name}, {"id": f"eq.{user['id']}"})
            user["display_name"] = req.display_name
        return user
    else:
        # Create new user
        new_user = await sb_post("/users", {
            "telegram_id": req.telegram_id,
            "username": req.username,
            "display_name": req.display_name,
        })
        return new_user[0] if isinstance(new_user, list) else new_user


@app.post("/api/sessions/start")
async def start_session(req: StartSessionRequest):
    """Create a new session."""
    session = await sb_post("/sessions", {"user_id": req.user_id})
    return session[0] if isinstance(session, list) else session


@app.post("/api/sessions/complete")
async def complete_session(req: CompleteSessionRequest):
    """Complete session: save answers, scores, update user streak."""
    # Update session
    score_data = {
        "completed_at": datetime.utcnow().isoformat(),
        "score_wellbeing": req.scores.get("wellbeing", 0),
        "score_sleep":     req.scores.get("sleep", 0),
        "score_emotions":  req.scores.get("emotions", 0),
        "score_stress":    req.scores.get("stress", 0),
        "score_habits":    req.scores.get("habits", 0),
        "score_social":    req.scores.get("social", 0),
        "score_selfesteem":req.scores.get("selfesteem", 0),
        "score_purpose":   req.scores.get("purpose", 0),
        "score_physical":  req.scores.get("physical", 0),
    }
    await sb_patch("/sessions", score_data, {"id": f"eq.{req.session_id}"})

    # Save answers
    session = await sb_get("/sessions", {"id": f"eq.{req.session_id}", "limit": "1"})
    if session:
        answers_data = [
            {
                "session_id": req.session_id,
                "question_id": a.question_id,
                "value_numeric": a.value_numeric,
                "value_text": a.value_text,
            }
            for a in req.answers
        ]
        if answers_data:
            await sb_post("/answers", answers_data)

        # Update user stats
        user_id = session[0]["user_id"]
        user_rows = await sb_get("/users", {"id": f"eq.{user_id}", "limit": "1"})
        if user_rows:
            user = user_rows[0]
            today = date.today().isoformat()
            last_date = user.get("last_session_date")
            yesterday = (date.today() - timedelta(days=1)).isoformat()

            new_streak = user.get("streak_days", 0)
            if last_date == today:
                pass  # Same day, no streak change
            elif last_date == yesterday:
                new_streak += 1
            else:
                new_streak = 1

            new_longest = max(user.get("longest_streak", 0), new_streak)
            new_total = (user.get("total_sessions") or 0) + 1

            await sb_patch("/users", {
                "streak_days": new_streak,
                "longest_streak": new_longest,
                "total_sessions": new_total,
                "last_session_at": datetime.utcnow().isoformat(),
                "last_session_date": today,
            }, {"id": f"eq.{user_id}"})

    return {"ok": True}


@app.get("/api/users/{user_id}/stats")
async def get_user_stats(user_id: int):
    """Get user stats with recent sessions."""
    users = await sb_get("/users", {"id": f"eq.{user_id}", "limit": "1"})
    if not users:
        raise HTTPException(404, "User not found")
    user = users[0]

    # Recent sessions
    sessions = await sb_get(
        "/sessions",
        {"user_id": f"eq.{user_id}", "completed_at": "not.is.null",
         "order": "completed_at.desc", "limit": "10"}
    )

    # Format sessions for frontend
    formatted = []
    for s in sessions:
        formatted.append({
            "id": s["id"],
            "completed_at": s["completed_at"],
            "scores": {
                "wellbeing": s.get("score_wellbeing", 0),
                "sleep":     s.get("score_sleep", 0),
                "emotions":  s.get("score_emotions", 0),
                "stress":    s.get("score_stress", 0),
                "habits":    s.get("score_habits", 0),
                "social":    s.get("score_social", 0),
                "selfesteem":s.get("score_selfesteem", 0),
                "purpose":   s.get("score_purpose", 0),
                "physical":  s.get("score_physical", 0),
            }
        })

    last_scores = formatted[0]["scores"] if formatted else None

    return {
        "total_sessions": user.get("total_sessions", 0),
        "streak_days": user.get("streak_days", 0),
        "longest_streak": user.get("longest_streak", 0),
        "sessions": formatted,
        "last_scores": last_scores,
    }


@app.get("/api/users/{user_id}/achievements")
async def get_user_achievements(user_id: int):
    """Get user achievements."""
    earned = await sb_get("/user_achievements", {"user_id": f"eq.{user_id}"})
    return earned or []


@app.post("/api/achievements/check")
async def check_achievements(req: CheckAchievementsRequest):
    """Check and award new achievements."""
    user_id = req.user_id
    users = await sb_get("/users", {"id": f"eq.{user_id}", "limit": "1"})
    if not users:
        return []
    user = users[0]

    # Get last session scores
    sessions = await sb_get(
        "/sessions",
        {"user_id": f"eq.{user_id}", "completed_at": "not.is.null",
         "order": "completed_at.desc", "limit": "1"}
    )
    last_scores = {}
    if sessions:
        s = sessions[0]
        last_scores = {
            "wellbeing": s.get("score_wellbeing", 0),
            "sleep":     s.get("score_sleep", 0),
            "emotions":  s.get("score_emotions", 0),
            "habits":    s.get("score_habits", 0),
        }

    # Get already earned
    earned = await sb_get("/user_achievements", {"user_id": f"eq.{user_id}"})
    earned_ids = {e["achievement_id"] for e in (earned or [])}

    newly_earned = []
    for ach in ACHIEVEMENTS:
        if ach["id"] in earned_ids:
            continue

        earned_it = False
        rt = ach["req_type"]
        rv = ach["req_value"]

        if rt == "sessions_total" and (user.get("total_sessions") or 0) >= rv:
            earned_it = True
        elif rt == "streak_days" and (user.get("streak_days") or 0) >= rv:
            earned_it = True
        elif rt == "score_sleep" and last_scores.get("sleep", 0) >= rv:
            earned_it = True
        elif rt == "score_emotions" and last_scores.get("emotions", 0) >= rv:
            earned_it = True
        elif rt == "score_wellbeing" and last_scores.get("wellbeing", 0) >= rv:
            earned_it = True
        elif rt == "score_habits" and last_scores.get("habits", 0) >= rv:
            earned_it = True

        if earned_it:
            try:
                await sb_post("/user_achievements", {
                    "user_id": user_id,
                    "achievement_id": ach["id"],
                })
                newly_earned.append(ach)
            except Exception:
                pass  # Already exists

    return newly_earned


# ─── ADMIN: USERS LIST ────────────────────────────────────────────────────────
@app.get("/api/admin/users")
async def admin_list_users(limit: int = 100, offset: int = 0):
    """List all users with their IDs, names, Telegram info and session counts.
    Protected: only works if SUPABASE_SERVICE_KEY is set."""
    if not SUPABASE_KEY:
        raise HTTPException(403, "Service key required")
    users = await sb_get("/users", {
        "select": "id,telegram_id,username,display_name,created_at",
        "order": "created_at.desc",
        "limit": str(limit),
        "offset": str(offset),
    })
    # Attach session count per user
    result = []
    for u in (users or []):
        sessions = await sb_get("/sessions", {
            "user_id": f"eq.{u['id']}",
            "completed_at": "not.is.null",
            "select": "id",
        })
        result.append({
            "id":           u["id"],
            "telegram_id":  u.get("telegram_id"),
            "username":     u.get("username"),
            "display_name": u.get("display_name"),
            "sessions":     len(sessions or []),
            "joined":       u.get("created_at", "")[:10],
        })
    return result


# ─── SERVE STATIC FILES ───────────────────────────────────────────────────────
if os.path.isdir("alisha"):
    app.mount("/", StaticFiles(directory="alisha", html=True), name="static")

# ─── RUN ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=False)
