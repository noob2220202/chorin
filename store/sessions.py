import json
import os
import threading
import time
import uuid
from datetime import datetime
from typing import Optional

_sessions: dict = {}
_lock = threading.Lock()
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DATA_FILE = os.path.join(_BASE_DIR, "data", "sessions.json")
_save_timer: Optional[threading.Timer] = None


def _load():
    os.makedirs("data", exist_ok=True)
    if os.path.exists(_DATA_FILE):
        try:
            with open(_DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            with _lock:
                _sessions.update(data)
        except Exception:
            pass


def _save_now():
    os.makedirs("data", exist_ok=True)
    with _lock:
        snapshot = dict(_sessions)
    with open(_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False, default=str)


def _schedule_save():
    global _save_timer
    if _save_timer:
        _save_timer.cancel()
    _save_timer = threading.Timer(0.5, _save_now)
    _save_timer.daemon = True
    _save_timer.start()


def _now_iso() -> str:
    return datetime.utcnow().isoformat()


def _make_session(session_type: str, user_id: str, user_name: str, session_id: Optional[str] = None) -> dict:
    sid = session_id or str(uuid.uuid4())
    return {
        "id": sid,
        "type": session_type,
        "user_id": user_id,
        "user_name": user_name,
        "messages": [],
        "created_at": _now_iso(),
        "last_activity": _now_iso(),
        "unread": 0,
    }


def get_or_create_website_session(session_id: str, user_name: str = "손님") -> dict:
    with _lock:
        if session_id not in _sessions:
            _sessions[session_id] = _make_session("website", session_id, user_name, session_id)
        else:
            _sessions[session_id]["user_name"] = user_name
    _schedule_save()
    return _sessions[session_id]


def get_or_create_telegram_session(tg_user_id: int, tg_user: dict) -> dict:
    sid = str(tg_user_id)
    name = tg_user.get("first_name", "")
    if tg_user.get("last_name"):
        name += f" {tg_user['last_name']}"
    name = name.strip() or f"user_{sid}"
    with _lock:
        if sid not in _sessions:
            _sessions[sid] = _make_session("telegram", sid, name, sid)
        else:
            _sessions[sid]["user_name"] = name
    _schedule_save()
    return _sessions[sid]


def add_message(session_id: str, sender: str, text: str, is_admin: bool = False):
    with _lock:
        if session_id not in _sessions:
            return
        _sessions[session_id]["messages"].append({
            "sender": sender,
            "text": text,
            "is_admin": is_admin,
            "timestamp": _now_iso(),
        })
        _sessions[session_id]["last_activity"] = _now_iso()
        if not is_admin:
            _sessions[session_id]["unread"] = _sessions[session_id].get("unread", 0) + 1
    _schedule_save()


def mark_read(session_id: str):
    with _lock:
        if session_id in _sessions:
            _sessions[session_id]["unread"] = 0
    _schedule_save()


def get_session(session_id: str) -> Optional[dict]:
    with _lock:
        return _sessions.get(session_id)


def all_sessions() -> list:
    with _lock:
        return sorted(_sessions.values(), key=lambda s: s["last_activity"], reverse=True)


_load()
