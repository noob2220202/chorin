from telegram import Update
from telegram.ext import ContextTypes
import config
import store.sessions as sessions


async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.data != "buy_start":
        await query.answer()
        return

    await query.answer()
    user = query.from_user
    session = sessions.get_or_create_telegram_session(user.id, user.to_dict())

    welcome = (
        "안녕하세요! 😊 구매 문의를 도와드리겠습니다.\n\n"
        "원하시는 상품명, 사이즈, 수량을 알려주시면 빠르게 안내해 드릴게요! 🛍️"
    )
    await context.bot.send_message(chat_id=user.id, text=welcome)

    sessions.add_message(session["id"], "봇", welcome, is_admin=True)
    _notify_admin(session, "봇", welcome, is_admin=True)


async def handle_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg or not msg.text:
        return

    user = msg.from_user
    session = sessions.get_or_create_telegram_session(user.id, user.to_dict())
    sessions.add_message(session["id"], user.first_name or "사용자", msg.text, is_admin=False)

    _notify_admin(session, user.first_name or "사용자", msg.text, is_admin=False)

    # 관리자 Telegram으로 포워드 (백업용)
    if config.ADMIN_CHAT_ID:
        try:
            await context.bot.forward_message(
                chat_id=int(config.ADMIN_CHAT_ID),
                from_chat_id=msg.chat_id,
                message_id=msg.message_id,
            )
        except Exception:
            pass


def _notify_admin(session: dict, sender: str, text: str, is_admin: bool):
    """Socket.io로 어드민 패널에 메시지 전달."""
    try:
        from web.app import socketio
        socketio.emit(
            "chat:message",
            {
                "session_id": session["id"],
                "session": _session_summary(session),
                "sender": sender,
                "text": text,
                "is_admin": is_admin,
                "type": session["type"],
            },
            room="admin-room",
        )
        if not is_admin:
            socketio.emit("new:session", _session_summary(session), room="admin-room")
    except Exception:
        pass


def _session_summary(session: dict) -> dict:
    return {
        "id": session["id"],
        "type": session["type"],
        "user_name": session["user_name"],
        "last_activity": session["last_activity"],
        "unread": session.get("unread", 0),
    }
