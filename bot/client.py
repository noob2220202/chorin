from telegram.ext import Application, CallbackQueryHandler, MessageHandler, filters
import config
import state
from bot.handlers import handle_callback_query, handle_user_message


def build_application() -> Application:
    app = Application.builder().token(config.BOT_TOKEN).build()
    app.add_handler(CallbackQueryHandler(handle_callback_query))
    app.add_handler(MessageHandler(filters.ChatType.PRIVATE & ~filters.COMMAND, handle_user_message))
    return app


async def start_bot(app: Application):
    state.ptb_app = app
    await app.initialize()
    await app.start()
    await app.updater.start_polling(drop_pending_updates=True)
    # 루프가 취소될 때까지 블로킹
    import asyncio
    await asyncio.Event().wait()
