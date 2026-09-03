import os
import sqlite3
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

TOKEN = os.getenv("BOT_TOKEN")
DB_FILE = "shop.db"
STARS_PRICE = 195
MIN_STARS = 10
MAX_STARS = 100000
ADMIN_URL = "https://t.me/Shamsbekman"

PREMIUM = {
    "1 oy": 45000,
    "3 oy": 164000,
    "6 oy": 222000,
    "1 yil": 377000,
}

PACKAGES = [25, 50, 100, 125, 150, 175, 200, 300, 400, 500]


def money(value):
    return f"{value:,}".replace(",", " ")


def init_db():
    con = sqlite3.connect(DB_FILE)
    con.execute(
        """CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product TEXT NOT NULL,
            amount INTEGER NOT NULL,
            price INTEGER NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL
        )"""
    )
    con.commit()
    con.close()


def create_order(user_id, product, amount, price):
    con = sqlite3.connect(DB_FILE)
    cur = con.cursor()
    cur.execute(
        """INSERT INTO orders
        (user_id, product, amount, price, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?)""",
        (
            user_id,
            product,
            amount,
            price,
            "pending",
            datetime.now().isoformat(timespec="seconds"),
        ),
    )
    order_id = cur.lastrowid
    con.commit()
    con.close()
    return order_id


def get_order_count(user_id):
    con = sqlite3.connect(DB_FILE)
    value = con.execute(
        "SELECT COUNT(*) FROM orders WHERE user_id = ?", (user_id,)
    ).fetchone()[0]
    con.close()
    return value


def get_orders(user_id):
    con = sqlite3.connect(DB_FILE)
    rows = con.execute(
        """SELECT id, product, price, status
        FROM orders WHERE user_id = ?
        ORDER BY id DESC LIMIT 5""",
        (user_id,),
    ).fetchall()
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


def home_button():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🏠 Bosh menyu", callback_data="home")]
    ])


async def edit(query, text, keyboard):
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


async def stars_menu(query):
    rows = []
    row = []

    for count in PACKAGES:
        row.append(
            InlineKeyboardButton(
                f"⭐ {count}",
                callback_data=f"stars:{count}",
            )
        )
        if len(row) == 3:
            rows.append(row)
            row = []

    if row:
        rows.append(row)

    rows.append([
        InlineKeyboardButton("✏️ Boshqa miqdor", callback_data="custom")
    ])
    rows.append([
        InlineKeyboardButton("🏠 Bosh menyu", callback_data="home")
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

    await edit(query, text, InlineKeyboardMarkup(rows))


async def gifts_menu(query, context):
    try:
        result = await context.bot.get_available_gifts()
        gifts = result.gifts if result else []

        if not gifts:
            await edit(
                query,
                "🎁 <b>Gift</b>\n\nHozircha mavjud Gift topilmadi.",
                home_button(),
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
                        callback_data=callback,
                    )
                ])

        rows.append([
            InlineKeyboardButton("🏠 Bosh menyu", callback_data="home")
        ])

        await edit(
            query,
            "🎁 <b>Gift</b>\n\n"
            "Kerakli Giftni tanlang:\n\n"
            "⚡ To'lov tasdiqlangach avtomatik yetkazib berish ulanadi.",
            InlineKeyboardMarkup(rows),
        )

    except Exception as exc:
        print("GIFT ERROR:", repr(exc))
        await edit(
            query,
            "🎁 <b>Gift</b>\n\nGiftlarni yuklashda xatolik yuz berdi.",
            home_button(),
        )


async def premium_menu(query):
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("💎 1 oy", callback_data="premium:1 oy"),
            InlineKeyboardButton("💎 3 oy", callback_data="premium:3 oy"),
        ],
        [
            InlineKeyboardButton("💎 6 oy", callback_data="premium:6 oy"),
            InlineKeyboardButton("💎 1 yil", callback_data="premium:1 yil"),
        ],
        [
            InlineKeyboardButton("🏠 Bosh menyu", callback_data="home")
        ],
    ])

    text = (
        "💎 <b>Telegram Premium</b>\n\n"
        "💎 1 oy — <b>45 000 so'm</b>\n"
        "💎 3 oy — <b>164 000 so'm</b>\n"
        "💎 6 oy — <b>222 000 so'm</b>\n"
        "💎 1 yil — <b>377 000 so'm</b>"
    )

    await edit(query, text, keyboard)


async def balance_menu(query):
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🟢 Payme", callback_data="pay:Payme"),
            InlineKeyboardButton("🔵 Click", callback_data="pay:Click"),
        ],
        [
            InlineKeyboardButton("💳 Uzcard", callback_data="pay:Uzcard"),
            InlineKeyboardButton("💳 Humo", callback_data="pay:Humo"),
        ],
        [
            InlineKeyboardButton("🪙 TON", callback_data="pay:TON")
        ],
        [
            InlineKeyboardButton("🏠 Bosh menyu", callback_data="home")
        ],
    ])

    await edit(
        query,
        "💰 <b>Balans</b>\n\n"
        "To'lov usulini tanlang:\n\n"
        "⚠️ Real API ma'lumotlari hali ulanmagan.",
        keyboard,
    )


