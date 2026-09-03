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

TOPUP = [10000, 20000, 50000, 100000, 200000, 500000]


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
        "SELECT balance FROM users WHERE user_id=?", (user_id,)
    ).fetchone()
    if row is None:
        con.execute(
            "INSERT INTO users(user_id,balance) VALUES(?,0)", (user_id,)
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
        "INSERT INTO orders(user_id,item,amount,status) VALUES(?,?,?,?)",
        (user_id, item, amount, "pending"),
    )
    con.commit()
    order_id = cur.lastrowid
    con.close()
    return order_id


def main_keyboard():
    return InlineKeyboardMarkup([
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
            InlineKeyboardButton("⚙️ Sozlama", callback_data="settings"),
        ],
    ])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "💙✨ STARGIFT SHOP ✨💙\n\n"
        "⭐ STARS  •  🎁 GIFTLAR  •  💎 PREMIUM\n"
        "⚡ Tez • 🔐 Ishonchli • 💳 So‘m\n\n"
        "Kerakli bo‘limni tanlang 👇"
    )

    # GitHub/Railway loyihasidagi stargift_start.png rasmi.
    image_path = "stargift_start.png"

    if os.path.exists(image_path):
        with open(image_path, "rb") as photo:
            await update.message.reply_photo(
                photo=photo,
                caption=text,
                reply_markup=main_keyboard(),
            )
    else:
        await update.message.reply_text(
            text + "\n\n⚠️ stargift_start.png topilmadi.",
            reply_markup=main_keyboard(),
        )


async def show_stars(query):
    keyboard = [
        [
            InlineKeyboardButton(
                f"⭐ {n} Stars — {n * STAR_PRICE:,} so'm",
                callback_data=f"star_{n}",
            )
        ]
        for n in [25, 50, 100, 125, 150, 175, 200, 300, 400, 500]
    ]
    keyboard.append([InlineKeyboardButton("⬅️ Orqaga", callback_data="back")])

    await query.edit_message_caption(
        caption="⭐ STARS\n\n1 Star = 195 so'm\n\nPaketni tanlang 👇",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def show_gifts(query, context):
    try:
        gifts = await context.bot.get_available_gifts()
    except Exception:
        await query.edit_message_caption(
            caption="🎁 GIFTLAR\n\nHozircha Gift ma'lumotlarini olishda xatolik.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("⬅️ Orqaga", callback_data="back")]]
            ),
        )
        return

    if not gifts.gifts:
        await query.edit_message_caption(
            caption="🎁 GIFTLAR\n\nHozircha mavjud Gift topilmadi.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("⬅️ Orqaga", callback_data="back")]]
            ),
        )
        return

    rows = []
    row = []

    for i, gift in enumerate(gifts.gifts):
        # Bot API Gift obyektida nom maydoni yo'q.
        # Shuning uchun uning haqiqiy sticker emojisini tugmada ko'rsatamiz.
        emoji = getattr(gift.sticker, "emoji", "🎁") or "🎁"
        price = gift.star_count * STAR_PRICE
        button = InlineKeyboardButton(
            f"{emoji} {gift.star_count}⭐ • {price:,} so'm",
            callback_data=f"gift_{gift.id}",
        )
        row.append(button)

        if len(row) == 2:
            rows.append(row)
            row = []

        if i >= 49:
            break

    if row:
        rows.append(row)

    rows.append([InlineKeyboardButton("⬅️ Orqaga", callback_data="back")])

    await query.edit_message_caption(
        caption=(
            "🎁 GIFTLAR\n\n"
            "Mavjud Giftlar quyida 👇\n"
            "Narxlar so'mda."
        ),
        reply_markup=InlineKeyboardMarkup(rows),
    )


async def gift_selected(query, context):
    gift_id = query.data[len("gift_"):]

    try:
        gifts = await context.bot.get_available_gifts()
        gift = next((g for g in gifts.gifts if g.id == gift_id), None)

        if gift is None:
            await query.answer("Gift topilmadi.", show_alert=True)
            return

        price = gift.star_count * STAR_PRICE
        emoji = getattr(gift.sticker, "emoji", "🎁") or "🎁"

        # Giftning haqiqiy Telegram sticker rasmini yuboramiz.
        try:
            await context.bot.send_sticker(
                chat_id=query.message.chat_id,
                sticker=gift.sticker.file_id,
            )
        except Exception:
            pass

        await query.message.reply_text(
            f"{emoji} Gift tanlandi!\n\n"
            f"⭐ Telegram narxi: {gift.star_count} Stars\n"
            f"💳 Bizdagi narxi: {price:,} so'm\n\n"
            "To‘lov integratsiyasi ulangandan keyin avtomatik beriladi.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ Giftlarga qaytish", callback_data="gift")],
                [InlineKeyboardButton("🏠 Bosh sahifa", callback_data="back")],
            ]),
        )
        await query.answer()

    except Exception:
        await query.answer("Giftni olishda xatolik yuz berdi.", show_alert=True)


