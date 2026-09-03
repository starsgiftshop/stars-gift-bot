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

STAR_PACKAGES = [
    25, 50, 100, 125, 150,
    175, 200, 300, 400, 500
]


# =========================================================
# DATABASE
# =========================================================

def db():
    con = sqlite3.connect("shop.db")

    con.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            balance INTEGER DEFAULT 0
        )
    """)

    con.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            item TEXT,
            amount INTEGER,
            status TEXT
        )
    """)

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
            "INSERT INTO users(user_id, balance) VALUES(?, 0)",
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
        """
        INSERT INTO orders(user_id, item, amount, status)
        VALUES(?, ?, ?, ?)
        """,
        (user_id, item, amount, "pending")
    )

    con.commit()
    order_id = cur.lastrowid

    con.close()

    return order_id


# =========================================================
# TEXT
# =========================================================

def home_text():
    return (
        "💙✨ STARGIFT SHOP ✨💙\n\n"
        "⭐ STARS  •  🎁 GIFTLAR  •  💎 PREMIUM\n"
        "⚡ Tez • 🔐 Ishonchli • 💳 So‘m\n\n"
        "Kerakli bo‘limni tanlang 👇"
    )


# =========================================================
# MAIN MENU
# =========================================================

def main_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "⭐ Stars",
                callback_data="stars"
            ),
            InlineKeyboardButton(
                "🎁 Gift",
                callback_data="gift"
            ),
            InlineKeyboardButton(
                "💎 Premium",
                callback_data="premium"
            ),
        ],
        [
            InlineKeyboardButton(
                "💰 Balans",
                callback_data="balance"
            ),
            InlineKeyboardButton(
                "➕ Hisob to‘ldirish",
                callback_data="topup"
            ),
            InlineKeyboardButton(
                "👤 Profil",
                callback_data="profile"
            ),
        ],
        [
            InlineKeyboardButton(
                "📋 Buyurtma",
                callback_data="orders"
            ),
            InlineKeyboardButton(
                "🔵 Yordam",
                callback_data="help"
            ),
            InlineKeyboardButton(
                "ℹ️ Ma'lumot",
                callback_data="info"
            ),
        ],
        [
            InlineKeyboardButton(
                "⚙️ Sozlama",
                callback_data="settings"
            ),
        ],
    ])


# =========================================================
# START
# =========================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = home_text()
    image_path = "stargift_start.png"

    if os.path.exists(image_path):

        with open(image_path, "rb") as photo:

            await update.message.reply_photo(
                photo=photo,
                caption=text,
                reply_markup=main_keyboard()
            )

    else:

        await update.message.reply_text(
            text,
            reply_markup=main_keyboard()
        )


# =========================================================
# TELEGRAM MENU
# =========================================================

async def post_init(application):

    await application.bot.set_my_commands([
        ("start", "🏠 Bosh sahifa"),
        ("orders", "📋 Buyurtmalarim"),
        ("profile", "👤 Profil"),
        ("help", "🔵 Yordam"),
    ])


# =========================================================
# ORDERS COMMAND
# =========================================================

async def orders_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    con = db()

    orders = con.execute(
        """
        SELECT id, item, amount, status
        FROM orders
        WHERE user_id=?
        ORDER BY id DESC
        LIMIT 10
        """,
        (user_id,)
    ).fetchall()

    con.close()

    if not orders:

        text = (
            "📋 BUYURTMALARIM\n\n"
            "Hozircha buyurtmalar yo‘q."
        )

    else:

        text = "📋 BUYURTMALARIM\n\n"

        for order_id, item, amount, status in orders:

            text += (
                f"📦 #{order_id}\n"
                f"🛍 {item}\n"
                f"💳 {amount:,} so'm\n"
                f"📌 {status}\n\n"
            )

    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "🏠 Bosh sahifa",
                    callback_data="back"
                )
            ]
        ])
    )


# =========================================================
# PROFILE COMMAND
# =========================================================

async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id
    balance = get_balance(user_id)

    await update.message.reply_text(
        "👤 PROFIL\n\n"
        f"🆔 ID: {user_id}\n"
        f"💰 Balans: {balance:,} so'm",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "🏠 Bosh sahifa",
                    callback_data="back"
                )
            ]
        ])
    )


# =========================================================
# HELP COMMAND
# =========================================================

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        f"🔵 YORDAM\n\n"
        f"Savollar bo‘lsa:\n{ADMIN}",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "🏠 Bosh sahifa",
                    callback_data="back"
                )
            ]
        ])
    )


# =========================================================
# STARS
# =========================================================

