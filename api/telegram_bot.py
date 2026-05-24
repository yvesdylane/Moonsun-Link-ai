import os
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, MessageHandler, CallbackQueryHandler, filters, ContextTypes

from tools.router import ToolRouter
from db.controller.userController import check_if_user_exist, create_user_from_whatsapp, \
    check_if_user_exist_by_telegram, create_user_from_telegram
from utils.formatter import format_listings, get_listing_images, format_listing_item
from utils.translator import translate_reply
from utils.transcriber import transcribe_audio
import tempfile, os

load_dotenv()

router = ToolRouter()

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    phone = None  # telegram users don't always have phone
    telegram_id = str(user.id)
    name = user.full_name
    message = update.message.text

    exist, user_id = check_if_user_exist_by_telegram(telegram_id)
    if not exist:
        user_id = create_user_from_telegram(telegram_id, name)

    result = router.handle(message, str(user_id))
    await send_telegram_reply(update, result)


async def send_telegram_reply(update: Update, result: dict):
    detected_lang = result.get("language", "en")

    if result.get("preview_image"):
        reply = translate_reply(result.get("message", "Done"), detected_lang)
        await update.message.reply_photo(photo=result["preview_image"], caption=reply)

    elif "data" in result:
        data = result["data"]
        show_seller = result.get("show_seller", False)
        listings = data["listings"]
        text_listings = [l for l in listings if not l[8]]
        image_listings = get_listing_images(data, show_seller=show_seller)

        if text_listings:
            reply = format_listings({**data, "listings": text_listings}, show_seller=show_seller)
            reply = translate_reply(reply, detected_lang)
            # add next/prev buttons if multiple pages
            keyboard = []
            if data["page"] > 1:
                keyboard.append(InlineKeyboardButton("◀ Previous", callback_data="prev"))
            if data["page"] < data["total_pages"]:
                keyboard.append(InlineKeyboardButton("Next ▶", callback_data="next"))
            if keyboard:
                markup = InlineKeyboardMarkup([keyboard])
                await update.message.reply_text(reply, reply_markup=markup)
            else:
                await update.message.reply_text(reply)

        for image_url, caption in image_listings:
            caption = translate_reply(caption, detected_lang)
            await update.message.reply_photo(photo=image_url, caption=caption)

    else:
        reply = translate_reply(result.get("message", "Done"), detected_lang)
        await update.message.reply_text(reply)


def main():
    app = Application.builder().token(os.getenv("TELEGRAM_TOKEN")).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Telegram bot running...")
    app.run_polling()


if __name__ == "__main__":
    main()