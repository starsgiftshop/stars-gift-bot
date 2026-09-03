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


def gift_price(stars):
    prices = {
        15: 3000,
        25: 5000,
        50: 14000,
        100: 27000,
    }
    return prices.get(stars, stars * PRICE_PER_STAR)


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
        "🎁 <b>Stars Gift Shop</b>\n\n"
        "Assalomu alaykum! 👋\n"
        "Kerakli bo‘limni tanlang 👇"
    )

    if update.message:
        await update.message.reply_text(
            text,
            parse_mode="HTML",
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
        "⭐ <b>Stars olish</b>\n\nPaketni tanlang:",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# =========================
# CUSTOM STARS
# =========================

async def ask_custom_stars(query, context):
    context.user_data["waiting_stars"] = True

    keyboard = [
        [InlineKeyboardButton("◀️ Orqaga", callback_data="stars")]
    ]

    await query.edit_message_text(
        "✏️ <b>Stars miqdorini yozing</b>\n\n"
        "Minimal miqdor: <b>10 Stars</b>\n\n"
        "Masalan: <code>30</code>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


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
            "❌ Minimal miqdor <b>10 Stars</b>.",
            parse_mode="HTML",
        )
        return

    context.user_data["waiting_stars"] = False

    price = amount * PRICE_PER_STAR

    keyboard = [
        [InlineKeyboardButton(
            f"💳 Sotib olish — {price:,} so‘m".replace(",", " "),
            callback_data=f"buy_custom_{amount}"
        )],
        [InlineKeyboardButton("◀️ Orqaga", callback_data="stars")],
    ]

    await update.message.reply_text(
        f"⭐ <b>{amount} Stars</b>\n\n"
        f"💰 Narxi: <b>{price:,} so‘m</b>\n\n"
        "Sotib olish uchun tugmani bosing 👇",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# =========================
# GIFTS
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

        # Bitta katalog xabari
        buttons = []

        for index, gift in enumerate(gifts.gifts, start=1):
            stars = gift.star_count
            price = gift_price(stars)

            button_text = (
                f"🎁 Gift {index} — {stars}⭐ | "
                f"{price:,} so‘m"
            ).replace(",", " ")

            buttons.append([
                InlineKeyboardButton(
                    button_text,
                    callback_data=f"giftpick:{gift.id}"
                )
            ])

        buttons.append([
            InlineKeyboardButton("◀️ Orqaga", callback_data="back")
        ])

        await query.edit_message_text(
            "🎁 <b>Giftlar</b>\n\n"
            "Kerakli Giftni tanlang 👇",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(buttons),
        )

    except Exception:
        await query.edit_message_text(
            "❌ Giftlarni yuklashda xatolik yuz berdi.\n\n"
            "Keyinroq qayta urinib ko‘ring.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("◀️ Orqaga", callback_data="back")]
            ]),
        )


# =========================
# GIFT PREVIEW
# =========================

async def show_gift_preview(query, context, gift_id):
    try:
        gifts = await context.bot.get_available_gifts()

        selected = None

        for gift in gifts.gifts:
            if str(gift.id) == str(gift_id):
                selected = gift
                break

        if selected is None:
            await query.answer("Gift topilmadi.", show_alert=True)
            return

        stars = selected.star_count
        price = gift_price(stars)

        keyboard = [
            [
                InlineKeyboardButton(
                    f"💳 Sotib olish — {price:,} so‘m".replace(",", " "),
                    callback_data=f"buygift:{selected.id}"
                )
            ],
            [
                InlineKeyboardButton(
                    "◀️ Giftlar",
                    callback_data="gift"
                )
            ],
        ]

        # Haqiqiy Gift rasmi/stickeri
        await context.bot.send_sticker(
            chat_id=query.message.chat_id,
            sticker=selected.sticker.file_id,
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

        await query.answer()

    except Exception:
        await query.answer(
            "❌ Gift rasmini yuklashda xatolik.",
            show_alert=True
        )


# =========================
# BUTTON HANDLER
# =========================

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "back":
        await start_from_button(query, context)

    elif data == "stars":
        await show_stars(query, context)

    elif data == "custom_stars":
        await ask_custom_stars(query, context)

    elif data == "gift":
        await show_gifts(query, context)

    elif data.startswith("giftpick:"):
        gift_id = data.split(":", 1)[1]
        await show_gift_preview(query, context, gift_id)

    elif data.startswith("buygift:"):
        await query.answer(
            "💳 To‘lov tizimi hali ulanmagan.",
            show_alert=True
        )

    elif data.startswith("buy_"):
        await query.answer(
            "💳 To‘lov tizimi hali ulanmagan.",
            show_alert=True
        )

    elif data.startswith("buy_custom_"):
        await query.answer(
            "💳 To‘lov tizimi hali ulanmagan.",
            show_alert=True
        )

    elif data == "premium":
        await query.edit_message_text(
            "💎 <b>Premium olish</b>\n\n"
            "Premium bo‘limi tez orada ishga tushadi.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("◀️ Orqaga", callback_data="back")]
            ]),
        )

    elif data == "balance":
        await query.edit_message_text(
            "💰 <b>Balansni to‘ldirish</b>\n\n"
            "To‘lov tizimi ulanmoqda.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("◀️ Orqaga", callback_data="back")]
            ]),
        )

    elif data == "profile":
        user = query.from_user

        await query.edit_message_text(
            f"👤 <b>Profil</b>\n\n"
            f"Ism: {user.first_name}\n"
            f"ID: <code>{user.id}</code>",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("◀️ Orqaga", callback_data="back")]
            ]),
        )

    elif data == "help":
        await query.edit_message_text(
            "🔵 <b>Yordam</b>\n\n"
            "Savollar bo‘lsa, administrator bilan bog‘laning.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("◀️ Orqaga", callback_data="back")]
            ]),
        )


# =========================
# BACK TO MENU
# =========================

async def start_from_button(query, context):
    keyboard = [
        [InlineKeyboardButton("⭐ Stars olish", callback_data="stars")],
        [InlineKeyboardButton("🎁 Gift olish", callback_data="gift")],
        [InlineKeyboardButton("💎 Premium olish", callback_data="premium")],
        [InlineKeyboardButton("💰 Balansni to‘ldirish", callback_data="balance")],
        [InlineKeyboardButton("👤 Profil", callback_data="profile")],
        [InlineKeyboardButton("🔵 Yordam", callback_data="help")],
    ]

    await query.edit_message_text(
        "🎁 <b>Stars Gift Shop</b>\n\n"
        "Kerakli bo‘limni tanlang 👇",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# =========================
# APPLICATION
# =========================

if not TOKEN:
    raise RuntimeError("BOT_TOKEN topilmadi!")

application = Application.builder().token(TOKEN).build()

application.add_handler(CommandHandler("start", start))
application.add_handler(CallbackQueryHandler(button))
application.add_handler(
    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_number)
)

application.run_polling(drop_pending_updates=True)
