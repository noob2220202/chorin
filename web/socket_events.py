import asyncio
from flask_socketio import SocketIO, join_room, emit
import store.sessions as sessions
import state


def register_events(socketio: SocketIO):

    @socketio.on("admin:join")
    def on_admin_join():
        join_room("admin-room")
        all_s = sessions.all_sessions()
        emit("sessions:list", all_s)

    @socketio.on("admin:read")
    def on_admin_read(data):
        session_id = data.get("session_id")
        if session_id:
            sessions.mark_read(session_id)

    @socketio.on("admin:reply")
    def on_admin_reply(data):
        session_id = data.get("session_id")
        text = (data.get("text") or "").strip()
        if not session_id or not text:
            return

        session = sessions.get_session(session_id)
        if not session:
            return

        sessions.add_message(session_id, "관리자", text, is_admin=True)

        if session["type"] == "telegram":
            if state.ptb_app and state.bot_loop:
                asyncio.run_coroutine_threadsafe(
                    state.ptb_app.bot.send_message(chat_id=int(session["user_id"]), text=text),
                    state.bot_loop,
                )
        else:
            # 웹 위젯 고객에게 전달
            socketio.emit("customer:reply", {"text": text, "sender": "관리자"}, room=f"chat-{session_id}")

        # 어드민 패널에도 에코
        socketio.emit(
            "chat:message",
            {
                "session_id": session_id,
                "sender": "관리자",
                "text": text,
                "is_admin": True,
                "type": session["type"],
            },
            room="admin-room",
        )

    @socketio.on("customer:join")
    def on_customer_join(data):
        session_id = data.get("session_id")
        user_name = data.get("user_name", "손님")
        if not session_id:
            return

        join_room(f"chat-{session_id}")
        session = sessions.get_or_create_website_session(session_id, user_name)

        socketio.emit(
            "new:session",
            {
                "id": session["id"],
                "type": session["type"],
                "user_name": session["user_name"],
                "last_activity": session["last_activity"],
                "unread": session.get("unread", 0),
            },
            room="admin-room",
        )

        # 이전 히스토리 전송
        emit("chat:history", session.get("messages", []))

    @socketio.on("customer:message")
    def on_customer_message(data):
        session_id = data.get("session_id")
        text = (data.get("text") or "").strip()
        if not session_id or not text:
            return

        session = sessions.get_session(session_id)
        if not session:
            return

        sender = session.get("user_name", "손님")
        sessions.add_message(session_id, sender, text, is_admin=False)

        socketio.emit(
            "chat:message",
            {
                "session_id": session_id,
                "session": {
                    "id": session["id"],
                    "type": session["type"],
                    "user_name": session["user_name"],
                    "last_activity": session["last_activity"],
                    "unread": session.get("unread", 0),
                },
                "sender": sender,
                "text": text,
                "is_admin": False,
                "type": session["type"],
            },
            room="admin-room",
        )
