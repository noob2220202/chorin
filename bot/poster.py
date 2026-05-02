from telegram import InputMediaPhoto, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.constants import ParseMode
import config
from utils.formatter import build_caption

BOT_USERNAME = "chorin_replicabot"


async def post_to_channel(bot, brand: str, name: str, sizes: list[str], features: str, photo_paths: list[str]):
    """첫 사진+글+버튼을 한 메시지로, 추가 사진은 아래에 전송합니다."""
    caption = build_caption(brand, name, sizes, features)

    button = InlineKeyboardMarkup([[
        InlineKeyboardButton("🛒 구매하기", url=f"https://t.me/{BOT_USERNAME}?start=buy")
    ]])

    # 첫 번째 사진 + 캡션 + 버튼 (한 메시지)
    with open(photo_paths[0], "rb") as fh:
        first_msg = await bot.send_photo(
            chat_id=config.CHANNEL_ID,
            photo=fh,
            caption=caption,
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=button,
        )

    # 나머지 사진들 (있으면 앨범으로 전송)
    extra_paths = photo_paths[1:]
    if extra_paths:
        media = []
        file_handles = []
        try:
            for path in extra_paths:
                fh = open(path, "rb")
                file_handles.append(fh)
                media.append(InputMediaPhoto(media=fh))
            await bot.send_media_group(chat_id=config.CHANNEL_ID, media=media)
        finally:
            for fh in file_handles:
                fh.close()

    return [first_msg.message_id]
