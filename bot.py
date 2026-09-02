import os

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

TOKEN = os.getenv("BOT_TOKEN")

PRICE_PER_STAR = 95


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("⭐ Stars olish", callback_data="stars")],
        [InlineKeyboardButton("🎁 Gift olish", callback_data="gift")],
        [InlineKeyboardButton("💎 Premium olish", callback_data="premium")],
        [InlineKeyboardButton("💰 Balansni to‘ldirish", callback_data="balance")],
        [InlineKeyboardButton("👤 Profil", callback_data="profile")],
        [InlineKeyboardButton("🔵 Yordam", callback_data="help")],
    ]

    await update.message.reply_text(
        "⭐ Stars Gift Shop\n\n"
        "Assalomu alaykum! 👋\n"
        "Kerakli bo‘limni tanlang 👇",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "stars":
        keyboard = [
            [InlineKeyboardButton("⭐ 100 Stars — 9 500 so‘m", callback_data="stars100")],
            [InlineKeyboardButton("⭐ 250 Stars — 23 750 so‘m", callback_data="stars250")],
            [InlineKeyboardButton("⭐ 500 Stars — 47 500 so‘m", callback_data="stars500")],
            [InlineKeyboardButton("✏️ Boshqa miqdor", callback_data="custom_stars")],
            [InlineKeyboardButton("◀️ Orqaga", callback_data="back")],
        ]

        await query.edit_message_text(
            "⭐ Stars olish\n\nPaketni tanlang:",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    elif query.data == "custom_stars":
        context.user_data["waiting_stars"] = True

        await query.edit_message_text(
            "✏️ Nechta Stars olmoqchisiz?\n\n"
            "Masalan: 500\n"
            "Minimum: 10 Stars"
        )

    elif query.data.startswith("stars"):
        amount = int(query.data.replace("stars", ""))
        price = amount * PRICE_PER_STAR

        await query.edit_message_text(
            f"⭐ {amount} Stars\n\n"
            f"💰 Narxi: {price:,} so‘m\n\n"
            "To‘lov qismi keyingi bosqichda ulanadi."
        )

    elif query.data == "gift":
        await query.edit_message_text(
            "🎁 Gift Shop\n\n"
            "Giftlar bo‘limi."
        )

    elif query.data == "premium":
        await query.edit_message_text(
            "💎 Premium olish\n\n"
            "Premium paketlar bo‘limi."
        )

    elif query.data == "balance":
        await query.edit_message_text(
            "💰 Balansni to‘ldirish\n\n"
            "Balans to‘ldirish bo‘limi."
        )

    elif query.data == "profile":
        await query.edit_message_text(
            "👤 Profil\n\n"
            "Profil ma’lumotlari."
        )

    elif query.data == "help":
        await query.edit_message_text(
            "🔵 Yordam\n\n"
            "Savollar bo‘lsa, admin bilan bog‘laning."
        )

    elif query.data == "back":
        await start(update, context)


async def handle_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("waiting_stars"):
        return

    text = update.message.text.strip()

    if not text.isdigit():
        await update.message.reply_text(
            "❌ Faqat raqam kiriting.\nMasalan: 500"
        )
        return

    amount = int(text)

    if amount < 10:
        await update.message.reply_text(
            "❌ Minimum 10 Stars."
        )
        return

    price = amount * PRICE_PER_STAR
    context.user_data["waiting_stars"] = False

    keyboard = [
        [InlineKeyboardButton(
            "💳 To‘lovga o‘tish",
            callback_data=f"pay_{amount}"
        )],
        [InlineKeyboardButton(
            "◀️ Orqaga",
            callback_data="stars"
        )],
    ]

    await update.message.reply_text(
        f"⭐ {amount} Stars\n\n"
        f"💰 Narxi: {price:,} so‘m\n\n"
        "Miqdor to‘g‘ri bo‘lsa, to‘lovni davom ettiring 👇",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


application = Application.builder().token(TOKEN).build()

application.add_handler(CommandHandler("start", start))
application.add_handler(CallbackQueryHandler(button))
application.add_handler(
    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_number)
)

application.run_polling()
