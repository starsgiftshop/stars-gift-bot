import os
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters
)

TOKEN = os.getenv("BOT_TOKEN")
ADMIN = "@Shamsbekman"
START_IMAGE = "stargift_start.png"

STAR_PRICE = 195
PREMIUM = [
    ("1 oy", 45000),
    ("3 oy", 164000),
    ("6 oy", 222000),
    ("12 oy", 377000),
]
TOPUP = [10000, 20000, 50000, 100000, 200000, 500000]


# =========================
# DATABASE
# =========================
def db():
    con = sqlite3.connect("shop.db")
    con.execute("""
        CREATE TABLE IF NOT EXISTS users(
            user_id INTEGER PRIMARY KEY,
            balance INTEGER DEFAULT 0,
            joined_at INTEGER DEFAULT (strftime('%s','now'))
        )
    """)
    con.execute("""
        CREATE TABLE IF NOT EXISTS orders(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            item TEXT,
            amount INTEGER,
            status TEXT DEFAULT 'pending',
            created_at INTEGER DEFAULT (strftime('%s','now'))
        )
    """)
    con.commit()
    return con


def ensure_user(user_id):
    con = db()
    con.execute("INSERT OR IGNORE INTO users(user_id, balance) VALUES(?,0)", (user_id,))
    con.commit()
    con.close()


def balance(user_id):
    ensure_user(user_id)
    con = db()
    row = con.execute("SELECT balance FROM users WHERE user_id=?", (user_id,)).fetchone()
    con.close()
    return row[0] if row else 0


def create_order(user_id, item, amount):
    con = db()
    cur = con.execute(
        "INSERT INTO orders(user_id,item,amount,status) VALUES(?,?,?,'pending')",
        (user_id, item, amount)
    )
    con.commit()
    order_id = cur.lastrowid
    con.close()
    return order_id


# =========================
# KEYBOARDS
# =========================
MAIN_MENU = ReplyKeyboardMarkup(
    [
        [KeyboardButton("🎁 Donat qilish"), KeyboardButton("📦 Xizmatlar")],
        [KeyboardButton("💳 Pul kiritish"), KeyboardButton("💵 Hisobim")],
        [KeyboardButton("👥 Referal"), KeyboardButton("📊 Buyurtmalarim")],
        [KeyboardButton("📢 Kanal ulash"), KeyboardButton("☎️ Qo'llab-quvvatlash")],
        [KeyboardButton("🤝 Hamkorlik dasturi")],
    ],
    resize_keyboard=True,
    is_persistent=True,
    input_field_placeholder="Bo'limni tanlang..."
)


def services_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("⭐ Stars", callback_data="stars"),
            InlineKeyboardButton("🎁 Gift", callback_data="gift"),
            InlineKeyboardButton("💎 Premium", callback_data="premium"),
        ],
        [InlineKeyboardButton("⬅️ Bosh sahifa", callback_data="home")]
    ])


def stars_keyboard():
    amounts = [25, 50, 100, 125, 150, 175, 200, 300, 400, 500]
    rows = []
    row = []
    for n in amounts:
        row.append(
            InlineKeyboardButton(
                f"⭐ {n} — {n * STAR_PRICE:,} so'm".replace(",", " "),
                callback_data=f"star:{n}"
            )
        )
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton("⬅️ Xizmatlar", callback_data="services")])
    return InlineKeyboardMarkup(rows)


def premium_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💎 1 oy — 45 000 so'm", callback_data="prem:0")],
        [InlineKeyboardButton("💎 3 oy — 164 000 so'm", callback_data="prem:1")],
        [InlineKeyboardButton("💎 6 oy — 222 000 so'm", callback_data="prem:2")],
        [InlineKeyboardButton("💎 12 oy — 377 000 so'm", callback_data="prem:3")],
        [InlineKeyboardButton("⬅️ Xizmatlar", callback_data="services")]
    ])


def topup_keyboard():
    rows = []
    row = []
    for amount in TOPUP:
        row.append(
            InlineKeyboardButton(
                f"💳 {amount:,} so'm".replace(",", " "),
                callback_data=f"topup:{amount}"
            )
        )
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton("⬅️ Bosh sahifa", callback_data="home")])
    return InlineKeyboardMarkup(rows)


# =========================
# START
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    ensure_user(user.id)

    text = (
        "💙✨ STARGIFT SHOP ✨💙\n\n"
        "⭐ Stars  •  🎁 Gift  •  💎 Premium\n"
        "⚡ Tez xizmat  •  🔐 Ishonchli  •  💳 So'm\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🌟 SIFAT • TEZLIK • ISHONCH 🌟\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "Quyidagi menyudan kerakli bo'limni tanlang:"
    )

    # START_IMAGE fayli GitHub repository ichida bo'lsa, Railway ham ko'radi.
    if os.path.exists(START_IMAGE):
        with open(START_IMAGE, "rb") as photo:
            await update.message.reply_photo(
                photo=photo,
                caption=text,
                reply_markup=MAIN_MENU
            )
    else:
        await update.message.reply_text(text, reply_markup=MAIN_MENU)


