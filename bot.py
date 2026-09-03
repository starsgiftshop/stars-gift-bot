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


async def show_gifts(query, context):
    try:
        gifts = await context.bot.get_available_gifts()

        if not gifts.gifts:
            await query.edit_message_text(
                "🎁 Hozircha mavjud Gift yo‘q.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("◀️ Orqaga", callback_data="back")]
                ]),
            )
            return

        # Har bir Gift uchun alohida xabar yuboramiz
        await query.edit_message_text(
            "🎁 Mavjud Giftlar yuklanmoqda..."
        )

        for gift in gifts.gifts:
            sticker = gift.sticker

            caption = (
                f"🎁 Gift\n\n"
                f"⭐ Telegram narxi: {gift.star_count} Stars\n"
            )

            if gift.remaining_count is not None:
                caption += f"📦 Qolgan: {gift.remaining_count}\n"

            keyboard = [
                [
                    InlineKeyboardButton(
                        "🛒 Tanlash",
                        callback_data=f"gift_{gift.id}"
                    )
                ]
            ]

            try:
                if sticker.is_video:
                    await context.bot.send_sticker(
                        chat_id=query.message.chat_id,
                        sticker=sticker.file_id,
                    )
                    await context.bot.send_message(
                        chat_id=query.message.chat_id,
                        text=caption,
                        reply_markup=InlineKeyboardMarkup(keyboard),
                    )

                else:
                    await context.bot.send_sticker(
                        chat_id=query.message.chat_id,
                        sticker=sticker.file_id,
                    )
                    await context.bot.send_message(
                        chat_id=query.message.chat_id,
                        text=caption,
                        reply_markup=InlineKeyboardMarkup(keyboard),
                    )

            except Exception:
                await context.bot.send_message(
                    chat_id=query.message.chat_id,
                    text=caption,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                )

        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="🎁 Gift katalogi tugadi.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("◀️ Bosh menyu", callback_data="back")]
            ]),
        )

    except Exception as e:
        await query.edit_message_text(
            "❌ Giftlarni yuklashda xatolik yuz berdi.\n\n"
            "Railway loglarini tekshirish kerak.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("◀️ Orqaga", callback_data="back")]
            ]),
        )


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "stars":
        keyboard = [
            [InlineKeyboardButton(
                "⭐ 100 Stars — 9 500 so‘m",
                callback_data="stars100"
            )],
            [InlineKeyboardButton(
                "⭐ 250 Stars — 23 750 so‘m",
                callback_data="stars250"
            )],
            [InlineKeyboardButton(
                "⭐ 500 Stars — 47 500 so‘m",
                callback_data="stars500"
            )],
            [InlineKeyboardButton(
                "✏️ Boshqa miqdor",
                callback_data="custom_stars"
            )],
            [InlineKeyboardButton(
                "◀️ Orqaga",
                callback_data="back"
            )],
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
            [InlineKeyboardButton(
                "💳 To‘lovga o‘tish",
                callback_data=f"pay_{amount}"
            )],
            [InlineKeyboardButton(
                "◀️ Orqaga",
                callback_data="stars"
            )],
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
        await show_gifts(query, context)

    elif query.data.startswith("gift_"):
        gift_id = query.data.replace("gift_", "")

        await query.edit_message_text(
            f"🎁 Gift tanlandi\n\n"
            f"🆔 Gift ID: {gift_id}\n\n"
            "💳 To‘lov qismi keyingi bosqichda ulanadi.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    "◀️ Giftlarga qaytish",
                    callback_data="gift"
                )],
                [InlineKeyboardButton(
                    "🏠 Bosh menyu",
                    callback_data="back"
                )],
            ]),
        )

    elif query.data == "premium":
        await query.edit_message_text(
            "💎 Premium olish\n\n"
            "Premium paketlari keyingi bosqichda ulanadi.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    "◀️ Orqaga",
                    callback_data="back"
                )]
            ]),
        )

    elif query.data == "balance":
        await query.edit_message_text(
            "💰 Balansni to‘ldirish\n\n"
            "Balans to‘ldirish keyingi bosqichda ulanadi.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    "◀️ Orqaga",
                    callback_data="back"
                )]
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
                [InlineKeyboardButton(
                    "◀️ Orqaga",
                    callback_data="back"
                )]
            ]),
        )

    elif query.data == "help":
        await query.edit_message_text(
            "🔵 Yordam\n\n"
            "Savollar bo‘lsa, admin bilan bog‘laning.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    "◀️ Orqaga",
                    callback_data="back"
                )]
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
        await update.message.reply_text(
            "❌ Minimum 10 Stars."
        )
        return

    price = amount * PRICE_PER_STAR

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

application.run_polling()
