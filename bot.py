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

STAR_PRICE = 195
MIN_CUSTOM_STARS = 10
MAX_CUSTOM_STARS = 100000

STARS_PACKAGES = [25, 50, 100, 125, 150, 175, 200, 300, 400, 500]

PREMIUM_PACKAGES = [
    ("1 oy", 45000),
    ("3 oy", 164000),
    ("6 oy", 222000),
    ("1 yil", 377000),
]


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
            user_id INTEGER NOT NULL,
            product TEXT NOT NULL,
            quantity TEXT,
            price INTEGER NOT NULL,
            status TEXT NOT NULL,
            created TEXT NOT NULL
        )
    """)

    con.commit()
    con.close()


def save_user(user_id, name):
    con = db()

    con.execute("""
        INSERT INTO users(user_id, name)
        VALUES (?, ?)
        ON CONFLICT(user_id)
        DO UPDATE SET name = excluded.name
    """, (user_id, name))

    con.commit()
    con.close()


def get_balance(user_id):
    con = db()

    row = con.execute(
        "SELECT balance FROM users WHERE user_id = ?",
        (user_id,)
    ).fetchone()

    con.close()

    return row[0] if row else 0


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
        str(quantity),
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
        WHERE user_id = ?
        ORDER BY rowid DESC
        LIMIT 20
    """, (user_id,)).fetchall()

    con.close()
    return rows


def money(number):
    return f"{number:,}".replace(",", " ")


def stars_price(stars):
    return stars * STAR_PRICE


# =========================
# MENU
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
    user = update.effective_user

    save_user(user.id, user.first_name or "")
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

async def show_stars(query):
    buttons = []

    for stars in STARS_PACKAGES:
        price = stars_price(stars)

        buttons.append([
            InlineKeyboardButton(
                f"⭐ {stars} Stars — {money(price)} so‘m",
                callback_data=f"stars:{stars}"
            )
        ])

    buttons.append([
        InlineKeyboardButton(
            "✏️ Boshqa miqdor",
            callback_data="custom_stars"
        )
    ])

    buttons.append([
        InlineKeyboardButton("◀️ Orqaga", callback_data="back")
    ])

    await query.edit_message_text(
        "⭐ <b>Stars olish</b>\n\n"
        "💵 1 ⭐ = <b>195 so‘m</b>\n"
        "⏱️ Bajarilish vaqti: <b>o‘rtacha 30 soniya</b>\n\n"
        "Kerakli miqdorni tanlang 👇",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(buttons)
    )


async def custom_stars(query, context):
    context.user_data["waiting_stars"] = True

    await query.edit_message_text(
        "✏️ <b>Boshqa miqdor</b>\n\n"
        f"🔹 Minimum: <b>{MIN_CUSTOM_STARS}</b> Stars\n"
        f"🔹 Maksimum: <b>{MAX_CUSTOM_STARS}</b> Stars\n"
        "💵 1 ⭐ = <b>195 so‘m</b>\n\n"
        "Nechta Stars kerakligini yozing.\n"
        "Masalan: <code>350</code>",
        parse_mode="HTML",
        reply_markup=back_button("stars")
    )


async def custom_stars_message(update, context):
    if not context.user_data.get("waiting_stars"):
        return

    try:
        amount = int(update.message.text.strip())
    except ValueError:
        await update.message.reply_text(
            "❌ Faqat raqam yozing.\nMasalan: 350"
        )
        return

    if amount < MIN_CUSTOM_STARS:
        await update.message.reply_text(
            f"❌ Minimum {MIN_CUSTOM_STARS} Stars."
        )
        return

    if amount > MAX_CUSTOM_STARS:
        await update.message.reply_text(
            f"❌ Maksimum {MAX_CUSTOM_STARS} Stars."
        )
        return

    context.user_data["waiting_stars"] = False

    price = stars_price(amount)

    order_id = create_order(
        update.effective_user.id,
        "Stars",
        amount,
        price
    )

    await update.message.reply_text(
        "📦 <b>Buyurtma yaratildi</b>\n\n"
        f"🆔 ID: <code>{order_id}</code>\n"
        f"⭐ Miqdor: <b>{amount} Stars</b>\n"
        f"💰 Narx: <b>{money(price)} so‘m</b>\n"
        "📊 Holat: <b>Kutilmoqda</b>\n"
        "⏱️ Bajarilish: <b>o‘rtacha 30 soniya</b>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(
                "💳 Sotib olish",
                callback_data=f"pay:{order_id}"
            )],
            [InlineKeyboardButton(
                "◀️ Stars",
                callback_data="stars"
            )]
        ])
    )


# =========================
# GIFT
# =========================