# =========================
# TEXT MENU — NEO SMM USLUBI
# =========================
async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id
    ensure_user(user_id)

    if text == "📦 Xizmatlar":
        await update.message.reply_text(
            "📦 XIZMATLAR\n\nKerakli xizmatni tanlang:",
            reply_markup=services_keyboard()
        )

    elif text == "🎁 Donat qilish":
        await update.message.reply_text(
            "🎁 DONAT\n\n"
            "⭐ Stars, 🎁 Gift yoki 💎 Premium xarid qilishingiz mumkin.",
            reply_markup=services_keyboard()
        )

    elif text == "💳 Pul kiritish":
        await update.message.reply_text(
            "💳 HISOB TO'LDIRISH\n\n"
            "Summani tanlang:",
            reply_markup=topup_keyboard()
        )

    elif text == "💵 Hisobim":
        await update.message.reply_text(
            f"💵 HISOBIM\n\n"
            f"💰 Balans: {balance(user_id):,} so'm\n\n"
            "Hisobni to'ldirish uchun «💳 Pul kiritish» tugmasini bosing."
            .replace(",", " ")
        )

    elif text == "📊 Buyurtmalarim":
        con = db()
        rows = con.execute(
            "SELECT id,item,amount,status FROM orders "
            "WHERE user_id=? ORDER BY id DESC LIMIT 20",
            (user_id,)
        ).fetchall()
        con.close()

        if not rows:
            await update.message.reply_text(
                "📊 BUYURTMALARIM\n\n"
                "Sizda hozircha buyurtma yo'q. 😊"
            )
            return

        out = ["📊 BUYURTMALARIM\n"]
        for order_id, item, amount, status in rows:
            out.append(
                f"📦 #{order_id}\n"
                f"🛍 {item}\n"
                f"💳 {amount:,} so'm\n"
                f"📌 {status}\n".replace(",", " ")
            )
        await update.message.reply_text("\n".join(out))

    elif text == "👥 Referal":
        me = await context.bot.get_me()
        await update.message.reply_text(
            "👥 REFERAL\n\n"
            "Do'stingizga bot havolasini yuboring:\n"
            f"https://t.me/{me.username}?start=ref_{user_id}\n\n"
            "Referal tizimi keyingi bosqichda avtomatlashtiriladi."
        )

    elif text == "📢 Kanal ulash":
        await update.message.reply_text(
            "📢 KANAL ULASH\n\n"
            "Kanalni ulash uchun botga kanal admin huquqini bering,\n"
            "so'ng qo'llab-quvvatlash xizmatiga yozing:\n"
            f"{ADMIN}"
        )

    elif text == "☎️ Qo'llab-quvvatlash":
        await update.message.reply_text(
            "☎️ QO'LLAB-QUVVATLASH\n\n"
            f"Operator: {ADMIN}\n"
            "O'rtacha javob vaqti: 30 soniya."
        )

    elif text == "🤝 Hamkorlik dasturi":
        await update.message.reply_text(
            "🤝 HAMKORLIK DASTURI\n\n"
            "Hamkorlik bo'yicha murojaat uchun:\n"
            f"{ADMIN}"
        )

    else:
        await update.message.reply_text(
            "🏠 Bosh sahifa\n\nQuyidagi menyudan bo'limni tanlang:",
            reply_markup=MAIN_MENU
        )


