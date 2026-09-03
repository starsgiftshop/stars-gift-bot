import os

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
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


# =========================
# START
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("⭐ Stars olish", callback_data="stars")],
        [InlineKeyboardButton("🎁 Gift olish", callback_data="gift")],
        [InlineKeyboardButton("💎 Premium olish", callback_data="premium")],
        [InlineKeyboardButton("💰 Balansni to‘ldirish", callback_data="balance")],
        [InlineKeyboardButton("👤 Profil", callback_data="profile")],
        [InlineKeyboardButton("🔵 Yordam", callback_data="help")],
    ]

    text = (
        "⭐ Stars Gift Shop\n\n"
        "Assalomu alaykum! 👋\n"
        "Kerakli bo‘limni tanlang 👇"
    )

    # /start oddiy xabar sifatida kelganda
    if update.message:
        await update.message.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    # Tugmadan qayta start chaqirilganda
    elif update.callback_query:
        await update.callback_query.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
        )


# =========================
# STARS
# =========================

async def show_stars(query, context):
    keyboard = [
        [InlineKeyboardButton("⭐ 100 Stars — 9 500 so‘m", callback_data="buy_100")],
        [InlineKeyboardButton("⭐ 250 Stars — 23 750 so‘m", callback_data="buy_250")],
        [InlineKeyboardButton("⭐ 500 Stars — 47 500 so‘m", callback_data="buy_500")],
        [InlineKeyboardButton("✏️ Boshqa miqdor", callback_data="custom_stars")],
        [InlineKeyboardButton("◀️ Orqaga", callback_data="back")],
    ]

    await query.edit_message_text(
        "⭐ Stars olish\n\nPaketni tanlang:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# =========================
# GIFTLAR
# =========================

async def show_gifts(query, context):
    try:
        gifts = await context.bot.get_available_gifts()

        if not gifts or not gifts.gifts:
            await query.edit_message_text(
                "🎁 Hozircha mavjud Gift topilmadi.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("◀️ Orqaga", callback_data="back")]
                ]),
            )
            return

        await query.edit_message_text("🎁 Mavjud Giftlar yuklanmoqda...")

        # Juda ko‘p xabar yuborib yubormaslik uchun
        gift_list = gifts.gifts[:20]

        for gift in gift_list:
            sticker = gift.sticker

            text = (
                f"🎁 Telegram Gift\n\n"
                f"⭐ Narxi: {gift.star_count} Stars"
            )

            if gift.remaining_count is not None:
                text += f"\n📦 Qolgan: {gift.remaining_count}"

            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "🎁 Tanlash",
                        callback_data=f"selectgift_{gift.id}"
                    )
                ]
            ])

            # Gift rasmini/stickerini yuborish
            try:
                await context.bot.send_sticker(
                    chat_id=query.message.chat_id,
                    sticker=sticker.file_id,
                )
            except Exception:
                # Agar sticker yuborishda xato bo‘lsa,
                # Gift ma'lumotini baribir ko‘rsatamiz.
                pass

            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=text,
                reply_markup=keyboard,
            )

        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="👇 Menyuga qaytish:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("◀️ Orqaga", callback_data="back")]
            ]),
        )

    except Exception as e:
        print("GIFT ERROR:", repr(e))

        await query.edit_message_text(
            "❌ Giftlarni yuklashda xatolik yuz berdi.\n\n"
            "Keyinroq qayta urinib ko‘ring.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("◀️ Orqaga", callback_data="back")]
            ]),
        )


# =========================
# PREMIUM
# =========================

async def show_premium(query, context):
    keyboard = [
        [InlineKeyboardButton("💎 Premium", callback_data="premium_info")],
        [InlineKeyboardButton("◀️ Orqaga", callback_data="back")],
    ]

    await query.edit_message_text(
        "💎 Premium olish\n\n"
        "Premium bo‘yicha ma'lumot tez orada qo‘shiladi.",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# =========================
# BALANS
# =========================

async def show_balance(query, context):
    await query.edit_message_text(
        "💰 Balansni to‘ldirish\n\n"
        "To‘lov tizimi ulanmoqda...",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("◀️ Orqaga", callback_data="back")]
        ]),
    )


