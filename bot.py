import os
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

TOKEN = os.getenv("BOT_TOKEN")
ADMIN = "@Shamsbekman"

# ⭐ 1 Star = 195 so'm
STAR_PRICE = 195

PREMIUM = [
    ("1 oy", 45000),
    ("3 oy", 164000),
    ("6 oy", 222000),
    ("12 oy", 377000),
]

TOPUP = [
    10000,
    20000,
    50000,
    100000,
    200000,
    500000,
]


def db():
    con = sqlite3.connect("shop.db")
    con.execute(
        "CREATE TABLE IF NOT EXISTS users "
        "(user_id INTEGER PRIMARY KEY, balance INTEGER DEFAULT 0)"
    )
    con.execute(
        "CREATE TABLE IF NOT EXISTS orders "
        "(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, "
        "item TEXT, amount INTEGER, status TEXT)"
    )
    con.commit()
    return con


def get_balance(user_id):
    con = db()
    row = con.execute(
        "SELECT balance FROM users WHERE user_id=?",
        (user_id,)
    ).fetchone()

    if row is None:
        con.execute(
            "INSERT INTO users(user_id,balance) VALUES(?,0)",
            (user_id,)
        )
        con.commit()
        balance = 0
    else:
        balance = row[0]

    con.close()
    return balance


