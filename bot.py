import os
import uuid
from datetime import datetime

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
# STARS NARXI
# 1 STAR = 95 SO'M
# =========================

def stars_price(stars):
    return stars * 95


STARS_PACKAGES = [25, 50, 100, 125, 150, 175, 200, 300, 400, 500]


# =========================
# ASOSIY MENYU
# =========================

def menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⭐ Stars olish", callback_data="stars")],
        [InlineKeyboardButton("🎁 Gift olish", callback_data="gift")],
        [InlineKeyboardButton("💎 Premium olish", callback_data="premium")],
        [InlineKeyboardButton("💰 Balansni to‘ldirish", callback_data="balance")],
        [InlineKeyboardButton("👤 Profil", callback_data="profile")],
        [InlineKeyboardButton("📋 Buyurtmalarim", callback_data="orders")],
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
        reply_markup=menu(),
    )


# =========================
# STARS
# =========================

async def show_stars(query, context):

    buttons = []

    for stars in STARS_PACKAGES:
        price = stars_price(stars)

        buttons.append([
            InlineKeyboardButton(
                f"⭐ {stars} Stars — {price:,} so‘m".replace(",", " "),
                callback_data=f"stars:{stars}",
            )
        ])

    buttons.append([
        InlineKeyboardButton(
            "✏️ Boshqa miqdor",
            callback_data="custom_stars",
        )
    ])

    buttons.append([
        InlineKeyboardButton(
            "◀️ Orqaga",
            callback_data="back",
        )
    ])

    await query.edit_message_text(
        "⭐ <b>Stars olish</b>\n\n"
        "Kerakli Stars miqdorini tanlang 👇",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(buttons),
    )


# =========================
# BOSHQA MIQDOR
# =========================

async def custom_stars(query, context):

    context.user_data["waiting_stars"] = True

    await query.edit_message_text(
        "✏️ <b>Boshqa miqdor</b>\n\n"
        "Nechta Stars kerakligini yozing.\n\n"
        "🔹 Minimum: <b>10 Stars</b>\n"
        "Masalan: <code>350</code>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "◀️ Orqaga",
                    callback_data="stars",
                )
            ]
        ]),
    )


async def custom_stars_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not context.user_data.get("waiting_stars"):
        return

    text = update.message.text.strip()

    try:
        amount = int(text)
    except ValueError:
        await update.message.reply_text(
            "❌ Faqat raqam yozing.\n"
            "Masalan: 350"
        )
        return

    if amount < 10:
        await update.message.reply_text(
            "❌ Minimum 10 Stars."
        )
        return

    if amount > 100000:
        await update.message.reply_text(
            "❌ Maksimum 100 000 Stars."
        )
        return

    context.user_data["waiting_stars"] = False

    price = stars_price(amount)

    await create_order_message(
        update,
        context,
        "Stars",
        amount,
        price,
    )


# =========================
# BUYURTMA YARATISH
# =========================

async def create_order_message(update, context, product, quantity, price):

    order_id = "SGS-" + uuid.uuid4().hex[:8].upper()

    order = {
        "id": order_id,
        "product": product,
        "quantity": quantity,
        "price": price,
        "status": "Kutilmoqda",
        "created": datetime.now().strftime("%d.%m.%Y %H:%M"),
    }

    orders = context.user_data.setdefault("orders", [])
    orders.append(order)

    await update.message.reply_text(
        "📦 <b>Buyurtma</b>\n\n"
        f"🆔 Buyurtma ID: <code>{order_id}</code>\n"
        f"📦 Mahsulot: <b>{product}</b>\n"
        f"⭐ Miqdor: <b>{quantity}</b>\n"
        f"💰 Narx: <b>{price:,} so‘m</b>\n\n"
        "📊 Holat: <b>Kutilmoqda</b>\n"
        "⏱️ Bajarilish vaqti: <b>To‘lov tasdiqlangach avtomatik</b>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "💳 Sotib olish",
                    callback_data=f"pay:{order_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    "◀️ Bosh menyu",
                    callback_data="back",
                )
            ],
        ]),
    )


# =========================
# GIFTLAR
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
                            callback_data="back",
                        )
                    ]
                ]),
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

            buttons.append([
                InlineKeyboardButton(
                    f"{emoji} {stars}⭐ — {price:,} so‘m".replace(",", " "),
                    callback_data=f"gift:{gift.id}",
                )
            ])

        buttons.append([
            InlineKeyboardButton(
                "◀️ Orqaga",
                callback_data="back",
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

        await query.edit_message_text(
            "❌ Giftlarni yuklashda xatolik.",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "◀️ Orqaga",
                        callback_data="back",
                    )
                ]
            ]),
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
                show_alert=True,
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

        await query.edit_message_text(
            f"{emoji} <b>Gift</b>\n\n"
            f"⭐ Gift qiymati: <b>{stars} Stars</b>\n"
            f"💰 Sotuv narxi: <b>{price:,} so‘m</b>\n\n"
            "📦 Bajarilish vaqti:\n"
            "<b>To‘lov tasdiqlangach avtomatik</b>",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        f"💳 Sotib olish — {price:,} so‘m".replace(",", " "),
                        callback_data=f"buygift:{selected.id}",
                    )
                ],
                [
                    InlineKeyboardButton(
                        "◀️ Giftlar",
                        callback_data="gift",
                    )
                ],
            ]),
        )

    except Exception as e:
        print("GIFT PREVIEW ERROR:", repr(e))

        await query.answer(
            "❌ Giftni ochishda xatolik.",
            show_alert=True,
        )


