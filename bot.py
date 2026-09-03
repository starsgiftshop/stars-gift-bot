import os
import sqlite3
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)

TOKEN = os.getenv("BOT_TOKEN")

STARS_PRICE = 195
MIN_STARS = 10
MAX_STARS = 100000
ADMIN_URL = "https://t.me/Shamsbekman"
DB_FILE = "shop.db"

PREMIUM = {
    "1 oy": 45000,
    "3 oy": 164000,
    "6 oy": 222000,
    "1 yil": 377000,
}

STARS_PACKAGES = [25, 50, 100, 125, 150, 175, 200, 300, 400, 500]


def money(value):
    return f"{value:,}".replace(",", " ")


def init_db():
    con = sqlite3.connect(DB_FILE)
    con.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product TEXT NOT NULL,
            amount INTEGER NOT NULL,
            price INTEGER NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    con.commit()
    con.close()


def create_order(user_id, product, amount, price):
    con = sqlite3.connect(DB_FILE)
    cur = con.cursor()

    cur.execute("""
        INSERT INTO orders
        (user_id, product, amount, price, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        product,
        amount,
        price,
        "pending",
        datetime.now().isoformat(timespec="seconds"),
    ))

    order_id = cur.lastrowid
    con.commit()
    con.close()

    return order_id


def user_order_count(user_id):
    con = sqlite3.connect(DB_FILE)

    count = con.execute(
        "SELECT COUNT(*) FROM orders WHERE user_id = ?",
        (user_id,)
    ).fetchone()[0]

    con.close()
    return count


def recent_orders(user_id, limit=5):
    con = sqlite3.connect(DB_FILE)

    rows = con.execute("""
        SELECT id, product, price, status
        FROM orders
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT ?
    """, (user_id, limit)).fetchall()

    con.close()
    return rows


def main_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("⭐ Stars", callback_data="stars"),
            InlineKeyboardButton("🎁 Gift", callback_data="gifts"),
            InlineKeyboardButton("💎 Premium", callback_data="premium"),
        ],
        [
            InlineKeyboardButton("💰 Balans", callback_data="balance"),
            InlineKeyboardButton("👤 Profil", callback_data="profile"),
            InlineKeyboardButton("📋 Buyurtma", callback_data="orders"),
        ],
        [
            InlineKeyboardButton("🔵 Yordam", callback_data="help"),
            InlineKeyboardButton("ℹ️ Ma'lumot", callback_data="info"),
            InlineKeyboardButton("⚙️ Sozlama", callback_data="settings"),
        ],
    ])


def home_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🏠 Bosh menyu",
                callback_data="home"
            )
        ]
    ])


async def edit_menu(query, text, keyboard):
    await query.edit_message_text(
        text=text,
        parse_mode=ParseMode.HTML,
        reply_markup=keyboard,
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()

    await update.message.reply_text(
        "🌟 <b>Stars Gift Shop</b>\n\n"
        "Kerakli xizmatni tanlang:\n\n"
        "⚡ O'rtacha bajarilish: <b>30 soniya</b>\n"
        "💵 1 ⭐ = <b>195 so'm</b>",
        parse_mode=ParseMode.HTML,
        reply_markup=main_keyboard(),
    )


async def show_stars(query):
    rows = []
    row = []

    for stars_count in STARS_PACKAGES:
        row.append(
            InlineKeyboardButton(
                f"⭐ {stars_count}",
                callback_data=f"stars_buy:{stars_count}"
            )
        )

        if len(row) == 3:
            rows.append(row)
            row = []

    if row:
        rows.append(row)

    rows.append([
        InlineKeyboardButton(
            "✏️ Boshqa miqdor",
            callback_data="custom_stars"
        )
    ])

    rows.append([
        InlineKeyboardButton(
            "🏠 Bosh menyu",
            callback_data="home"
        )
    ])

    text = (
        "⭐ <b>Stars</b>\n\n"
        "25 ⭐ — 4 875 so'm\n"
        "50 ⭐ — 9 750 so'm\n"
        "100 ⭐ — 19 500 so'm\n"
        "125 ⭐ — 24 375 so'm\n"
        "150 ⭐ — 29 250 so'm\n"
        "175 ⭐ — 34 125 so'm\n"
        "200 ⭐ — 39 000 so'm\n"
        "300 ⭐ — 58 500 so'm\n"
        "400 ⭐ — 78 000 so'm\n"
        "500 ⭐ — 97 500 so'm\n\n"
        "⚡ O'rtacha bajarilish: <b>30 soniya</b>"
    )

    await edit_menu(
        query,
        text,
        InlineKeyboardMarkup(rows)
    )


async def show_gifts(query, context):
    try:
        result = await context.bot.get_available_gifts()
        gifts = result.gifts if result else []

        if not gifts:
            await edit_menu(
                query,
                "🎁 <b>Gift</b>\n\n"
                "Hozircha mavjud Gift topilmadi.",
                home_keyboard(),
            )
            return

        rows = []

        for gift in gifts[:30]:
            icon = getattr(gift.sticker, "emoji", None) or "🎁"
            price = getattr(gift, "star_count", 0)
            callback = f"gift:{gift.id}"

            if len(callback.encode("utf-8")) <= 64:
                rows.append([
                    InlineKeyboardButton(
                        f"{icon} {price} ⭐",
                        callback_data=callback
                    )
                ])

        rows.append([
            InlineKeyboardButton(
                "🏠 Bosh menyu",
                callback_data="home"
            )
        ])

        await edit_menu(
            query,
            "🎁 <b>Gift</b>\n\n"
            "Kerakli Giftni tanlang:\n\n"
            "⚡ To'lov tizimi ulangach avtomatik yetkazib beriladi.",
            InlineKeyboardMarkup(rows),
        )

    except Exception as exc:
        print("GIFT ERROR:", repr(exc))

        await edit_menu(
            query,
            "🎁 <b>Gift</b>\n\n"
            "Giftlarni yuklashda xatolik yuz berdi.",
            home_keyboard(),
        )


async def show_premium(query):
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "💎 1 oy",
                callback_data="premium_buy:1 oy"
            ),
            InlineKeyboardButton(
                "💎 3 oy",
                callback_data="premium_buy:3 oy"
            ),
        ],
        [
            InlineKeyboardButton(
                "💎 6 oy",
                callback_data="premium_buy:6 oy"
            ),
            InlineKeyboardButton(
                "💎 1 yil",
                callback_data="premium_buy:1 yil"
            ),
        ],
        [
            InlineKeyboardButton(
                "🏠 Bosh menyu",
                callback_data="home"
            )
        ],
    ])

    text = (
        "💎 <b>Telegram Premium</b>\n\n"
        "💎 1 oy — <b>45 000 so'm</b>\n"
        "💎 3 oy — <b>164 000 so'm</b>\n"
        "💎 6 oy — <b>222 000 so'm</b>\n"
        "💎 1 yil — <b>377 000 so'm</b>\n\n"
        "⚡ To'lov tasdiqlangach avtomatik yetkazib berish ulanadi."
    )

    await edit_menu(
        query,
        text,
        keyboard
    )


async def show_balance(query):
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🟢 Payme",
                callback_data="balance_pay:Payme"
            ),
            InlineKeyboardButton(
                "🔵 Click",
                callback_data="balance_pay:Click"
            ),
        ],
        [
            InlineKeyboardButton(
                "💳 Uzcard",
                callback_data="balance_pay:Uzcard"
            ),
            InlineKeyboardButton(
                "💳 Humo",
                callback_data="balance_pay:Humo"
            ),
        ],
        [
            InlineKeyboardButton(
                "🪙 TON",
                callback_data="balance_pay:TON"
            ),
        ],
        [
            InlineKeyboardButton(
                "🏠 Bosh menyu",
                callback_data="home"
            )
        ],
    ])

    await edit_menu(
        query,
        "💰 <b>Balans</b>\n\n"
        "To'lov usulini tanlang:\n\n"
        "🟢 Payme\n"
        "🔵 Click\n"
        "💳 Uzcard\n"
        "💳 Humo\n"
        "🪙 TON\n\n"
        "ℹ️ Real API ma'lumotlari ulangach to'lov avtomatik tasdiqlanadi.",
        keyboard,
    )


async def show_profile(query):
    user = query.from_user
    count = user_order_count(user.id)

    await edit_menu(
        query,
        "👤 <b>Profil</b>\n\n"
        f"🆔 ID: <code>{user.id}</code>\n"
        f"👤 Ism: {user.first_name or '-'}\n"
        f"🔗 Username: @{user.username or '-'}\n"
        f"📦 Buyurtmalar: <b>{count}</b>",
        home_keyboard(),
    )


async def show_orders(query):
    rows = recent_orders(query.from_user.id)

    if not rows:
        text = (
            "📋 <b>Buyurtmalar</b>\n\n"
            "Hozircha buyurtma yo'q."
        )
    else:
        text = "📋 <b>So'nggi buyurtmalar</b>\n\n"

        for order_id, product, price, status in rows:
            status_text = {
                "pending": "⏳ Kutilmoqda",
                "paid": "✅ To'langan",
                "completed": "🎉 Bajarildi",
                "cancelled": "❌ Bekor qilingan",
            }.get(status, status)

            text += (
                f"🆔 <b>#{order_id}</b> — {product}\n"
                f"💵 {money(price)} so'm\n"
                f"{status_text}\n\n"
            )

    await edit_menu(
        query,
        text,
        home_keyboard()
    )


async def show_help(query):
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "👨‍💻 Admin bilan bog'lanish",
                url=ADMIN_URL
            )
        ],
        [
            InlineKeyboardButton(
                "🏠 Bosh menyu",
                callback_data="home"
            )
        ],
    ])

    await edit_menu(
        query,
        "🔵 <b>Yordam</b>\n\n"
        "Savol yoki muammo bo'lsa admin bilan bog'laning:\n"
        "@Shamsbekman",
        keyboard,
    )


async def show_info(query):
    await edit_menu(
        query,
        "ℹ️ <b>Ma'lumot</b>\n\n"
        "🌟 Stars Gift Shop\n"
        "⭐ Stars\n"
        "🎁 Telegram Gift\n"
        "💎 Telegram Premium\n\n"
        "⚡ O'rtacha bajarilish: <b>30 soniya</b>",
        home_keyboard(),
    )


async def show_settings(query):
    await edit_menu(
        query,
        "⚙️ <b>Sozlamalar</b>\n\n"
        "Hozircha qo'shimcha sozlamalar mavjud emas.",
        home_keyboard(),
    )


async def show_payment(query, context):
    order_id = context.user_data.get("order_id")

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🟢 Payme",
                callback_data=f"checkout:Payme:{order_id}"
            ),
            InlineKeyboardButton(
                "🔵 Click",
                callback_data=f"checkout:Click:{order_id}"
            ),
        ],
        [
            InlineKeyboardButton(
                "💳 Uzcard",
                callback_data=f"checkout:Uzcard:{order_id}"
            ),
            InlineKeyboardButton(
                "💳 Humo",
                callback_data=f"checkout:Humo:{order_id}"
            ),
        ],
        [
            InlineKeyboardButton(
                "🪙 TON",
                callback_data=f"checkout:TON:{order_id}"
            ),
        ],
        [
            InlineKeyboardButton(
                "🏠 Bosh menyu",
                callback_data="home"
            )
        ],
    ])

    await edit_menu(
        query,
        "💳 <b>To'lov</b>\n\n"
        f"🆔 Buyurtma: <b>#{order_id}</b>\n\n"
        "To'lov usulini tanlang.\n\n"
        "⚠️ Real Merchant/API hali ulanmagan. "
        "Soxta to'lov tasdiqlanmaydi.",
        keyboard,
    )


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    await query.answer()

    data = query.data or ""

    try:
        if data == "home":
            context.user_data.clear()

            await edit_menu(
                query,
                "🌟 <b>Stars Gift Shop</b>\n\n"
                "Kerakli xizmatni tanlang:\n\n"
                "⚡ O'rtacha bajarilish: <b>30 soniya</b>",
                main_keyboard(),
            )

        elif data == "stars":
            context.user_data.pop("waiting_stars", None)
            await show_stars(query)

        elif data == "gifts":
            await show_gifts(query, context)

        elif data == "premium":
            await show_premium(query)

        elif data == "balance":
            await show_balance(query)

        elif data == "profile":
            await show_profile(query)

        elif data == "orders":
            await show_orders(query)

        elif data == "help":
            await show_help(query)

        elif data == "info":
            await show_info(query)

        elif data == "settings":
            await show_settings(query)

        elif data == "custom_stars":
            context.user_data["waiting_stars"] = True

            await edit_menu(
                query,
                "✏️ <b>Stars miqdorini kiriting</b>\n\n"
                f"Minimal: <b>{MIN_STARS}</b> ⭐\n"
                f"Maksimal: <b>{MAX_STARS}</b> ⭐\n\n"
                "Masalan: <code>150</code>",
                InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton(
                            "❌ Bekor qilish",
                            callback_data="stars"
                        )
                    ]
                ]),
            )

        elif data.startswith("stars_buy:"):
            stars_count = int(data.split(":", 1)[1])
            price = stars_count * STARS_PRICE

            order_id = create_order(
                query.from_user.id,
                f"{stars_count} Stars",
                stars_count,
                price,
            )

            context.user_data["order_id"] = order_id

            await edit_menu(
                query,
                "⭐ <b>Stars buyurtmasi</b>\n\n"
                f"⭐ Miqdor: <b>{stars_count}</b>\n"
                f"💵 Narx: <b>{money(price)} so'm</b>\n"
                f"🆔 Buyurtma: <b>#{order_id}</b>",
                InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton(
                            "💳 To'lovni tanlash",
                            callback_data="payment"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "⬅️ Orqaga",
                            callback_data="stars"
                        )
                    ],
                ]),
            )

        elif data.startswith("premium_buy:"):
            package = data.split(":", 1)[1]
            price = PREMIUM[package]

            order_id = create_order(
                query.from_user.id,
                f"Premium {package}",
                1,
                price,
            )

            context.user_data["order_id"] = order_id

            await edit_menu(
                query,
                "💎 <b>Premium buyurtmasi</b>\n\n"
                f"📦 Paket: <b>{package}</b>\n"
                f"💵 Narx: <b>{money(price)} so'm</b>\n"
                f"🆔 Buyurtma: <b>#{order_id}</b>",
                InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton(
                            "💳 To'lovni tanlash",
                            callback_data="payment"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "⬅️ Orqaga",
                            callback_data="premium"
                        )
                    ],
                ]),
            )

        elif data.startswith("gift:"):
            gift_id = data.split(":", 1)[1]

            context.user_data["gift_id"] = gift_id

            order_id = create_order(
                query.from_user.id,
                f"Gift {gift_id}",
                1,
                0,
            )

            context.user_data["order_id"] = order_id

            await edit_menu(
                query,
                "🎁 <b>Gift buyurtmasi</b>\n\n"
                f"🎁 Gift ID: <code>{gift_id}</code>\n"
                f"🆔 Buyurtma: <b>#{order_id}</b>\n\n"
                "To'lov usulini tanlang:",
                InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton(
                            "💳 To'lovni tanlash",
                            callback_data="payment"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "⬅️ Orqaga",
                            callback_data="gifts"
                        )
                    ],
                ]),
            )

        elif data == "payment":
            await show_payment(query, context)

        elif data.startswith("balance_pay:"):
            method = data.split(":", 1)[1]

            await query.answer(
                f"{method} API keyin ulanadi.",
                show_alert=True
            )

        elif data.startswith("checkout:"):
            method = data.split(":")[1]

            await query.answer(
                "Real to'lov API hali ulanmagan.",
                show_alert=True
            )

            await edit_menu(
                query,
                "⏳ <b>To'lov moduli</b>\n\n"
                f"💳 Usul: <b>{method}</b>\n\n"
                "Merchant/API ma'lumotlari ulangach "
                "haqiqiy to'lov oynasi shu yerda ishlaydi.\n\n"
                "⚠️ Soxta to'lov tasdiqlanmaydi.",
                home_keyboard(),
            )

    except Exception as exc:
        print("BUTTON ERROR:", repr(exc))

        try:
            await query.answer(
                "❌ Xatolik yuz berdi.",
                show_alert=True
            )
        except Exception:
            pass


async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("waiting_stars"):
        return

    try:
        stars_count = int(update.message.text.strip())
    except ValueError:
        await update.message.reply_text(
            "❌ Faqat raqam yuboring. Masalan: 150"
        )
        return

    if not MIN_STARS <= stars_count <= MAX_STARS:
        await update.message.reply_text(
            f"❌ {MIN_STARS} dan {MAX_STARS} gacha kiriting."
        )
        return

    context.user_data["waiting_stars"] = False

    price = stars_count * STARS_PRICE

    order_id = create_order(
        update.effective_user.id,
        f"{stars_count} Stars",
        stars_count,
        price,
    )

    context.user_data["order_id"] = order_id

    await update.message.reply_text(
        "⭐ <b>Stars buyurtmasi</b>\n\n"
        f"⭐ Miqdor: <b>{stars_count:,}</b>\n"
        f"💵 Narx: <b>{money(price)} so'm</b>\n"
        f"🆔 Buyurtma: <b>#{order_id}</b>",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "💳 To'lovni tanlash",
                    callback_data="payment"
                )
            ],
            [
                InlineKeyboardButton(
                    "⭐ Stars",
                    callback_data="stars"
                )
            ],
        ]),
    )


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    print("BOT ERROR:", repr(context.error))


if n:
