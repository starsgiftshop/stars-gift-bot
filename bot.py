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


# =========================
# NARXLAR
# =========================

def stars_price(stars):
    if stars == 15:
        return 3000
    if stars == 25:
        return 5000
    if stars == 50:
        return 14000
    if stars == 100:
        return 27000
    return stars * 95


def menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⭐ Stars olish", callback_data="stars")],
        [InlineKeyboardButton("🎁 Gift olish", callback_data="gift")],
        [InlineKeyboardButton("💎 Premium olish", callback_data="premium")],
        [InlineKeyboardButton("💰 Balansni to‘ldirish", callback_data="balance")],
        [InlineKeyboardButton("👤 Profil", callback_data="profile")],
        [InlineKeyboardButton("🔵 Yordam", callback_data="help")],
    ])


# =========================
# START
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    context.user_data["waiting_stars"] = False

    await update.message.reply_text(
        "🎁 <b>Stars Gift Shop</b>\n\n"
        "Assalomu alaykum! 👋\n"
        "Kerakli bo‘limni tanlang 👇",
        parse_mode="HTML",
        reply_markup=menu()
    )


# =========================
# STARS
# =========================

async def show_stars(query, context):

    keyboard = [
        [InlineKeyboardButton("⭐ 100 Stars — 9 500 so‘m", callback_data="stars:100")],
        [InlineKeyboardButton("⭐ 250 Stars — 23 750 so‘m", callback_data="stars:250")],
        [InlineKeyboardButton("⭐ 500 Stars — 47 500 so‘m", callback_data="stars:500")],
        [InlineKeyboardButton("✏️ Boshqa miqdor", callback_data="custom_stars")],
        [InlineKeyboardButton("◀️ Orqaga", callback_data="back")],
    ]

    await query.edit_message_text(
        "⭐ <b>Stars olish</b>\n\n"
        "Kerakli miqdorni tanlang 👇",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================
# CUSTOM STARS
# =========================

async def custom_stars(query, context):

    context.user_data["waiting_stars"] = True

    await query.edit_message_text(
        "✏️ <b>Boshqa miqdor</b>\n\n"
        "Nechta Stars kerak?\n\n"
        "🔹 Minimum: 10 Stars\n"
        "Masalan: <code>30</code>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("◀️ Orqaga", callback_data="stars")]
        ])
    )


async def custom_stars_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

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
            "❌ Minimum 10 Stars."
        )
        return

    context.user_data["waiting_stars"] = False

    price = stars_price(amount)

    await update.message.reply_text(
        "⭐ <b>Stars buyurtmasi</b>\n\n"
        f"⭐ Miqdor: <b>{amount}</b> Stars\n"
        f"💰 Narxi: <b>{price:,} so‘m</b>\n\n"
        "💳 To‘lov tizimi ulanmoqda.",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(
                "💳 Sotib olish",
                callback_data=f"buy_stars:{amount}"
            )],
            [InlineKeyboardButton(
                "◀️ Orqaga",
                callback_data="stars"
            )]
        ])
    )


# =========================
# GIFTS
# =========================

async def show_gifts(query, context):

    try:
        result = await context.bot.get_available_gifts()

        if not result or not result.gifts:
            await query.edit_message_text(
                "🎁 Hozircha Gift mavjud emas.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("◀️ Orqaga", callback_data="back")]
                ])
            )
            return

        buttons = []

        for gift in result.gifts[:30]:

            stars = gift.star_count
            price = stars_price(stars)

            emoji = "🎁"

            try:
                if gift.sticker and gift.sticker.emoji:
                    emoji = gift.sticker.emoji
            except Exception:
                pass

            text = (
                f"{emoji} {stars}⭐ — "
                f"{price:,} so‘m"
            ).replace(",", " ")

            buttons.append([
                InlineKeyboardButton(
                    text,
                    callback_data=f"gift:{gift.id}"
                )
            ])

        buttons.append([
            InlineKeyboardButton("◀️ Orqaga", callback_data="back")
        ])

        await query.edit_message_text(
            "🎁 <b>Giftlar</b>\n\n"
            "Kerakli Giftni tanlang 👇",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    except Exception as e:
        print("GIFTS ERROR:", repr(e))

        await query.edit_message_text(
            "❌ Giftlarni yuklashda xatolik.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("◀️ Orqaga", callback_data="back")]
            ])
        )


# =========================
# GIFT PREVIEW
# =========================