async def show_gifts(query, context):
    try:
        result = await context.bot.get_available_gifts()

        if not result or not result.gifts:
            await query.edit_message_text(
                "🎁 Hozircha Gift mavjud emas.",
                reply_markup=back_button()
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
                    f"{emoji} {stars}⭐ — {money(price)} so‘m",
                    callback_data=f"gift:{gift.id}"
                )
            ])

        buttons.append([
            InlineKeyboardButton("◀️ Orqaga", callback_data="back")
        ])

        await query.edit_message_text(
            "🎁 <b>Giftlar</b>\n\n"
            "💵 1 ⭐ = <b>195 so‘m</b>\n"
            "⏱️ Bajarilish vaqti: <b>o‘rtacha 30 soniya</b>\n\n"
            "Kerakli Giftni tanlang 👇",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    except Exception as e:
        print("GIFTS ERROR:", repr(e))

        await query.edit_message_text(
            "❌ Giftlarni yuklashda xatolik.\n\n"
            "Keyinroq qayta urinib ko‘ring.",
            reply_markup=back_button()
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

        await query.edit_message_text(
            f"{emoji} <b>Gift</b>\n\n"
            f"⭐ Qiymati: <b>{stars} Stars</b>\n"
            f"💰 Narxi: <b>{money(price)} so‘m</b>\n\n"
            "⏱️ Bajarilish: <b>o‘rtacha 30 soniya</b>\n"
            "📊 Holat: <b>Kutilmoqda</b>",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    f"💳 Sotib olish — {money(price)} so‘m",
                    callback_data=f"buygift:{selected.id}"
                )],
                [InlineKeyboardButton(
                    "◀️ Giftlar",
                    callback_data="gift"
                )]
            ])
        )

    except Exception as e:
        print("GIFT ERROR:", repr(e))

        await query.answer(
            "❌ Giftni ochishda xatolik.",
            show_alert=True
        )


# =========================
# PREMIUM
# =========================

async def show_premium(query):
    buttons = []

    for name, price in PREMIUM_PACKAGES:
        buttons.append([
            InlineKeyboardButton(
                f"💎 {name} — {money(price)} so‘m",
                callback_data=f"premium:{name}"
            )
        ])

    buttons.append([
        InlineKeyboardButton("◀️ Orqaga", callback_data="back")
    ])

    await query.edit_message_text(
        "💎 <b>Telegram Premium</b>\n\n"
        "Kerakli paketni tanlang 👇\n\n"
        "⏱️ Bajarilish vaqti: <b>o‘rtacha 30 soniya</b>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(buttons)
    )


async def premium_preview(query, package):
    price = None

    for name, package_price in PREMIUM_PACKAGES:
        if name == package:
            price = package_price
            break

    if price is None:
        await query.answer(
            "Paket topilmadi.",
            show_alert=True
        )
        return

    await query.edit_message_text(
        "💎 <b>Premium buyurtmasi</b>\n\n"
        f"📦 Paket: <b>{package}</b>\n"
        f"💰 Narx: <b>{money(price)} so‘m</b>\n\n"
        "⏱️ Bajarilish: <b>o‘rtacha 30 soniya</b>\n"
        "📊 Holat: <b>Kutilmoqda</b>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(
                "💳 Sotib olish",
                callback_data=f"buy_premium:{package}"
            )],
            [InlineKeyboardButton(
                "◀️ Premium",
                callback_data="premium"
            )]
        ])
    )


# =========================
# BALANCE
# =========================

async def show_balance(query):
    await query.edit_message_text(
        "💰 <b>Balansni to‘ldirish</b>\n\n"
        "To‘lov usulini tanlang 👇",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🟢 Payme", callback_data="payme")],
            [InlineKeyboardButton("🔵 Click", callback_data="click")],
            [InlineKeyboardButton("💳 Uzcard", callback_data="uzcard")],
            [InlineKeyboardButton("💳 Humo", callback_data="humo")],
            [InlineKeyboardButton("◀️ Orqaga", callback_data="back")],
        ])
    )


async def payment_method(query, method):
    names = {
        "payme": "🟢 Payme",
        "click": "🔵 Click",
        "uzcard": "💳 Uzcard",
        "humo": "💳 Humo",
    }

    name = names.get(method, "To‘lov")

    await query.edit_message_text(
        f"{name}\n\n"
        "💰 Balansni to‘ldirish\n\n"
        "⚙️ Avtomatik to‘lov tizimi ulanmoqda.\n"
        "To‘lov integratsiyasi ulangandan keyin "
        "bu tugma orqali avtomatik to‘lov qilinadi.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(
                "◀️ To‘lov usullari",
                callback_data="balance"
            )]
        ])
    )


# =========================
# ORDERS
# =========================