# =========================
# BUYURTMALAR
# =========================

async def show_orders(query, context):

    orders = context.user_data.get("orders", [])

    if not orders:
        await query.edit_message_text(
            "📋 <b>Buyurtmalarim</b>\n\n"
            "Hozircha buyurtmalar yo‘q.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "◀️ Orqaga",
                        callback_data="back",
                    )
                ]
            ]),
        )
        return

    text = "📋 <b>Buyurtmalarim</b>\n\n"

    for order in orders[-10:][::-1]:

        text += (
            f"🆔 <code>{order['id']}</code>\n"
            f"📦 {order['product']}\n"
            f"⭐ {order['quantity']}\n"
            f"💰 {order['price']:,} so‘m\n"
            f"📊 {order['status']}\n"
            f"⏱️ {order['created']}\n\n"
        )

    await query.edit_message_text(
        text.replace(",", " "),
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "◀️ Orqaga",
                    callback_data="back",
                )
            ]
        ]),
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

    if data == "back":

        context.user_data["waiting_stars"] = False

        await query.edit_message_text(
            "🎁 <b>Stars Gift Shop</b>\n\n"
            "Kerakli bo‘limni tanlang 👇",
            parse_mode="HTML",
            reply_markup=menu(),
        )

    elif data == "stars":

        context.user_data["waiting_stars"] = False
        await show_stars(query, context)

    elif data == "custom_stars":

        await custom_stars(query, context)

    elif data.startswith("stars:"):

        amount = int(data.split(":", 1)[1])
        price = stars_price(amount)

        order_id = "SGS-" + uuid.uuid4().hex[:8].upper()

        order = {
            "id": order_id,
            "product": "Stars",
            "quantity": amount,
            "price": price,
            "status": "Kutilmoqda",
            "created": datetime.now().strftime("%d.%m.%Y %H:%M"),
        }

        orders = context.user_data.setdefault("orders", [])
        orders.append(order)

        await query.edit_message_text(
            "📦 <b>Stars buyurtmasi</b>\n\n"
            f"🆔 ID: <code>{order_id}</code>\n"
            f"⭐ Miqdor: <b>{amount} Stars</b>\n"
            f"💰 Narx: <b>{price:,} so‘m</b>\n\n"
            "📊 Holat: <b>Kutilmoqda</b>\n"
            "⏱️ Bajarilish vaqti: "
            "<b>To‘lov tasdiqlangach avtomatik</b>",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "💳 Sotib olish",
                        callback_data=f"pay:{order_id}",
                    )
                ],
                [
                    InlineKeyboardButton(
                        "◀️ Stars",
                        callback_data="stars",
                    )
                ],
            ]),
        )

    elif data.startswith("pay:"):

        await query.answer(
            "💳 To‘lov tizimi keyingi bosqichda ulanadi.",
            show_alert=True,
        )

    elif data == "gift":

        await show_gifts(query, context)

    elif data.startswith("gift:"):

        gift_id = data.split(":", 1)[1]
        await gift_preview(query, context, gift_id)

    elif data.startswith("buygift:"):

        await query.answer(
            "💳 To‘lov tizimi keyingi bosqichda ulanadi.",
            show_alert=True,
        )

    elif data == "orders":

        await show_orders(query, context)

    elif data == "premium":

        await query.edit_message_text(
            "💎 <b>Premium</b>\n\n"
            "Premium paketlari tez orada ulanadi.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "◀️ Orqaga",
                        callback_data="back",
                    )
                ]
            ]),
        )

    elif data == "balance":

        await query.edit_message_text(
            "💰 <b>Balansni to‘ldirish</b>\n\n"
            "Click to‘lovi keyingi bosqichda ulanadi.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "◀️ Orqaga",
                        callback_data="back",
                    )
                ]
            ]),
        )

    elif data == "profile":

        user = query.from_user

        orders = context.user_data.get("orders", [])

        await query.edit_message_text(
            "👤 <b>Profil</b>\n\n"
            f"👤 Ism: {user.first_name}\n"
            f"🆔 ID: <code>{user.id}</code>\n"
            f"📋 Buyurtmalar: <b>{len(orders)}</b>\n\n"
            "💰 Balans: <b>0 so‘m</b>",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "◀️ Orqaga",
                        callback_data="back",
                    )
                ]
            ]),
        )

    elif data == "help":

        await query.edit_message_text(
            "🔵 <b>Yordam</b>\n\n"
            "Muammo bo‘lsa administrator bilan bog‘laning.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "◀️ Orqaga",
                        callback_data="back",
                    )
                ]
            ]),
        )


# =========================
# ISHGA TUSHIRISH
# =========================

if not TOKEN:
    raise RuntimeError("BOT_TOKEN topilmadi!")

application = Application.builder().token(TOKEN).build()

application.add_handler(
    CommandHandler("start", start)
)

application.add_handler(
    MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        custom_stars_message,
    )
)

application.add_handler(
    CallbackQueryHandler(button)
)

application.run_polling(
    drop_pending_updates=True
        )