async def gift_preview(query, context, gift_id):

    try:
        result = await context.bot.get_available_gifts()

        selected = None

        for gift in result.gifts:
            if str(gift.id) == str(gift_id):
                selected = gift
                break

        if selected is None:
            await query.answer(
                "Gift topilmadi.",
                show_alert=True
            )
            return

        stars = selected.star_count
        price = stars_price(stars)

        emoji = "🎁"

        try:
            if selected.sticker and selected.sticker.emoji:
                emoji = selected.sticker.emoji
        except Exception:
            pass

        text = (
            f"{emoji} <b>Gift</b>\n\n"
            f"⭐ Gift qiymati: <b>{stars} Stars</b>\n"
            f"💰 Sotuv narxi: <b>{price:,} so‘m</b>\n\n"
            "🎁 Sotib olgandan keyin Gift avtomatik yuboriladi.\n"
            "💳 To‘lov tizimi ulanmoqda."
        ).replace(",", " ")

        keyboard = [
            [InlineKeyboardButton(
                f"💳 Sotib olish — {price:,} so‘m".replace(",", " "),
                callback_data=f"buygift:{selected.id}"
            )],
            [InlineKeyboardButton(
                "◀️ Giftlar",
                callback_data="gift"
            )]
        ]

        await query.edit_message_text(
            text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    except Exception as e:
        print("GIFT PREVIEW ERROR:", repr(e))

        await query.answer(
            "❌ Giftni ochishda xatolik.",
            show_alert=True
        )


# =========================
# BUTTONLAR
# =========================

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    data = query.data or ""

    try:
        await query.answer()
    except Exception:
        pass

    # ORQAGA
    if data == "back":

        await query.edit_message_text(
            "🎁 <b>Stars Gift Shop</b>\n\n"
            "Kerakli bo‘limni tanlang 👇",
            parse_mode="HTML",
            reply_markup=menu()
        )

    # STARS
    elif data == "stars":

        context.user_data["waiting_stars"] = False
        await show_stars(query, context)

    # CUSTOM STARS
    elif data == "custom_stars":

        await custom_stars(query, context)

    # STARS BUY
    elif data.startswith("stars:"):

        amount = data.split(":", 1)[1]

        await query.edit_message_text(
            "⭐ <b>Stars</b>\n\n"
            f"⭐ Miqdor: <b>{amount}</b>\n"
            f"💰 Narxi: <b>{stars_price(int(amount)):,} so‘m</b>\n\n"
            "💳 To‘lov tizimi ulanmoqda.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    "💳 To‘lash",
                    callback_data=f"buy_stars:{amount}"
                )],
                [InlineKeyboardButton(
                    "◀️ Stars",
                    callback_data="stars"
                )]
            ])
        )

    # BUY STARS
    elif data.startswith("buy_stars:"):

        await query.answer(
            "💳 Click to‘lovi hali ulanmagan.",
            show_alert=True
        )

    # GIFTS
    elif data == "gift":

        await show_gifts(query, context)

    # GIFT PREVIEW
    elif data.startswith("gift:"):

        gift_id = data.split(":", 1)[1]
        await gift_preview(query, context, gift_id)

    # BUY GIFT
    elif data.startswith("buygift:"):

        await query.answer(
            "💳 Click to‘lovi hali ulanmagan.",
            show_alert=True
        )

    # PREMIUM
    elif data == "premium":

        await query.edit_message_text(
            "💎 <b>Premium</b>\n\n"
            "Premium paketlari tez orada ulanadi.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    "◀️ Orqaga",
                    callback_data="back"
                )]
            ])
        )

    # BALANCE
    elif data == "balance":

        await query.edit_message_text(
            "💰 <b>Balans</b>\n\n"
            "Balansni Click orqali to‘ldirish tizimi ulanmoqda.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    "◀️ Orqaga",
                    callback_data="back"
                )]
            ])
        )

    # PROFILE
    elif data == "profile":

        user = query.from_user

        await query.edit_message_text(
            "👤 <b>Profil</b>\n\n"
            f"👤 Ism: {user.first_name}\n"
            f"🆔 ID: <code>{user.id}</code>\n\n"
            "💰 Balans: <b>0 so‘m</b>",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    "◀️ Orqaga",
                    callback_data="back"
                )]
            ])
        )

    # HELP
    elif data == "help":

        await query.edit_message_text(
            "🔵 <b>Yordam</b>\n\n"
            "Muammo bo‘lsa administrator bilan bog‘laning.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    "◀️ Orqaga",
                    callback_data="back"
                )]
            ])
        )


# =========================
# BOTNI ISHGA TUSHIRISH
# =========================

if not TOKEN:
    raise RuntimeError("BOT_TOKEN topilmadi!")

application = Application.builder().token(TOKEN).build()

application.add_handler(CommandHandler("start", start))

application.add_handler(
    MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        custom_stars_message
    )
)

application.add_handler(
    CallbackQueryHandler(button)
)

application.run_polling(
    drop_pending_updates=True
    )