async def show_orders(query):
    orders = get_orders(query.from_user.id)

    if not orders:
        await query.edit_message_text(
            "📋 <b>Buyurtmalarim</b>\n\n"
            "Hozircha buyurtmalar yo‘q.",
            parse_mode="HTML",
            reply_markup=back_button()
        )
        return

    text = "📋 <b>Buyurtmalarim</b>\n\n"

    for order in orders:
        order_id, product, quantity, price, status, created = order

        text += (
            f"🆔 <code>{order_id}</code>\n"
            f"📦 {product}\n"
            f"⭐ {quantity}\n"
            f"💰 {money(price)} so‘m\n"
            f"📊 {status}\n"
            f"⏱️ Bajarilish: o‘rtacha 30 soniya\n"
            f"🕐 {created}\n"
            "────────────\n"
        )

    await query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=back_button()
    )


# =========================
# PROFILE
# =========================

async def show_profile(query):
    user = query.from_user

    save_user(user.id, user.first_name or "")

    orders = get_orders(user.id)
    balance = get_balance(user.id)

    await query.edit_message_text(
        "👤 <b>Profil</b>\n\n"
        f"👤 Ism: {user.first_name}\n"
        f"🆔 ID: <code>{user.id}</code>\n"
        f"📋 Buyurtmalar: <b>{len(orders)}</b>\n"
        f"💰 Balans: <b>{money(balance)} so‘m</b>",
        parse_mode="HTML",
        reply_markup=back_button()
    )


# =========================
# HELP
# =========================

async def show_help(query):
    await query.edit_message_text(
        "🔵 <b>Yordam</b>\n\n"
        "Savol yoki muammo bo‘lsa administrator bilan bog‘laning.\n\n"
        "👨‍💻 Administrator: @Shamsbekman",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(
                "👨‍💻 Administrator",
                url="https://t.me/Shamsbekman"
            )],
            [InlineKeyboardButton(
                "◀️ Orqaga",
                callback_data="back"
            )]
        ])
    )


# =========================
# BUTTONS
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
            reply_markup=menu()
        )

    elif data == "stars":
        context.user_data["waiting_stars"] = False
        await show_stars(query)

    elif data == "custom_stars":
        await custom_stars(query, context)

    elif data.startswith("stars:"):
        try:
            amount = int(data.split(":", 1)[1])
        except ValueError:
            await query.answer("Xatolik", show_alert=True)
            return

        price = stars_price(amount)

        order_id = create_order(
            query.from_user.id,
            "Stars",
            amount,
            price
        )

        await query.edit_message_text(
            "📦 <b>Stars buyurtmasi</b>\n\n"
            f"🆔 ID: <code>{order_id}</code>\n"
            f"⭐ Miqdor: <b>{amount} Stars</b>\n"
            f"💰 Narx: <b>{money(price)} so‘m</b>\n\n"
            "📊 Holat: <b>Kutilmoqda</b>\n"
            "⏱️ Bajarilish: <b>o‘rtacha 30 soniya</b>",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    "💳 Sotib olish",
                    callback_data=f"pay:{order_id}"
                )],
                [InlineKeyboardButton(
                    "◀️ Stars",
                    callback_data="stars"
                )]
            ])
        )

    elif data.startswith("pay:"):
        await query.answer(
            "💳 To‘lov tizimi ulanmoqda.",
            show_alert=True
        )

    elif data == "gift":
        await show_gifts(query, context)

    elif data.startswith("gift:"):
        gift_id = data.split(":", 1)[1]
        await gift_preview(query, context, gift_id)

    elif data.startswith("buygift:"):
        await query.answer(
            "💳 Gift uchun avtomatik to‘lov ulanmoqda.",
            show_alert=True
        )

    elif data == "premium":
        await show_premium(query)

    elif data.startswith("premium:"):
        package = data.split(":", 1)[1]
        await premium_preview(query, package)

    elif data.startswith("buy_premium:"):
        await query.answer(
            "💳 Premium uchun avtomatik to‘lov ulanmoqda.",
            show_alert=True
        )

    elif data == "balance":
        await show_balance(query)

    elif data in ("payme", "click", "uzcard", "humo"):
        await payment_method(query, data)

    elif data == "orders":
        await show_orders(query)

    elif data == "profile":
        await show_profile(query)

    elif data == "help":
        await show_help(query)


# =========================
# ERROR
# =========================

async def error_handler(update, context):
    print("BOT ERROR:", repr(context.error))


# =========================
# START BOT
# =========================

if not TOKEN:
    raise RuntimeError("BOT_TOKEN topilmadi!")

init_db()

application = Application.builder().token(TOKEN).build()

application.add_handler(CommandHandler("start", start))

application.add_handler(
    CallbackQueryHandler(button)
)

application.add_handler(
    MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        custom_stars_message
    )
)

application.add_error_handler(error_handler)

print("Stars Gift Shop ishga tushdi!")

application.run_polling(
    drop_pending_updates=True
    )
