import os
from telegram import InputMediaPhoto, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.constants import ParseMode
import config
from utils.formatter import build_caption, build_button_text

BOT_USERNAME = "chorin_replicabot"


async def post_to_channel(bot, brand: str, name: str, sizes: list[str], features: str, photo_paths: list[str]):
    """채널에 옷 정보를 앨범 + 버튼 형식으로 게시합니다."""
    caption = build_caption(brand, name, sizes, features)
    button_text = build_button_text()

    media = []
    file_handles = []
    try:
        for i, path in enumerate(photo_paths):
            fh = open(path, "rb")
            file_handles.append(fh)
            media.append(
                InputMediaPhoto(
                    media=fh,
                    caption=caption if i == 0 else None,
                    parse_mode=ParseMode.MARKDOWN_V2 if i == 0 else None,
                )
            )

        messages = await bot.send_media_group(chat_id=config.CHANNEL_ID, media=media)
    finally:
        for fh in file_handles:
            fh.close()

    first_msg_id = messages[0].message_id
    await bot.send_message(
        chat_id=config.CHANNEL_ID,
        text=button_text,
        parse_mode=ParseMode.MARKDOWN_V2,
        reply_to_message_id=first_msg_id,
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🛒 구매하기", url=f"https://t.me/{BOT_USERNAME}?start=buy")
        ]]),
    )

    return [m.message_id for m in messages]
