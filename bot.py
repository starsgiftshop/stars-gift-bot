import os

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    MessageEntity,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)


TOKEN = os.getenv("BOT_TOKEN")


# =========================
# NARXLAR
# =========================

def gift_price(stars):
    if stars == 15:
        return 3000
    if stars == 25:
        return 5000
    if stars == 50:
        return 14000
    if stars == 100:
        return 27000

    return stars * 95


# =========================
# ASOSIY MENYU
# =========================

def main_menu():
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

    await update.message.reply_text(
        "🎁 <b>Stars Gift Shop</b>\n\n"
        "Assalomu alaykum! 👋\n"
        "Kerakli bo‘limni tanlang 👇",
        parse_mode="HTML",
        reply_markup=main_menu(),
    )


# =========================
# GIFTLAR RO‘YXATI
# =========================

async def show_gifts(query, context):
    try:
        result = await context.bot.get_available_gifts()

        if not result or not result.gifts:
            await query.edit_message_text(
                "🎁 Hozircha Gift mavjud emas.",
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton(
                            "◀️ Orqaga",
                            callback_data="back"
                        )
                    ]
                ]),
            )
            return

        buttons = []

        for index, gift in enumerate(result.gifts[:30], start=1):
            stars = gift.star_count
            price = gift_price(stars)

            text = (
                f"🎁 Gift {index} — "
                f"{stars}⭐ | "
                f"{price:,} so‘m"
            ).replace(",", " ")

            buttons.append([
                InlineKeyboardButton(
                    text,
                    callback_data=f"gift:{gift.id}"
                )
            ])

        buttons.append([
            InlineKeyboardButton(
                "◀️ Orqaga",
                callback_data="back"
            )
        ])

        await query.edit_message_text(
            "🎁 <b>Giftlar</b>\n\n"
            "Kerakli Giftni tanlang 👇",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(buttons),
        )

    except Exception as e:
        print("GIFTS ERROR:", repr(e))

        try:
            await query.edit_message_text(
                "❌ Giftlarni yuklashda xatolik.\n\n"
                "Keyinroq qayta urinib ko‘ring.",
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton(
                            "◀️ Orqaga",
                            callback_data="back"
                        )
                    ]
                ]),
            )
        except Exception:
            pass


# =========================
# GIFT PREVIEW
# =========================

async def show_gift_preview(query, context, gift_id):
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
        price = gift_price(stars)

        sticker = selected.sticker

        # ---------------------------------
        # CUSTOM EMOJI GIFT
        # ---------------------------------

        if (
            sticker.type == "custom_emoji"
            and sticker.custom_emoji_id
        ):
            emoji = sticker.emoji or "🎁"

            # Telegram custom emoji entity
            # aynan bitta emoji ustiga qo‘yiladi.
            emoji_length = len(
                emoji.encode("utf-16-le")
            ) // 2

            text = (
                f"{emoji} <b>Gift</b>\n\n"
                f"⭐ Narxi: <b>{stars} Stars</b>\n"
                f"💰 Sotuv narxi: <b>"
                f"{price:,} so‘m</b>\n\n"
                "💳 Sotib olish uchun tugmani bosing."
            ).replace(",", " ")

            entity = MessageEntity(
                type=MessageEntity.CUSTOM_EMOJI,
                offset=0,
                length=emoji_length,
                custom_emoji_id=sticker.custom_emoji_id,
            )

            await query.message.reply_text(
                text,
                entities=[entity],
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton(
                            "💳 Sotib olish",
                            callback_data=f"buygift:{selected.id}"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "◀️ Giftlar",
                            callback_data="gift"
                        )
                    ]
                ]),
            )

        # ---------------------------------
        # ODDIY STICKER GIFT
        # ---------------------------------

        else:
            await query.message.reply_sticker(
                sticker=sticker.file_id,
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton(
                            "💳 Sotib olish",
                            callback_data=f"buygift:{selected.id}"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "◀️ Giftlar",
                            callback_data="gift"
                        )
                    ]
                ]),
            )

            await query.message.reply_text(
                f"🎁 <b>Gift</b>\n\n"
                f"⭐ Narxi: <b>{stars} Stars</b>\n"
                f"💰 Sotuv narxi: <b>"
                f"{price:,} so‘m</b>".replace(",", " "),
                parse_mode="HTML",
            )

        await query.answer()

    except Exception as e:
        print("GIFT PREVIEW ERROR:", repr(e))

        try:
            await query.answer(
                "❌ Gift rasmini ochishda xatolik.",
                show_alert=True
            )
        except Exception:
            pass


# =========================
# BUTTONLAR
# =========================

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    try:
        await query.answer()
    except Exception:
        pass

    data = query.data or ""

    # ORQAGA
    if data == "back":
        await query.edit_message_text(
            "🎁 <b>Stars Gift Shop</b>\n\n"
            "Kerakli bo‘limni tanlang 👇",
            parse_mode="HTML",
            reply_markup=main_menu(),
        )

    # GIFT
    elif data == "gift":
        await show_gifts(query, context)

    # GIFT TANLASH
    elif data.startswith("gift:"):
        gift_id = data.split(":", 1)[1]
        await show_gift_preview(
            query,
            context,
            gift_id
        )

    # SOTIB OLISH
    elif data.startswith("buygift:"):
        await query.answer(
            "💳 To‘lov tizimi hali ulanmagan.",
            show_alert=True
        )

    # STARS
    elif data == "stars":
        await query.edit_message_text(
            "⭐ <b>Stars olish</b>\n\n"
            "100 ⭐ — 9 500 so‘m\n"
            "250 ⭐ — 23 750 so‘m\n"
            "500 ⭐ — 47 500 so‘m",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "◀️ Orqaga",
                        callback_data="back"
                    )
                ]
            ]),
        )

    # PREMIUM
    elif data == "premium":
        await query.edit_message_text(
            "💎 <b>Premium olish</b>\n\n"
            "Premium bo‘limi tez orada ulanadi.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "◀️ Orqaga",
                        callback_data="back"
                    )
                ]
            ]),
        )

    # BALANS
    elif data == "balance":
        await query.edit_message_text(
            "💰 <b>Balansni to‘ldirish</b>\n\n"
            "To‘lov tizimi ulanmoqda.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "◀️ Orqaga",
                        callback_data="back"
                    )
                ]
            ]),
        )

    # PROFIL
    elif data == "profile":
        user = query.from_user

        await query.edit_message_text(
            f"👤 <b>Profil</b>\n\n"
            f"Ism: {user.first_name}\n"
            f"ID: <code>{user.id}</code>\n\n"
            "💰 Balans: 0 so‘m",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "◀️ Orqaga",
                        callback_data="back"
                    )
                ]
            ]),
        )

    # YORDAM
    elif data == "help":
        await query.edit_message_text(
            "🔵 <b>Yordam</b>\n\n"
            "Savollar bo‘lsa administrator bilan bog‘laning.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "◀️ Orqaga",
                        callback_data="back"
                    )
                ]
            ]),
        )


# =========================
# BOTNI ISHGA TUSHIRISH
# =========================

if not TOKEN:
    raise RuntimeError(
        "BOT_TOKEN topilmadi!"
    )

application = (
    Application
    .builder()
    .token(TOKEN)
    .build()
)

application.add_handler(
    CommandHandler("start", start)
)

application.add_handler(
    CallbackQueryHandler(button)
)

application.run_polling(
    drop_pending_updates=True
            )
