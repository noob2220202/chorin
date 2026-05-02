import asyncio
import os
import uuid
from flask import Blueprint, request, jsonify, send_from_directory, abort
from werkzeug.utils import secure_filename
import config
import state
import store.sessions as sessions

bp = Blueprint("main", __name__)

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}


def _allowed(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@bp.route("/")
def index():
    return send_from_directory(
        os.path.join(os.path.dirname(__file__), "..", "public", "admin"),
        "index.html",
    )


@bp.route("/admin")
def admin():
    return send_from_directory(
        os.path.join(os.path.dirname(__file__), "..", "public", "admin"),
        "index.html",
    )


@bp.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(os.path.abspath(config.UPLOAD_DIR), filename)


@bp.route("/api/sessions")
def api_sessions():
    return jsonify(sessions.all_sessions())


@bp.route("/api/post", methods=["POST"])
def api_post():
    brand = request.form.get("brand", "").strip()
    name = request.form.get("name", "").strip()
    sizes_raw = request.form.get("sizes", "").strip()
    features = request.form.get("features", "").strip()

    if not brand or not name:
        return jsonify({"error": "브랜드와 옷이름은 필수입니다."}), 400

    sizes = [s.strip() for s in sizes_raw.split(",") if s.strip()]

    files = request.files.getlist("photos")
    if not files or not any(f.filename for f in files):
        return jsonify({"error": "사진을 최소 1장 첨부해야 합니다."}), 400

    max_bytes = config.MAX_FILE_SIZE_MB * 1024 * 1024
    photo_paths = []
    for f in files[: config.MAX_FILES_PER_POST]:
        if not f.filename or not _allowed(f.filename):
            continue
        f.seek(0, 2)
        size = f.tell()
        f.seek(0)
        if size > max_bytes:
            return jsonify({"error": f"파일 크기 초과: {f.filename}"}), 400
        ext = secure_filename(f.filename).rsplit('.', 1)[-1].lower()
        fname = f"{uuid.uuid4().hex}.{ext}"
        path = os.path.join(config.UPLOAD_DIR, fname)
        f.save(path)
        photo_paths.append(path)

    if not photo_paths:
        return jsonify({"error": "유효한 이미지 파일이 없습니다."}), 400

    if state.ptb_app is None or state.bot_loop is None:
        return jsonify({"error": "봇이 아직 초기화되지 않았습니다. 잠시 후 다시 시도하세요."}), 503

    from bot.poster import post_to_channel

    future = asyncio.run_coroutine_threadsafe(
        post_to_channel(state.ptb_app.bot, brand, name, sizes, features, photo_paths),
        state.bot_loop,
    )
    try:
        message_ids = future.result(timeout=30)
    except Exception as e:
        return jsonify({"error": f"텔레그램 전송 실패: {e}"}), 500

    return jsonify({"success": True, "message_ids": message_ids})


@bp.route("/api/reply", methods=["POST"])
def api_reply():
    """어드민이 Telegram 사용자에게 답장."""
    data = request.get_json(force=True)
    session_id = data.get("session_id")
    text = data.get("text", "").strip()
    if not session_id or not text:
        return jsonify({"error": "session_id와 text가 필요합니다."}), 400

    session = sessions.get_session(session_id)
    if not session:
        return jsonify({"error": "세션을 찾을 수 없습니다."}), 404

    if session["type"] == "telegram":
        if state.ptb_app is None or state.bot_loop is None:
            return jsonify({"error": "봇이 준비되지 않았습니다."}), 503
        future = asyncio.run_coroutine_threadsafe(
            state.ptb_app.bot.send_message(chat_id=int(session["user_id"]), text=text),
            state.bot_loop,
        )
        try:
            future.result(timeout=10)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    sessions.add_message(session_id, "관리자", text, is_admin=True)
    return jsonify({"success": True})
