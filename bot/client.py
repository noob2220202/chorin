from telegram.ext import Application, CommandHandler, MessageHandler, filters
import config
import state
from bot.handlers import handle_start, handle_user_message


def build_application() -> Application:
    app = Application.builder().token(config.BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", handle_start))
    app.add_handler(MessageHandler(filters.ChatType.PRIVATE & ~filters.COMMAND, handle_user_message))
    return app


async def start_bot(app: Application):
    state.ptb_app = app
    await app.initialize()
    await app.start()
    await app.updater.start_polling(drop_pending_updates=True)
    import asyncio
    await asyncio.Event().wait()
