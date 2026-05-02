import asyncio
import threading

import config
import state
from bot.client import build_application, start_bot
from web.app import create_app, socketio


def run_bot():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    state.bot_loop = loop
    app = build_application()
    state.ptb_app = app
    loop.run_until_complete(start_bot(app))


if __name__ == "__main__":
    bot_thread = threading.Thread(target=run_bot, daemon=True, name="telegram-bot")
    bot_thread.start()

    flask_app = create_app()
    print(f"서버 시작: http://{config.HOST}:{config.PORT}")
    socketio.run(flask_app, host=config.HOST, port=config.PORT)