async def profile_menu(query):
    user = query.from_user
    count = get_order_count(user.id)

    await edit(
        query,
        "👤 <b>Profil</b>\n\n"
        f"🆔 ID: <code>{user.id}</code>\n"
        f"👤 Ism: {user.first_name or '-'}\n"
        f"🔗 Username: @{user.username or '-'}\n"
        f"📦 Buyurtmalar: <b>{count}</b>",
        home_button(),
    )


async def orders_menu(query):
    rows = get_orders(query.from_user.id)

    if not rows:
        text = "📋 <b>Buyurtmalar</b>\n\nHozircha buyurtma yo'q."
    else:
        text = "📋 <b>So'nggi buyurtmalar</b>\n\n"

        for oid, product, price, status in rows:
            status_text = {
                "pending": "⏳ Kutilmoqda",
                "paid": "✅ To'langan",
                "completed": "🎉 Bajarildi",
                "cancelled": "❌ Bekor qilingan",
            }.get(status, status)

            text += (
                f"🆔 <b>#{oid}</b> — {product}\n"
                f"💵 {money(price)} so'm\n"
                f"{status_text}\n\n"
            )

    await edit(query, text, home_button())


async def help_menu(query):
    await edit(
        query,
        "🔵 <b>Yordam</b>\n\n"
        "Savol yoki muammo bo'lsa admin bilan bog'laning:\n"
        "@Shamsbekman",
        InlineKeyboardMarkup([
            [InlineKeyboardButton("👨‍💻 Admin", url=ADMIN_URL)],
            [InlineKeyboardButton("🏠 Bosh menyu", callback_data="home")],
        ]),
    )


async def info_menu(query):
    await edit(
        query,
        "ℹ️ <b>Ma'lumot</b>\n\n"
        "🌟 Stars Gift Shop\n"
        "⭐ Stars\n"
        "🎁 Gift\n"
        "💎 Premium\n\n"
        "⚡ O'rtacha bajarilish: <b>30 soniya</b>",
        home_button(),
    )


async def settings_menu(query):
    await edit(
        query,
        "⚙️ <b>Sozlama</b>\n\n"
        "Hozircha qo'shimcha sozlamalar mavjud emas.",
        home_button(),
    )