def create_order(user_id, item, amount):
    con = db()
    cur = con.execute(
        "INSERT INTO orders(user_id,item,amount,status) "
        "VALUES(?,?,?,'pending')",
        (user_id, item, amount)
    )
    con.commit()
    order_id = cur.lastrowid
    con.close()
    return order_id


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("⭐ Stars", callback_data="stars"),
            InlineKeyboardButton("🎁 Gift", callback_data="gift"),
            InlineKeyboardButton("💎 Premium", callback_data="premium"),
        ],
        [
            InlineKeyboardButton("💰 Balans", callback_data="balance"),
            InlineKeyboardButton("➕ Hisob to‘ldirish", callback_data="topup"),
            InlineKeyboardButton("👤 Profil", callback_data="profile"),
        ],
        [
            InlineKeyboardButton("📋 Buyurtma", callback_data="orders"),
            InlineKeyboardButton("🔵 Yordam", callback_data="help"),
            InlineKeyboardButton("ℹ️ Ma'lumot", callback_data="info"),
        ],
        [
            InlineKeyboardButton("⚙️ Sozlama", callback_data="settings")
        ],
    ]

    text = (
        "⭐ <b>Stars Gift Shop</b>\n\n"
        "Assalomu alaykum! 👋\n"
        "Kerakli bo‘limni tanlang 👇\n\n"
        "⚡ Tez xizmat\n"
        "🔐 Ishonchli\n"
        "💳 So‘mda to‘lov"
    )

    await update.message.reply_text(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    data = query.data

    if data == "stars":
        keyboard = [
            [
                InlineKeyboardButton(
                    "⭐ 25 Stars — 4 875 so‘m",
                    callback_data="star_25"
                ),
                InlineKeyboardButton(
                    "⭐ 50 Stars — 9 750 so‘m",
                    callback_data="star_50"
                ),
            ],
            [
                InlineKeyboardButton(
                    "⭐ 100 Stars — 19 500 so‘m",
                    callback_data="star_100"
                ),
                InlineKeyboardButton(
                    "⭐ 125 Stars — 24 375 so‘m",
                    callback_data="star_125"
                ),
            ],
            [
                InlineKeyboardButton(
                    "⭐ 150 Stars — 29 250 so‘m",
                    callback_data="star_150"
                ),
                InlineKeyboardButton(
                    "⭐ 175 Stars — 34 125 so‘m",
                    callback_data="star_175"
                ),
            ],
            [
                InlineKeyboardButton(
                    "⭐ 200 Stars — 39 000 so‘m",
                    callback_data="star_200"
                ),
                InlineKeyboardButton(
                    "⭐ 300 Stars — 58 500 so‘m",
                    callback_data="star_300"
                ),
            ],
            [
                InlineKeyboardButton(
                    "⭐ 400 Stars — 78 000 so‘m",
                    callback_data="star_400"
                ),
                InlineKeyboardButton(
                    "⭐ 500 Stars — 97 500 so‘m",
                    callback_data="star_500"
                ),
            ],
            [
                InlineKeyboardButton("🔙 Orqaga", callback_data="home")
            ],
        ]

        await query.edit_message_text(
            "⭐ <b>STARS OLISH</b>\n\n"
            "Kerakli Stars paketini tanlang:",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif data.startswith("star_"):
        stars = int(data.split("_")[1])
        amount = stars * STAR_PRICE
        order_id = create_order(
            user_id,
            f"{stars} Stars",
            amount
        )

        keyboard = [
            [
                InlineKeyboardButton(
                    "💳 SO‘MDA TO‘LASH",
                    callback_data=f"pay_{order_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    "🔙 Orqaga",
                    callback_data="stars"
                )
            ],
        ]

        await query.edit_message_text(
            f"⭐ <b>{stars} Stars</b>\n\n"
            f"💰 Narxi: <b>{amount:,} so‘m</b>\n"
            f"⚡ O‘rtacha bajarilish: <b>30 soniya</b>\n\n"
            f"Buyurtma № <b>{order_id}</b>\n\n"
            "To‘lov uchun tugmani bosing 👇",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif data == "gift":
        await show_gifts(query)

    elif data == "premium":
        keyboard = [
            [
                InlineKeyboardButton(
                    "💎 1 oy — 45 000 so‘m",
                    callback_data="prem_0"
                )
            ],
            [
                InlineKeyboardButton(
                    "💎 3 oy — 164 000 so‘m",
                    callback_data="prem_1"
                )
            ],
            [
                InlineKeyboardButton(
                    "💎 6 oy — 222 000 so‘m",
                    callback_data="prem_2"
                )
            ],
            [
                InlineKeyboardButton(
                    "💎 12 oy — 377 000 so‘m",
                    callback_data="prem_3"
                )
            ],
            [
                InlineKeyboardButton(
                    "🔙 Orqaga",
                    callback_data="home"
                )
            ],
        ]

        await query.edit_message_text(
            "💎 <b>PREMIUM</b>\n\n"
            "Premium paketini tanlang:",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif data.startswith("prem_"):
        index = int(data.split("_")[1])
        name, amount = PREMIUM[index]

        order_id = create_order(
            user_id,
            f"Premium {name}",
            amount
        )

        keyboard = [
            [
                InlineKeyboardButton(
                    "💳 SO‘MDA TO‘LASH",
                    callback_data=f"pay_{order_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    "🔙 Orqaga",
                    callback_data="premium"
                )
            ],
        ]

        await query.edit_message_text(
            f"💎 <b>Premium {name}</b>\n\n"
            f"💰 Narxi: <b>{amount:,} so‘m</b>\n"
            f"⚡ O‘rtacha bajarilish: <b>30 soniya</b>\n\n"
            f"Buyurtma № <b>{order_id}</b>",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif data == "balance":
        balance = get_balance(user_id)

        await query.edit_message_text(
            f"💰 <b>BALANS</b>\n\n"
            f"💵 Balansingiz: <b>{balance:,} so‘m</b>",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "➕ Hisob to‘ldirish",
                        callback_data="topup"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "🔙 Orqaga",
                        callback_data="home"
                    )
                ],
            ])
        )

    elif data == "topup":
        keyboard = []

        for amount in TOPUP:
            keyboard.append([
                InlineKeyboardButton(
                    f"💰 {amount:,} so‘m",
                    callback_data=f"top_{amount}"
                )
            ])

        keyboard.append([
            InlineKeyboardButton(
                "🔙 Orqaga",
                callback_data="home"
            )
        ])

        await query.edit_message_text(
            "➕ <b>HISOB TO‘LDIRISH</b>\n\n"
            "To‘ldirish summasini tanlang:",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif data.startswith("top_"):
        amount = int(data.split("_")[1])
        order_id = create_order(
            user_id,
            "Balans to‘ldirish",
            amount
        )

        await query.edit_message_text(
            f"➕ <b>Hisob to‘ldirish</b>\n\n"
            f"💰 Summa: <b>{amount:,} so‘m</b>\n"
            f"📋 Buyurtma: <b>#{order_id}</b>\n\n"
            "💳 To‘lov tizimi ulanishi bilan shu yerda "
            "to‘lov tugmasi chiqadi.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "🔙 Orqaga",
                        callback_data="topup"
                    )
                ]
            ])
        )

    elif data.startswith("pay_"):
        await query.edit_message_text(
            "💳 <b>SO‘MDA TO‘LOV</b>\n\n"
            "To‘lov tizimi hali API orqali ulanmagan.\n\n"
            "Click/Payme API ulangandan keyin "
            "to‘lov avtomatik tasdiqlanadi.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "🔙 Orqaga",
                        callback_data="home"
                    )
                ]
            ])
        )

    elif data == "profile":
        balance = get_balance(user_id)

        await query.edit_message_text(
            f"👤 <b>PROFIL</b>\n\n"
            f"🆔 ID: <code>{user_id}</code>\n"
            f"💰 Balans: <b>{balance:,} so‘m</b>",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "🔙 Orqaga",
                        callback_data="home"
                    )
                ]
            ])
        )

    elif data == "orders":
        con = db()
        rows = con.execute(
            "SELECT id,item,amount,status FROM orders "
            "WHERE user_id=? ORDER BY id DESC LIMIT 10",
            (user_id,)
        ).fetchall()
        con.close()

        if not rows:
            text = "📋 <b>BUYURTMALAR</b>\n\nHozircha buyurtmalar yo‘q."
        else:
            text = "📋 <b>BUYURTMALAR</b>\n\n"
            for oid, item, amount, status in rows:
                text += (
                    f"#{oid} — {item}\n"
                    f"💰 {amount:,} so‘m — {status}\n\n"
                )

        await query.edit_message_text(
            text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "🔙 Orqaga",
                        callback_data="home"
                    )
                ]
            ])
        )

    elif data == "help":
        await query.edit_message_text(
            "🔵 <b>YORDAM</b>\n\n"
            f"Operator: {ADMIN}\n\n"
            "Savollar bo‘lsa operatorga yozing.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "🔙 Orqaga",
                        callback_data="home"
                    )
                ]
            ])
        )

    elif data == "info":
        await query.edit_message_text(
            "ℹ️ <b>MA'LUMOT</b>\n\n"
            "⭐ Stars\n"
            "🎁 Gift\n"
            "💎 Premium\n\n"
            "⚡ O‘rtacha bajarilish: 30 soniya\n"
            "💳 To‘lov: so‘m",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "🔙 Orqaga",
                        callback_data="home"
                    )
                ]
            ])
        )

    elif data == "settings":
        await query.edit_message_text(
            "⚙️ <b>SOZLAMA</b>\n\n"
            "Til: 🇺🇿 O‘zbekcha",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "🔙 Orqaga",
                        callback_data="home"
                    )
                ]
            ])
        )

    elif data == "home":
        keyboard = [
            [
                InlineKeyboardButton("⭐ Stars", callback_data="stars"),
                InlineKeyboardButton("🎁 Gift", callback_data="gift"),
                InlineKeyboardButton("💎 Premium", callback_data="premium"),
            ],
            [
                InlineKeyboardButton("💰 Balans", callback_data="balance"),
                InlineKeyboardButton("➕ Hisob to‘ldirish", callback_data="topup"),
                InlineKeyboardButton("👤 Profil", callback_data="profile"),
            ],
            [
                InlineKeyboardButton("📋 Buyurtma", callback_data="orders"),
                InlineKeyboardButton("🔵 Yordam", callback_data="help"),
                InlineKeyboardButton("ℹ️ Ma'lumot", callback_data="info"),
            ],
            [
                InlineKeyboardButton("⚙️ Sozlama", callback_data="settings")
            ],
        ]

        await query.edit_message_text(
            "⭐ <b>Stars Gift Shop</b>\n\n"
            "Kerakli bo‘limni tanlang 👇",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


async def show_gifts(query):
    try:
        gifts = await query.message.get_bot().get_available_gifts()

        if not gifts.gifts:
            await query.edit_message_text(
                "🎁 <b>GIFTLAR</b>\n\n"
                "Hozircha mavjud Gift topilmadi.",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton(
                            "🔙 Orqaga",
                            callback_data="home"
                        )
                    ]
                ])
            )
            return

        keyboard = []

        for gift in gifts.gifts:
            price = gift.star_count
            som = price * STAR_PRICE

            keyboard.append([
                InlineKeyboardButton(
                    f"🎁 ⭐{price} — {som:,} so‘m",
                    callback_data=f"gift_{gift.id}"
                )
            ])

        keyboard.append([
            InlineKeyboardButton(
                "🔙 Orqaga",
                callback_data="home"
            )
        ])

        await query.edit_message_text(
            "🎁 <b>GIFTLAR</b>\n\n"
            "Mavjud Giftlar va ularning narxlari:",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    except Exception:
        await query.edit_message_text(
            "🎁 <b>GIFTLAR</b>\n\n"
            "Giftlarni yuklashda xatolik yuz berdi.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "🔙 Orqaga",
                        callback_data="home"
                    )
                ]
            ])
        )


