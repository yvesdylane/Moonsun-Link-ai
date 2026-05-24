import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from tools.router import ToolRouter
from db.controller.userController import check_if_user_exist_by_telegram, create_user_from_telegram
from utils.formatter import format_listings, get_listing_images
from utils.translator import translate_reply

router = ToolRouter()

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    telegram_id = str(user.id)
    name = user.full_name
    message = update.message.text

    exist, user_id = check_if_user_exist_by_telegram(telegram_id)
    if not exist:
        # don't auto-create — ask them to register first
        await update.message.reply_text(
            "👋 Welcome to Moonso Link! You need to register first.\n"
            "Please share your phone number by typing /register"
        )
        return

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


def setup_handlers(app: Application):
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))