# =========================
# PROFIL
# =========================

async def show_profile(query, context):
    user = query.from_user

    text = (
        "👤 Profil\n\n"
        f"🆔 ID: {user.id}\n"
        f"👤 Ism: {user.first_name}\n\n"
        "💰 Balans: 0 so‘m"
    )

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("◀️ Orqaga", callback_data="back")]
        ]),
    )


# =========================
# YORDAM
# =========================

async def show_help(query, context):
    await query.edit_message_text(
        "🔵 Yordam\n\n"
        "⭐ Stars olish — Stars paketlarini tanlash.\n"
        "🎁 Gift olish — mavjud Giftlarni ko‘rish.\n"
        "💎 Premium olish — Premium bo‘limi.\n"
        "💰 Balans — hisobni to‘ldirish.\n\n"
        "Savollar bo‘lsa administratorga murojaat qiling.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("◀️ Orqaga", callback_data="back")]
        ]),
    )


# =========================
# TUGMALAR
# =========================

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "back":
        await start(update, context)

    elif data == "stars":
        await show_stars(query, context)

    elif data == "gift":
        await show_gifts(query, context)

    elif data == "premium":
        await show_premium(query, context)

    elif data == "balance":
        await show_balance(query, context)

    elif data == "profile":
        await show_profile(query, context)

    elif data == "help":
        await show_help(query, context)

    elif data == "custom_stars":
        context.user_data["waiting_stars"] = True

        await query.edit_message_text(
            "✏️ Stars miqdorini yozing.\n\n"
            "Minimum: 10 Stars\n"
            "Masalan: 30"
        )

    elif data.startswith("buy_"):
        amount = int(data.split("_")[1])
        price = amount * PRICE_PER_STAR

        await query.edit_message_text(
            f"⭐ {amount} Stars\n\n"
            f"💰 Narxi: {price:,} so‘m\n\n"
            "💳 To‘lov tizimi ulanmoqda...",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("◀️ Orqaga", callback_data="stars")]
            ]),
        )

    elif data.startswith("selectgift_"):
        gift_id = data.replace("selectgift_", "")

        context.user_data["selected_gift"] = gift_id

        await query.message.reply_text(
            "🎁 Gift tanlandi.\n\n"
            "💳 To‘lov tizimi ulanmoqda..."
        )

    elif data == "premium_info":
        await query.edit_message_text(
            "💎 Premium\n\n"
            "Premium to‘lov tizimi keyingi bosqichda ulanadi.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("◀️ Orqaga", callback_data="premium")]
            ]),
        )


# =========================
# CUSTOM STARS
# =========================

async def handle_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("waiting_stars"):
        return

    text = update.message.text.strip()

    try:
        amount = int(text)
    except ValueError:
        await update.message.reply_text(
            "❌ Faqat raqam yozing.\nMasalan: 30"
        )
        return

    if amount < 10:
        await update.message.reply_text(
            "❌ Minimum 10 Stars.\nQaytadan yozing:"
        )
        return

    price = amount * PRICE_PER_STAR

    context.user_data["waiting_stars"] = False

    keyboard = [
        [
            InlineKeyboardButton(
                "💳 To‘lash",
                callback_data=f"buy_{amount}"
            )
        ],
        [
            InlineKeyboardButton(
                "◀️ Orqaga",
                callback_data="stars"
            )
        ],
    ]

    await update.message.reply_text(
        f"⭐ {amount} Stars\n"
        f"💰 Narxi: {price:,} so‘m\n\n"
        "Paketni tasdiqlang:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# =========================
# APPLICATION
# =========================

def main():
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN topilmadi!")

    application = Application.builder().token(TOKEN).build()

    application.add_handler(
        CommandHandler("start", start)
    )

    application.add_handler(
        CallbackQueryHandler(button)
    )

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_number
        )
    )

    print("Bot ishga tushdi...")

    application.run_polling(
        drop_pending_updates=True
    )


if __name__ == "__main__":
    main()