async def payment_menu(query, context):
    oid = context.user_data.get("order_id", "-")

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🟢 Payme",
                callback_data=f"checkout:Payme:{oid}",
            ),
            InlineKeyboardButton(
                "🔵 Click",
                callback_data=f"checkout:Click:{oid}",
            ),
        ],
        [
            InlineKeyboardButton(
                "💳 Uzcard",
                callback_data=f"checkout:Uzcard:{oid}",
            ),
            InlineKeyboardButton(
                "💳 Humo",
                callback_data=f"checkout:Humo:{oid}",
            ),
        ],
        [
            InlineKeyboardButton(
                "🪙 TON",
                callback_data=f"checkout:TON:{oid}",
            )
        ],
        [
            InlineKeyboardButton("🏠 Bosh menyu", callback_data="home")
        ],
    ])

    await edit(
        query,
        "💳 <b>To'lov</b>\n\n"
        f"🆔 Buyurtma: <b>#{oid}</b>\n\n"
        "To'lov usulini tanlang.\n\n"
        "⚠️ Real API hali ulanmagan. Soxta to'lov tasdiqlanmaydi.",
        keyboard,
    )


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data or ""

    try:
        if data == "home":
            context.user_data.clear()
            await edit(
                query,
                "🌟 <b>Stars Gift Shop</b>\n\n"
                "Kerakli xizmatni tanlang:\n\n"
                "⚡ O'rtacha bajarilish: <b>30 soniya</b>",
                main_keyboard(),
            )

        elif data == "stars":
            context.user_data.pop("waiting_stars", None)
            await stars_menu(query)

        elif data == "gifts":
            await gifts_menu(query, context)

        elif data == "premium":
            await premium_menu(query)

        elif data == "balance":
            await balance_menu(query)

        elif data == "profile":
            await profile_menu(query)

        elif data == "orders":
            await orders_menu(query)

        elif data == "help":
            await help_menu(query)

        elif data == "info":
            await info_menu(query)

        elif data == "settings":
            await settings_menu(query)

        elif data == "custom":
            context.user_data["waiting_stars"] = True

            await edit(
                query,
                "✏️ <b>Stars miqdorini kiriting</b>\n\n"
                f"Minimal: <b>{MIN_STARS}</b> ⭐\n"
                f"Maksimal: <b>{MAX_STARS}</b> ⭐\n\n"
                "Masalan: <code>150</code>",
                InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                        "❌ Bekor qilish",
                        callback_data="stars"
                    )]
                ]),
            )

        elif data.startswith("stars:"):
            count = int(data.split(":", 1)[1])
            price = count * STARS_PRICE

            oid = create_order(
                query.from_user.id,
                f"{count} Stars",
                count,
                price,
            )
            context.user_data["order_id"] = oid

            await edit(
                query,
                "⭐ <b>Stars buyurtmasi</b>\n\n"
                f"⭐ Miqdor: <b>{count}</b>\n"
                f"💵 Narx: <b>{money(price)} so'm</b>\n"
                f"🆔 Buyurtma: <b>#{oid}</b>",
                InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                        "💳 To'lovni tanlash",
                        callback_data="payment"
                    )],
                    [InlineKeyboardButton(
                        "⬅️ Orqaga",
                        callback_data="stars"
                    )],
                ]),
            )

        elif data.startswith("premium:"):
            package = data.split(":", 1)[1]
            price = PREMIUM[package]

            oid = create_order(
                query.from_user.id,
                f"Premium {package}",
                1,
                price,
            )
            context.user_data["order_id"] = oid

            await edit(
                query,
                "💎 <b>Premium buyurtmasi</b>\n\n"
                f"📦 Paket: <b>{package}</b>\n"
                f"💵 Narx: <b>{money(price)} so'm</b>\n"
                f"🆔 Buyurtma: <b>#{oid}</b>",
                InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                        "💳 To'lovni tanlash",
                        callback_data="payment"
                    )],
                    [InlineKeyboardButton(
                        "⬅️ Orqaga",
                        callback_data="premium"
                    )],
                ]),
            )

        elif data.startswith("gift:"):
            gift_id = data.split(":", 1)[1]

            oid = create_order(
                query.from_user.id,
                f"Gift {gift_id}",
                1,
                0,
            )
            context.user_data["order_id"] = oid
            context.user_data["gift_id"] = gift_id

            await edit(
                query,
                "🎁 <b>Gift buyurtmasi</b>\n\n"
                f"🎁 Gift ID: <code>{gift_id}</code>\n"
                f"🆔 Buyurtma: <b>#{oid}</b>\n\n"
                "To'lov usulini tanlang:",
                InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                        "💳 To'lovni tanlash",
                        callback_data="payment"
                    )],
                    [InlineKeyboardButton(
                        "⬅️ Orqaga",
                        callback_data="gifts"
                    )],
                ]),
            )

        elif data == "payment":
            await payment_menu(query, context)

        elif data.startswith("pay:"):
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

            await edit(
                query,
                "⏳ <b>To'lov moduli</b>\n\n"
                f"💳 Usul: <b>{method}</b>\n\n"
                "Merchant/API ulangach haqiqiy to'lov oynasi ishlaydi.\n\n"
                "⚠️ Soxta to'lov tasdiqlanmaydi.",
                home_button(),
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
        count = int(update.message.text.strip())
    except ValueError:
        await update.message.reply_text(
            "❌ Faqat raqam yuboring. Masalan: 150"
        )
        return

    if count < MIN_STARS or count > MAX_STARS:
        await update.message.reply_text(
            f"❌ {MIN_STARS} dan {MAX_STARS} gacha kiriting."
        )
        return

    context.user_data["waiting_stars"] = False

    price = count * STARS_PRICE

    oid = create_order(
        update.effective_user.id,
        f"{count} Stars",
        count,
        price,
    )
    context.user_data["order_id"] = oid

    await update.message.reply_text(
        "⭐ <b>Stars buyurtmasi</b>\n\n"
        f"⭐ Miqdor: <b>{count:,}</b>\n"
        f"💵 Narx: <b>{money(price)} so'm</b>\n"
        f"🆔 Buyurtma: <b>#{oid}</b>",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(
                "💳 To'lovni tanlash",
                callback_data="payment"
            )],
            [InlineKeyboardButton(
                "⭐ Stars",
                callback_data="stars"
            )],
        ]),
    )


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    print("BOT ERROR:", repr(context.error))


if not TOKEN:
    raise RuntimeError(
        "BOT_TOKEN topilmadi! Railway Variables ichiga BOT_TOKEN qo'ying."
    )

init_db()

application = Application.builder().token(TOKEN).build()

application.add_handler(CommandHandler("start", start))
application.add_handler(CallbackQueryHandler(button))
application.add_handler(
    MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler)
)
application.add_error_handler(error_handler)

print("Stars Gift Shop ishga tushdi!")
application.run_polling(drop_pending_updates=True)
                              