async def gift_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    gift_id = query.data.replace("gift_", "")

    try:
        gifts = await context.bot.get_available_gifts()

        selected = None
        for gift in gifts.gifts:
            if str(gift.id) == gift_id:
                selected = gift
                break

        if selected is None:
            await query.edit_message_text(
                "🎁 Bu Gift hozir mavjud emas."
            )
            return

        stars = selected.star_count
        amount = stars * STAR_PRICE

        order_id = create_order(
            query.from_user.id,
            f"Gift ⭐{stars}",
            amount
        )

        await query.edit_message_text(
            f"🎁 <b>GIFT TANLANDI</b>\n\n"
            f"⭐ Narxi: <b>{stars} Stars</b>\n"
            f"💰 So‘mda: <b>{amount:,} so‘m</b>\n"
            f"⚡ O‘rtacha bajarilish: <b>30 soniya</b>\n\n"
            f"📋 Buyurtma № <b>{order_id}</b>\n\n"
            "💳 To‘lov tizimi ulangandan keyin "
            "avtomatik bajariladi.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "🎁 Giftlar",
                        callback_data="gift"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "🔙 Orqaga",
                        callback_data="home"
                    )
                ]
            ])
        )

    except Exception:
        await query.edit_message_text(
            "❌ Giftni ochishda xatolik yuz berdi.",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "🔙 Orqaga",
                        callback_data="gift"
                    )
                ]
            ])
        )


def main():
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN topilmadi!")

    db()

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(
        CallbackQueryHandler(
            gift_selected,
            pattern=r"^gift_.+"
        )
    )
    app.add_handler(
        CallbackQueryHandler(button)
    )

    print("STARGIFT SHOP BOT ISHGA TUSHDI")
    app.run_polling()


if __name__ == "__main__":
    main()