async def show_premium(query):
    keyboard = []
    for i, (period, price) in enumerate(PREMIUM):
        keyboard.append([
            InlineKeyboardButton(
                f"💎 {period} — {price:,} so'm",
                callback_data=f"premium_{i}",
            )
        ])
    keyboard.append([InlineKeyboardButton("⬅️ Orqaga", callback_data="back")])

    await query.edit_message_caption(
        caption="💎 PREMIUM\n\nMuddatni tanlang 👇",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def show_balance(query):
    balance = get_balance(query.from_user.id)
    await query.edit_message_caption(
        caption=f"💰 BALANS\n\nBalansingiz: {balance:,} so'm",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ Hisob to‘ldirish", callback_data="topup")],
            [InlineKeyboardButton("⬅️ Orqaga", callback_data="back")],
        ]),
    )


async def show_topup(query):
    keyboard = []
    row = []

    for amount in TOPUP:
        row.append(
            InlineKeyboardButton(
                f"💳 {amount:,} so'm",
                callback_data=f"topup_{amount}",
            )
        )
        if len(row) == 2:
            keyboard.append(row)
            row = []

    if row:
        keyboard.append(row)

    keyboard.append([InlineKeyboardButton("⬅️ Orqaga", callback_data="back")])

    await query.edit_message_caption(
        caption="➕ HISOB TO‘LDIRISH\n\nSummani tanlang 👇",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "back":
        await query.edit_message_caption(
            caption=(
                "💙✨ STARGIFT SHOP ✨💙\n\n"
                "⭐ STARS  •  🎁 GIFTLAR  •  💎 PREMIUM\n"
                "⚡ Tez • 🔐 Ishonchli • 💳 So‘m\n\n"
                "Kerakli bo‘limni tanlang 👇"
            ),
            reply_markup=main_keyboard(),
        )

    elif data == "stars":
        await show_stars(query)

    elif data == "gift":
        await show_gifts(query, context)

    elif data.startswith("gift_"):
        await gift_selected(query, context)

    elif data == "premium":
        await show_premium(query)

    elif data.startswith("premium_"):
        index = int(data.split("_")[1])
        period, price = PREMIUM[index]
        order_id = create_order(query.from_user.id, f"Premium {period}", price)

        await query.edit_message_caption(
            caption=(
                f"💎 Premium — {period}\n\n"
                f"💳 Narxi: {price:,} so'm\n"
                f"📦 Buyurtma: #{order_id}\n\n"
                "To‘lov tizimi ulanmoqda."
            ),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ Premium", callback_data="premium")],
                [InlineKeyboardButton("🏠 Bosh sahifa", callback_data="back")],
            ]),
        )

    elif data == "balance":
        await show_balance(query)

    elif data == "topup":
        await show_topup(query)

    elif data.startswith("topup_"):
        amount = int(data.split("_")[1])
        order_id = create_order(query.from_user.id, "Hisob to‘ldirish", amount)

        await query.edit_message_caption(
            caption=(
                "➕ HISOB TO‘LDIRISH\n\n"
                f"💳 Summa: {amount:,} so'm\n"
                f"📦 Buyurtma: #{order_id}\n\n"
                "To‘lov tizimi ulanmoqda.\n"
                "Hozircha avtomatik balans qo‘shilmaydi."
            ),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ Summalar", callback_data="topup")],
                [InlineKeyboardButton("🏠 Bosh sahifa", callback_data="back")],
            ]),
        )

    elif data == "profile":
        balance = get_balance(query.from_user.id)
        await query.edit_message_caption(
            caption=(
                "👤 PROFIL\n\n"
                f"🆔 ID: {query.from_user.id}\n"
                f"💰 Balans: {balance:,} so'm"
            ),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ Orqaga", callback_data="back")]
            ]),
        )

    elif data == "help":
        await query.edit_message_caption(
            caption=f"🔵 YORDAM\n\nSavollar bo‘lsa: {ADMIN}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ Orqaga", callback_data="back")]
            ]),
        )

    elif data == "info":
        await query.edit_message_caption(
            caption=(
                "ℹ️ MA'LUMOT\n\n"
                "🌟 STARGIFT SHOP\n"
                "⭐ Stars • 🎁 Gifts • 💎 Premium\n"
                "⚡ O‘rtacha bajarilish vaqti: 30 soniya"
            ),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ Orqaga", callback_data="back")]
            ]),
        )

    elif data == "orders":
        await query.edit_message_caption(
            caption="📋 BUYURTMALAR\n\nHozircha buyurtmalar tarixi tayyorlanmoqda.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ Orqaga", callback_data="back")]
            ]),
        )

    elif data == "settings":
        await query.edit_message_caption(
            caption="⚙️ SOZLAMA\n\nHozircha sozlamalar mavjud emas.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ Orqaga", callback_data="back")]
            ]),
        )


def main():
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN environment variable topilmadi.")

    db()

    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.run_polling()


if __name__ == "__main__":
    main()
    
