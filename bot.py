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
        await query.edit_message_text(
            "✏️ Nechta Stars olmoqchisiz?\n\n"
            "Masalan: 500\n"
            "Minimum: 10 Stars"
        )

    elif query.data.startswith("stars"):
        amount = int(query.data.replace("stars", ""))
        price = amount * PRICE_PER_STAR

        keyboard = [
            [InlineKeyboardButton("💳 To‘lovga o‘tish", callback_data=f"pay_{amount}")],
            [InlineKeyboardButton("◀️ Orqaga", callback_data="stars")],
        ]

        await query.edit_message_text(
            f"⭐ {amount} Stars\n\n"
            f"💰 Narxi: {price:,} so‘m\n\n"
            "To‘lov qismi keyingi bosqichda ulanadi.",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    elif query.data.startswith("pay_"):
        amount = int(query.data.replace("pay_", ""))
        price = amount * PRICE_PER_STAR

        await query.edit_message_text(
            f"💳 To‘lov\n\n"
            f"⭐ Stars: {amount}\n"
            f"💰 Summa: {price:,} so‘m\n\n"
            "Avtomatik to‘lov keyingi bosqichda ulanadi."
        )

    elif query.data == "gift":
        try:
            gifts = await context.bot.get_available_gifts()

            if not gifts.gifts:
                await query.edit_message_text(
                    "🎁 Hozircha Gift mavjud emas.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("◀️ Orqaga", callback_data="back")]
                    ]),
                )
                return

            keyboard = []

            for gift in gifts.gifts:
                keyboard.append([
                    InlineKeyboardButton(
                        f"🎁 {gift.star_count} Stars",
                        callback_data=f"gift_{gift.id}"
                    )
                ])

            keyboard.append([
                InlineKeyboardButton("◀️ Orqaga", callback_data="back")
            ])

            await query.edit_message_text(
                "🎁 Gift olish\n\n"
                "Kerakli Giftni tanlang:",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )

        except Exception:
            await query.edit_message_text(
                "❌ Giftlarni yuklashda xatolik yuz berdi.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("◀️ Orqaga", callback_data="back")]
                ]),
            )

    elif query.data.startswith("gift_"):
        await query.edit_message_text(
            "🎁 Gift tanlandi.\n\n"
            "Avtomatik sotib olish va yuborish keyingi bosqichda ulanadi.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("◀️ Orqaga", callback_data="gift")],
                [InlineKeyboardButton("🏠 Bosh menyu", callback_data="back")],
            ]),
        )

    elif query.data == "premium":
        await query.edit_message_text(
            "💎 Premium olish\n\n"
            "Premium paketlar keyingi bosqichda ulanadi.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("◀️ Orqaga", callback_data="back")]
            ]),
        )

    elif query.data == "balance":
        await query.edit_message_text(
            "💰 Balansni to‘ldirish\n\n"
            "Balans to‘ldirish bo‘limi keyingi bosqichda ulanadi.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("◀️ Orqaga", callback_data="back")]
            ]),
        )

    elif query.data == "profile":
        user = update.effective_user

        await query.edit_message_text(
            f"👤 Profil\n\n"
            f"🆔 ID: {user.id}\n"
            f"👤 Ism: {user.first_name}\n\n"
            f"💰 Balans: 0 so‘m",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("◀️ Orqaga", callback_data="back")]
            ]),
        )

    elif query.data == "help":
        await query.edit_message_text(
            "🔵 Yordam\n\n"
            "Savollar bo‘lsa, admin bilan bog‘laning.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("◀️ Orqaga", callback_data="back")]
            ]),
        )

    elif query.data == "back":
        await query.message.delete()
        await start(update, context)


async def handle_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if not text.isdigit():
        return

    amount = int(text)

    if amount < 10:
        await update.message.reply_text("❌ Minimum 10 Stars.")
        return

    price = amount * PRICE_PER_STAR

    keyboard = [
        [InlineKeyboardButton("💳 To‘lovga o‘tish", callback_data=f"pay_{amount}")],
        [InlineKeyboardButton("◀️ Orqaga", callback_data="stars")],
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
