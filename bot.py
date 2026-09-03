import os
import sqlite3
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
DB = "shop.db"

STARS_PACKAGES = [25, 50, 100, 125, 150, 175, 200, 300, 400, 500]


# =========================
# DATABASE
# =========================

def db():
    return sqlite3.connect(DB)


def init_db():
    con = db()

    con.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            name TEXT,
            balance INTEGER DEFAULT 0
        )
    """)

    con.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id TEXT PRIMARY KEY,
            user_id INTEGER,
            product TEXT,
            quantity INTEGER,
            price INTEGER,
            status TEXT,
            created TEXT
        )
    """)

    con.commit()
    con.close()


def save_user(user_id, name):
    con = db()

    con.execute("""
        INSERT INTO users(user_id, name)
        VALUES(?, ?)
        ON CONFLICT(user_id)
        DO UPDATE SET name=excluded.name
    """, (user_id, name))

    con.commit()
    con.close()


def create_order(user_id, product, quantity, price):
    order_id = "SGS-" + uuid.uuid4().hex[:8].upper()

    con = db()

    con.execute("""
        INSERT INTO orders
        (id, user_id, product, quantity, price, status, created)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        order_id,
        user_id,
        product,
        quantity,
        price,
        "Kutilmoqda",
        datetime.now().strftime("%d.%m.%Y %H:%M"),
    ))

    con.commit()
    con.close()

    return order_id


def get_orders(user_id):
    con = db()

    rows = con.execute("""
        SELECT id, product, quantity, price, status, created
        FROM orders
        WHERE user_id=?
        ORDER BY rowid DESC
        LIMIT 20
    """, (user_id,)).fetchall()

    con.close()
    return rows


# =========================
# NARX
# =========================

def stars_price(stars):
    return stars * 95


# =========================
# MENYU
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


def back_button(callback="back"):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("◀️ Orqaga", callback_data=callback)]
    ])


# =========================
# START
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not update.message:
        return

    user = update.effective_user

    save_user(
        user.id,
        user.first_name or ""
    )

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

async def show_stars(query):

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
        "Kerakli miqdorni tanlang 👇\n\n"
        "💵 1 ⭐ = 95 so‘m",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(buttons),
    )


# =========================
# CUSTOM STARS
# =========================

async def custom_stars(query, context):

    context.user_data["waiting_stars"] = True

    await query.edit_message_text(
        "✏️ <b>Boshqa miqdor</b>\n\n"
        "Nechta Stars kerakligini yozing.\n\n"
        "🔹 Minimum: <b>10 Stars</b>\n"
        "🔹 1 ⭐ = <b>95 so‘m</b>\n\n"
        "Masalan: <code>350</code>",
        parse_mode="HTML",
        reply_markup=back_button("stars"),
    )


async def custom_stars_message(update, context):

    if not context.user_data.get("waiting_stars"):
        return

    try:
        amount = int(update.message.text.strip())
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

    order_id = create_order(
        update.effective_user.id,
        "Stars",
        amount,
        price,
    )

    await update.message.reply_text(
        "📦 <b>Buyurtma yaratildi</b>\n\n"
        f"🆔 ID: <code>{order_id}</code>\n"
        f"⭐ Miqdor: <b>{amount} Stars</b>\n"
        f"💰 Narx: <b>{price:,} so‘m</b>\n\n"
        "📊 Holat: <b>Kutilmoqda</b>\n"
        "⏱️ Bajarilish vaqti:\n"
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
                reply_markup=back_button(),
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
                    f"{emoji} {stars}⭐ — "
                    f"{price:,} so‘m".replace(",", " "),
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
            reply_markup=back_button(),
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
            "⏱️ <b>Bajarilish vaqti</b>\n"
            "To‘lov tasdiqlangach avtomatik.\n\n"
            "📦 Buyurtma holati:\n"
            "<b>Kutilmoqda</b>",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        f"💳 Sotib olish — "
                        f"{price:,} so‘m".replace(",", " "),
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

async def show_orders(query):

    user_id = query.from_user.id
    orders = get_orders(user_id)

    if not orders:

        await query.edit_message_text(
            "📋 <b>Buyurtmalarim</b>\n\n"
            "Hozircha buyurtmalar yo‘q.",
            parse_mode="HTML",
            reply_markup=back_button(),
        )
        return

    text = "📋 <b>Buyurtmalarim</b>\n\n"

    for order in orders:

        order_id, product, quantity, price, status, created = order

        text += (
            f"🆔 <code>{order_id}</code>\n"
            f"📦 {product}\n"
            f"⭐ {quantity}\n"
            f"💰 {price:,} so‘m\n"
            f"📊 {status}\n"
            f"⏱️ {created}\n"
            "────────────\n"
        )

    await query.edit_message_text(
        text.replace(",", " "),
        parse_mode="HTML",
        reply_markup=back_button(),
    )


# =========================
# BUTTONLAR
# =========================

async def button(update: Update, context):

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
        await show_stars(query)

    elif data == "custom_stars":

        await custom_stars(query, context)

    elif data.startswith("stars:"):

        amount = int(data.split(":", 1)[1])
        price = stars_price(amount)

        order_id = create_order(
            query.from_user.id,
            "Stars",
            amount,
            price,
        )

        await query.edit_message_text(
            "📦 <b>Stars buyurtmasi</b>\n\n"
            f"🆔 ID: <code>{order_id}</code>\n"
            f"⭐ Miqdor: <b>{amount} Stars</b>\n"
            f"💰 Narx: <b>{price:,} so‘m</b>\n\n"
            "📊 Holat: <b>Kutilmoqda</b>\n"
            "⏱️ Bajarilish vaqti:\n"
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
            "💳 Click to‘lovi keyingi bosqichda ulanadi.",
            show_alert=True,
        )

    elif data == "gift":

        await show_gifts(query, context)

    elif data.startswith("gift:"):

        gift_id = data.split(":", 1)[1]
        await gift_preview(query, context, gift_id)

    elif data.startswith("buygift:"):

        await query.answer(
            "💳 Click to‘lovi keyingi bosqichda ulanadi.",
            show_alert=True,
        )

    elif data == "orders":

        await show_orders(query)

    elif data == "premium":

        await query.edit_message_text(
            "💎 <b>Premium olish</b>\n\n"
            "Premium paketlari tez orada ulanadi.\n\n"
            "⏱️ Bajarilish vaqti:\n"
            "<b>To‘lov tasdiqlangach avtomatik</b>",
            parse_mode="HTML",
            reply_markup=back_button(),
        )

    elif data == "balance":

        await query.edit_message_text(
            "💰 <b>Balansni to‘ldirish</b>\n\n"
            "Click to‘lovi keyingi bosqichda ulanadi.",
            parse_mode="HTML",
            reply_markup=back_button(),
        )

    elif data == "profile":

        user = query.from_user
        orders = get_orders(user.id)

        await query.edit_message_text(
            "👤 <b>Profil</b>\n\n"
            f"👤 Ism: {user.first_name}\n"
            f"🆔 ID: <code>{user.id}</code>\n"
            f"📋 Buyurtmalar: <b>{len(orders)}</b>\n"
            "💰 Balans: <b>0 so‘m</b>",
            parse_mode="HTML",
            reply_markup=back_button(),
        )

    elif data == "help":

        await query.edit_message_text(
            "🔵 <b>Yordam</b>\n\n"
            "Muammo bo‘lsa administrator bilan bog‘laning.\n\n"
            "📋 Buyurtma ID orqali buyurtmani aniqlash mumkin.",
            parse_mode="HTML",
            reply_markup=back_button(),
        )


# =========================
# ISHGA TUSHIRISH
# =========================

if not TOKEN:
    raise RuntimeError("BOT_TOKEN topilmadi!")

init_db()

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