async def show_stars(query):

    keyboard = []

    for n in STAR_PACKAGES:

        price = n * STAR_PRICE

        keyboard.append([
            InlineKeyboardButton(
                f"⭐ {n} Stars — {price:,} so'm",
                callback_data=f"star_{n}"
            )
        ])

    keyboard.append([
        InlineKeyboardButton(
            "🏠 Bosh sahifa",
            callback_data="back"
        )
    ])

    await query.edit_message_caption(
        caption=(
            "⭐ STARS\n\n"
            "💰 1 Star = 195 so'm\n\n"
            "Paketni tanlang 👇"
        ),
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def star_selected(query):

    stars = int(query.data.split("_")[1])
    price = stars * STAR_PRICE

    order_id = create_order(
        query.from_user.id,
        f"{stars} Stars",
        price
    )

    await query.edit_message_caption(
        caption=(
            "⭐ STARS BUYURTMASI\n\n"
            f"⭐ Miqdor: {stars} Stars\n"
            f"💳 Narxi: {price:,} so'm\n"
            f"📦 Buyurtma: #{order_id}\n\n"
            "💳 To‘lov tizimi keyingi bosqichda ulanadi."
        ),
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "⬅️ Stars",
                    callback_data="stars"
                )
            ],
            [
                InlineKeyboardButton(
                    "🏠 Bosh sahifa",
                    callback_data="back"
                )
            ],
        ])
    )


# =========================================================
# GIFTS
# =========================================================

async def show_gifts(query, context):

    try:

        gifts = await context.bot.get_available_gifts()

    except Exception as e:

        print("GIFT ERROR:", e)

        await query.edit_message_caption(
            caption=(
                "🎁 GIFTLAR\n\n"
                "⚠️ Giftlarni olishda xatolik."
            ),
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "🏠 Bosh sahifa",
                        callback_data="back"
                    )
                ]
            ])
        )

        return

    if not gifts.gifts:

        await query.edit_message_caption(
            caption=(
                "🎁 GIFTLAR\n\n"
                "Hozircha mavjud Gift topilmadi."
            ),
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "🏠 Bosh sahifa",
                        callback_data="back"
                    )
                ]
            ])
        )

        return

    rows = []
    row = []

    for i, gift in enumerate(gifts.gifts):

        emoji = getattr(
            gift.sticker,
            "emoji",
            "🎁"
        ) or "🎁"

        price = gift.star_count * STAR_PRICE

        row.append(
            InlineKeyboardButton(
                f"{emoji} {gift.star_count}⭐ • {price:,} so'm",
                callback_data=f"gift_{gift.id}"
            )
        )

        if len(row) == 2:

            rows.append(row)
            row = []

        if i >= 49:
            break

    if row:
        rows.append(row)

    rows.append([
        InlineKeyboardButton(
            "🏠 Bosh sahifa",
            callback_data="back"
        )
    ])

    await query.edit_message_caption(
        caption=(
            "🎁 GIFTLAR\n\n"
            "Mavjud Giftlar 👇\n\n"
            "💳 Narxlar so‘mda."
        ),
        reply_markup=InlineKeyboardMarkup(rows)
    )


async def gift_selected(query, context):

    try:

        gift_id = query.data[len("gift_"):]

        gifts = await context.bot.get_available_gifts()

        gift = next(
            (g for g in gifts.gifts if g.id == gift_id),
            None
        )

        if gift is None:

            await query.answer(
                "Gift topilmadi!",
                show_alert=True
            )

            return

        price = gift.star_count * STAR_PRICE

        emoji = getattr(
            gift.sticker,
            "emoji",
            "🎁"
        ) or "🎁"

        order_id = create_order(
            query.from_user.id,
            f"Gift {gift_id}",
            price
        )

        await query.edit_message_caption(
            caption=(
                f"{emoji} GIFT TANLANDI!\n\n"
                f"⭐ Telegram narxi: "
                f"{gift.star_count} Stars\n"
                f"💳 Bizdagi narxi: "
                f"{price:,} so'm\n"
                f"📦 Buyurtma: #{order_id}\n\n"
                "💳 To‘lov tizimi keyingi bosqichda ulanadi."
            ),
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "⬅️ Giftlarga qaytish",
                        callback_data="gift"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "🏠 Bosh sahifa",
                        callback_data="back"
                    )
                ],
            ])
        )

        await query.answer()

    except Exception as e:

        print("GIFT SELECT ERROR:", e)

        await query.answer(
            "Giftni tanlashda xatolik!",
            show_alert=True
        )


# =========================================================
# PREMIUM
# =========================================================

async def show_premium(query):

    keyboard = []

    for i, (period, price) in enumerate(PREMIUM):

        keyboard.append([
            InlineKeyboardButton(
                f"💎 {period} — {price:,} so'm",
                callback_data=f"premium_{i}"
            )
        ])

    keyboard.append([
        InlineKeyboardButton(
            "🏠 Bosh sahifa",
            callback_data="back"
        )
    ])

    await query.edit_message_caption(
        caption="💎 PREMIUM\n\nMuddatni tanlang 👇",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def premium_selected(query):

    index = int(query.data.split("_")[1])

    period, price = PREMIUM[index]

    order_id = create_order(
        query.from_user.id,
        f"Premium {period}",
        price
    )

    await query.edit_message_caption(
        caption=(
            f"💎 PREMIUM\n\n"
            f"📅 Muddat: {period}\n"
            f"💳 Narxi: {price:,} so'm\n"
            f"📦 Buyurtma: #{order_id}\n\n"
            "💳 To‘lov tizimi keyingi bosqichda ulanadi."
        ),
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "⬅️ Premium",
                    callback_data="premium"
                )
            ],
            [
                InlineKeyboardButton(
                    "🏠 Bosh sahifa",
                    callback_data="back"
                )
            ],
        ])
    )


