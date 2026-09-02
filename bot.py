import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("⭐ Stars olish", callback_data="stars")],
        [InlineKeyboardButton("🎁 Gift olish", callback_data="gift")],
        [InlineKeyboardButton("💎 Premium olish", callback_data="premium")],
        [InlineKeyboardButton("💰 Balansni to‘ldirish", callback_data="balance")],
        [InlineKeyboardButton("👤 Profil", callback_data="profile")],
        [InlineKeyboardButton("🔵 Yordam", callback_data="help")]
    ]

    await update.message.reply_text(
        "🌟 Stars Gift Shop\n\n"
        "Assalomu alaykum!\n"
        "Kerakli bo‘limni tanlang 👇",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "stars":
        keyboard = [
            [InlineKeyboardButton("⭐ 100 Stars — 9 500 so‘m", callback_data="stars100")],
            [InlineKeyboardButton("⭐ 250 Stars — 23 750 so‘m", callback_data="stars250")],
            [InlineKeyboardButton("⭐ 500 Stars — 47 500 so‘m", callback_data="stars500")],
            [InlineKeyboardButton("⬅️ Orqaga", callback_data="back")]
        ]
        await query.edit_message_text(
            "⭐ Stars olish\n\nPaketni tanlang:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif query.data == "gift":
        await query.edit_message_text(
            "🎁 Gift Shop\n\n"
            "Bu yerda mavjud Giftlar va ularning narxlari chiqadi."
        )

    elif query.data == "premium":
        await query.edit_message_text(
            "💎 Premium olish\n\n"
            "Premium paket
