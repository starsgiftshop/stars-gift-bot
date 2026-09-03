import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

TOKEN = os.getenv("BOT_TOKEN")

def menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⭐ Stars olish", callback_data="stars")],
        [InlineKeyboardButton("🎁 Gift olish", callback_data="gift")],
        [InlineKeyboardButton("💎 Premium olish", callback_data="premium")],
        [InlineKeyboardButton("💰 Balansni to‘ldirish", callback_data="balance")],
        [InlineKeyboardButton("👤 Profil", callback_data="profile")],
        [InlineKeyboardButton("🔵 Yordam", callback_data="help")],
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        await update.message.reply_text(
            "🎁 <b>Stars Gift Shop</b>\n\n"
            "Assalomu alaykum! 👋\n"
            "Kerakli bo‘limni tanlang 👇",
            parse_mode="HTML",
            reply_markup=menu()
        )

async def gifts(query, context):
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

        for i, gift in enumerate(result.gifts[:30], 1):
            stars = gift.star_count

            if stars == 15:
                price = 3000
            elif stars == 25:
                price = 5000
            elif stars == 50:
                price = 14000
            elif stars == 100:
                price = 27000
            else:
                price = stars * 95

            buttons.append([
                InlineKeyboardButton(
                    f"🎁 Gift {i} — {stars}⭐ | {price:,} so‘m".replace(",", " "),
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

async def gift_preview(query, context, gift_id):
    try:
        result = await context.bot.get_available_gifts()

        selected = None

        for gift in result.gifts:
            if str(gift.id) == str(gift_id):
                selected = gift
                break

        if selected is None:
            await query.answer("Gift topilmadi.", show_alert=True)
            return

        stars = selected.star_count

        if stars == 15:
            price = 3000
        elif stars == 25:
            price = 5000
        elif stars == 50:
            price = 14000
        elif stars == 100:
            price = 27000
        else:
            price = stars * 95

        # Gift stickeri emoji sticker bo‘lishi mumkin,
        # shuning uchun send_sticker ishlatmaymiz.
        await query.message.reply_text(
            f"🎁 <b>Gift</b>\n\n"
            f"⭐ Narxi: {stars} Stars\n"
            f"💰 Sotuv narxi: {price:,} so‘m\n\n"
            "💳 Sotib olish uchun tugmani bosing.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    "💳 Sotib olish",
                    callback_data=f"buygift:{gift_id}"
                )],
                [InlineKeyboardButton(
                    "◀️ Giftlar",
                    callback_data="gift"
                )]
            ])
        )

        await query.answer()

    except Exception as e:
        print("GIFT PREVIEW ERROR:", repr(e))
        await query.answer(
            "❌ Giftni ochishda xatolik.",
            show_alert=True
        )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    try:
        await query.answer()
    except Exception:
        pass

    data = query.data or ""

    if data == "back":
        await query.edit_message_text(
            "🎁 <b>Stars Gift Shop</b>\n\n"
            "Kerakli bo‘limni tanlang 👇",
            parse_mode="HTML",
            reply_markup=menu()
        )

    elif data == "gift":
        await gifts(query, context)

    elif data.startswith("gift:"):
        gift_id = data.split(":", 1)[1]
        await gift_preview(query, context, gift_id)

    elif data.startswith("buygift:"):
        await query.answer(
            "💳 To‘lov tizimi hali ulanmagan.",
            show_alert=True
        )

    elif data == "stars":
        await query.edit_message_text(
            "⭐ <b>Stars olish</b>\n\n"
            "100 ⭐ — 9 500 so‘m\n"
            "250 ⭐ — 23 750 so‘m\n"
            "500 ⭐ — 47 500 so‘m",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("◀️ Orqaga", callback_data="back")]
            ])
        )

    elif data == "premium":
        await query.edit_message_text(
            "💎 <b>Premium</b>\n\n"
            "Premium bo‘limi tez orada ulanadi.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("◀️ Orqaga", callback_data="back")]
            ])
        )

    elif data == "balance":
        await query.edit_message_text(
            "💰 <b>Balans</b>\n\n"
            "To‘lov tizimi ulanmoqda.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("◀️ Orqaga", callback_data="back")]
            ])
        )

    elif data == "profile":
        user = query.from_user
        await query.edit_message_text(
            f"👤 <b>Profil</b>\n\n"
            f"Ism: {user.first_name}\n"
            f"ID: <code>{user.id}</code>\n\n"
            "💰 Balans: 0 so‘m",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("◀️ Orqaga", callback_data="back")]
            ])
        )

    elif data == "help":
        await query.edit_message_text(
            "🔵 <b>Yordam</b>\n\n"
            "Administrator bilan bog‘laning.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("◀️ Orqaga", callback_data="back")]
            ])
        )

if not TOKEN:
    raise RuntimeError("BOT_TOKEN topilmadi!")

application = Application.builder().token(TOKEN).build()

application.add_handler(CommandHandler("start", start))
application.add_handler(CallbackQueryHandler(button))

application.run_polling(drop_pending_updates=True)