# =========================
# CALLBACK BUTTONS
# =========================
async def callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id
    ensure_user(user_id)

    if data == "home":
        await query.message.reply_text(
            "🏠 BOSH SAHIFA\n\nKerakli bo'limni tanlang:",
            reply_markup=MAIN_MENU
        )

    elif data == "services":
        await query.edit_message_text(
            "📦 XIZMATLAR\n\nKerakli xizmatni tanlang:",
            reply_markup=services_keyboard()
        )

    elif data == "stars":
        await query.edit_message_text(
            "⭐ STARS\n\nPaketni tanlang:\n"
            f"1 Star = {STAR_PRICE} so'm",
            reply_markup=stars_keyboard()
        )

    elif data == "gift":
        await show_gifts(query, context.bot)

    elif data == "premium":
        await query.edit_message_text(
            "💎 PREMIUM\n\nMuddatni tanlang:",
            reply_markup=premium_keyboard()
        )

    elif data.startswith("star:"):
        n = int(data.split(":")[1])
        amount = n * STAR_PRICE
        order_id = create_order(user_id, f"{n} Stars", amount)
        await query.edit_message_text(
            f"⭐ {n} STARS\n\n"
            f"💳 Narxi: {amount:,} so'm\n"
            f"📦 Buyurtma: #{order_id}\n"
            f"⏱ O'rtacha: 30 soniya\n\n"
            "To'lov integratsiyasi ulangach, shu yerda avtomatik tasdiqlanadi."
            .replace(",", " "),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ Stars", callback_data="stars")],
                [InlineKeyboardButton("🏠 Bosh sahifa", callback_data="home")]
            ])
        )

    elif data.startswith("prem:"):
        index = int(data.split(":")[1])
        name, amount = PREMIUM[index]
        order_id = create_order(user_id, f"Premium {name}", amount)
        await query.edit_message_text(
            f"💎 PREMIUM {name}\n\n"
            f"💳 Narxi: {amount:,} so'm\n"
            f"📦 Buyurtma: #{order_id}\n"
            f"⏱ O'rtacha: 30 soniya\n\n"
            "To'lov integratsiyasi ulangach, avtomatik tasdiqlanadi."
            .replace(",", " "),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ Premium", callback_data="premium")],
                [InlineKeyboardButton("🏠 Bosh sahifa", callback_data="home")]
            ])
        )

    elif data.startswith("topup:"):
        amount = int(data.split(":")[1])
        order_id = create_order(user_id, "Hisob to'ldirish", amount)
        await query.edit_message_text(
            f"💳 HISOB TO'LDIRISH\n\n"
            f"💰 Summa: {amount:,} so'm\n"
            f"📦 Buyurtma: #{order_id}\n\n"
            "To'lov tizimi ulanmagan bo'lsa, buyurtma pending bo'lib turadi."
            .replace(",", " "),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("💳 Yana to'ldirish", callback_data="topup_menu")],
                [InlineKeyboardButton("🏠 Bosh sahifa", callback_data="home")]
            ])
        )

    elif data == "topup_menu":
        await query.edit_message_text(
            "💳 HISOB TO'LDIRISH\n\nSummani tanlang:",
            reply_markup=topup_keyboard()
        )

    elif data.startswith("gift_select:"):
        gift_id = data.split(":", 1)[1]
        await send_selected_gift(query, gift_id, context.bot)


# =========================
# TELEGRAM GIFTS
# =========================
async def show_gifts(query, bot):
    try:
        result = await bot.get_available_gifts()
        gifts = result.gifts
    except Exception as e:
        await query.edit_message_text(
            "🎁 GIFTLAR\n\n"
            "Giftlarni hozir olishning iloji bo'lmadi.\n"
            "Birozdan keyin qayta urinib ko'ring."
        )
        return

    if not gifts:
        await query.edit_message_text(
            "🎁 GIFTLAR\n\nHozircha mavjud Gift topilmadi.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ Xizmatlar", callback_data="services")]
            ])
        )
        return

    rows = []
    row = []
    # Bot API Gift obyektida nom maydoni bo'lmasligi mumkin.
    # Shuning uchun tugmada xavfsiz ravishda emoji + Stars + so'm ko'rsatiladi.
    for gift in gifts[:30]:
        stars = gift.star_count
        price = stars * STAR_PRICE
        label = f"🎁 {stars} ⭐ — {price:,} so'm".replace(",", " ")
        row.append(
            InlineKeyboardButton(label, callback_data=f"gift_select:{gift.id}")
        )
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)

    rows.append([InlineKeyboardButton("⬅️ Xizmatlar", callback_data="services")])

    await query.edit_message_text(
        "🎁 GIFTLAR\n\n"
        "Quyidan Giftni tanlang.\n"
        "Tanlaganingizda uning haqiqiy Telegram rasmi/stickeri ko'rsatiladi.",
        reply_markup=InlineKeyboardMarkup(rows)
    )


async def send_selected_gift(query, gift_id, bot):
    try:
        result = await bot.get_available_gifts()
        gift = next((g for g in result.gifts if str(g.id) == str(gift_id)), None)

        if gift is None:
            await query.message.reply_text("🎁 Bu Gift hozir mavjud emas.")
            return

        stars = gift.star_count
        price = stars * STAR_PRICE

        # Haqiqiy gift sticker rasmi
        await query.message.reply_sticker(gift.sticker.file_id)

        order_id = create_order(
            query.from_user.id,
            f"Gift {stars} Stars",
            price
        )

        await query.message.reply_text(
            f"🎁 GIFT\n\n"
            f"⭐ Qiymati: {stars} Stars\n"
            f"💳 Narxi: {price:,} so'm\n"
            f"📦 Buyurtma: #{order_id}\n"
            f"⏱ O'rtacha: 30 soniya\n\n"
            "To'lov integratsiyasi ulangach, avtomatik tasdiqlanadi."
            .replace(",", " "),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🎁 Giftlar", callback_data="gift")],
                [InlineKeyboardButton("🏠 Bosh sahifa", callback_data="home")]
            ])
        )

    except Exception:
        await query.message.reply_text(
            "❌ Giftni ko'rsatishda xatolik yuz berdi.\n"
            "Iltimos, qayta urinib ko'ring."
        )


# =========================
# ERROR HANDLER
# =========================
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    print("BOT ERROR:", repr(context.error))


# =========================
# MAIN
# =========================
def main():
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN Railway Variables ichida topilmadi.")

    db()

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(callbacks))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, menu))
    app.add_error_handler(error_handler)

    print("STARGIFT SHOP BOT IS RUNNING")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
    
