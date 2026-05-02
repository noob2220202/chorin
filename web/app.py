import os
from flask import Flask
from flask_socketio import SocketIO
import config

socketio = SocketIO(cors_allowed_origins="*", async_mode="eventlet")


def create_app() -> Flask:
    app = Flask(
        __name__,
        static_folder=os.path.join(os.path.dirname(__file__), "..", "public"),
        static_url_path="/static",
    )
    app.secret_key = os.urandom(24)

    os.makedirs(config.UPLOAD_DIR, exist_ok=True)

    from web.routes import bp as routes_bp
    from web.socket_events import register_events

    app.register_blueprint(routes_bp)
    register_events(socketio)
    socketio.init_app(app)

    return app