# =========================================================
# BALANCE
# =========================================================

async def show_balance(query):

    balance = get_balance(query.from_user.id)

    await query.edit_message_caption(
        caption=(
            "💰 BALANS\n\n"
            f"💵 {balance:,} so'm"
        ),
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "➕ Hisob to‘ldirish",
                    callback_data="topup"
                )
            ],
            [
                InlineKeyboardButton(
                    "🏠 Bosh sahifa",
                    callback_data="back"
                )
            ]
        ])
    )


# =========================================================
# TOPUP
# =========================================================

async def show_topup(query):

    keyboard = []
    row = []

    for amount in TOPUP:

        row.append(
            InlineKeyboardButton(
                f"💳 {amount:,} so'm",
                callback_data=f"topup_{amount}"
            )
        )

        if len(row) == 2:

            keyboard.append(row)
            row = []

    if row:
        keyboard.append(row)

    keyboard.append([
        InlineKeyboardButton(
            "🏠 Bosh sahifa",
            callback_data="back"
        )
    ])

    await query.edit_message_caption(
        caption=(
            "➕ HISOB TO‘LDIRISH\n\n"
            "Summani tanlang 👇"
        ),
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def topup_selected(query):

    amount = int(
        query.data.split("_")[1]
    )

    order_id = create_order(
        query.from_user.id,
        "Hisob to‘ldirish",
        amount
    )

    await query.edit_message_caption(
        caption=(
            "➕ HISOB TO‘LDIRISH\n\n"
            f"💳 Summa: {amount:,} so'm\n"
            f"📦 Buyurtma: #{order_id}\n\n"
            "💳 To‘lov tizimi keyingi bosqichda ulanadi."
        ),
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "⬅️ Summalar",
                    callback_data="topup"
                )
            ],
            [
                InlineKeyboardButton(
                    "🏠 Bosh sahifa",
                    callback_data="back"
                )
            ],
        ])
    )


# =========================================================
# PROFILE
# =========================================================

async def show_profile(query):

    balance = get_balance(
        query.from_user.id
    )

    await query.edit_message_caption(
        caption=(
            "👤 PROFIL\n\n"
            f"🆔 ID: {query.from_user.id}\n"
            f"💰 Balans: {balance:,} so'm"
        ),
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "🏠 Bosh sahifa",
                    callback_data="back"
                )
            ]
        ])
    )


# =========================================================
# ORDERS
# =========================================================

async def show_orders(query):

    con = db()

    orders = con.execute(
        """
        SELECT id, item, amount, status
        FROM orders
        WHERE user_id=?
        ORDER BY id DESC
        LIMIT 10
        """,
        (query.from_user.id,)
    ).fetchall()

    con.close()

    if not orders:

        text = (
            "📋 BUYURTMALARIM\n\n"
            "Hozircha buyurtmalar yo‘q."
        )

    else:

        text = "📋 BUYURTMALARIM\n\n"

        for order_id, item, amount, status in orders:

            text += (
                f"📦 #{order_id}\n"
                f"🛍 {item}\n"
                f"💳 {amount:,} so'm\n"
                f"📌 {status}\n\n"
            )

    await query.edit_message_caption(
        caption=text,
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "🏠 Bosh sahifa",
                    callback_data="back"
                )
            ]
        ])
    )


# =========================================================
# HELP
# =========================================================

async def show_help(query):

    await query.edit_message_caption(
        caption=(
            "🔵 YORDAM\n\n"
            f"Savollar bo‘lsa:\n{ADMIN}"
        ),
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "🏠 Bosh sahifa",
                    callback_data="back"
                )
            ]
        ])
    )


# =========================================================
# INFO
# =========================================================

async def show_info(query):

    await query.edit_message_caption(
        caption=(
            "ℹ️ MA'LUMOT\n\n"
            "🌟 STARGIFT SHOP\n\n"
            "⭐ Stars\n"
            "🎁 Gifts\n"
            "💎 Premium\n\n"
            "⚡ Tez • 🔐 Ishonchli • 💳 So‘m"
        ),
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "🏠 Bosh sahifa",
                    callback_data="back"
                )
            ]
        ])
    )


# =========================================================
# SETTINGS
# =========================================================

async def show_settings(query):

    await query.edit_message_caption(
        caption=(
            "⚙️ SOZLAMA\n\n"
            "Hozircha sozlamalar mavjud emas."
        ),
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "🏠 Bosh sahifa",
                    callback_data="back"
                )
    
