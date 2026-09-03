
import os
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

TOKEN = os.getenv("BOT_TOKEN")
PAYMENT_URL = os.getenv("PAYMENT_URL", "")  # Click/Payme sahifasi URL
ADMIN = "@Shamsbekman"
STARS_PRICE = 195

PACKAGES = {
    25: 4875, 50: 9750, 100: 19500, 125: 24375,
    150: 29250, 175: 34125, 200: 39000,
    300: 58500, 400: 78000, 500: 97500
}

PREMIUM = {
    "1 oy": 45000,
    "3 oy": 164000,
    "6 oy": 222000,
    "1 yil": 377000
}

def db():
    con = sqlite3.connect("shop.db")
    con.execute("""CREATE TABLE IF NOT EXISTS orders(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        product TEXT,
        amount INTEGER,
        status TEXT DEFAULT 'pending'
    )""")
    con.commit()
    return con

def order(user_id, product, amount):
    con = db()
    cur = con.cursor()
    cur.execute("INSERT INTO orders(user_id,product,amount) VALUES(?,?,?)",
                (user_id, product, amount))
    con.commit()
    oid = cur.lastrowid
    con.close()
    return oid

def menu():
    return ReplyKeyboardMarkup([
        ["⭐ Stars", "🎁 Gift", "💎 Premium"],
        ["💰 Balans", "👤 Profil", "📋 Buyurtma"],
        ["🔵 Yordam", "ℹ️ Ma'lumot", "⚙️ Sozlama"]
    ], resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⭐ Stars Gift Shop\n\nSo'mda to'lov qilish uchun paket tanlang.",
        reply_markup=menu()
    )

async def stars(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rows = []
    for n, price in PACKAGES.items():
        rows.append([InlineKeyboardButton(
            f"⭐ {n} Stars — {price:,} so'm",
            callback_data=f"star_{n}"
        )])
    await update.message.reply_text(
        "⭐ Stars paketini tanlang:",
        reply_markup=InlineKeyboardMarkup(rows)
    )

async def premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rows = []
    for name, price in PREMIUM.items():
        rows.append([InlineKeyboardButton(
            f"💎 {name} — {price:,} so'm",
            callback_data=f"prem_{name}"
        )])
    await update.message.reply_text(
        "💎 Premium paketini tanlang:",
        reply_markup=InlineKeyboardMarkup(rows)
    )

async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    if q.data.startswith("star_"):
        n = int(q.data.split("_")[1])
        product, amount = f"{n} Stars", PACKAGES[n]
    elif q.data.startswith("prem_"):
        name = q.data[5:]
        product, amount = f"Premium {name}", PREMIUM[name]
    else:
        return

    oid = order(q.from_user.id, product, amount)

    buttons = []
    if PAYMENT_URL:
        # Keyin PAYMENT_URL ni Click/Payme real to'lov sahifasiga almashtiramiz.
        pay_url = PAYMENT_URL.replace("{order_id}", str(oid)).replace(
            "{amount}", str(amount)
        )
        buttons.append([InlineKeyboardButton("💳 So'mda to'lash", url=pay_url)])

    text = (
        f"🧾 Buyurtma #{oid}\n"
        f"📦 {product}\n"
        f"💰 {amount:,} so'm\n\n"
    )

    if PAYMENT_URL:
        text += "To'lovni tugating. To'lov tasdiqlangach mahsulot beriladi."
    else:
        text += "💳 To'lov tizimi hali ulanmagan.\n"
        text += "Click/Payme ma'lumotlari kelgach shu joyga ulanadi."

    await q.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(buttons) if buttons else None
    )

async def text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    t = update.message.text
    if t == "⭐ Stars":
        await stars(update, context)
    elif t == "💎 Premium":
        await premium(update, context)
    elif t == "🎁 Gift":
        await update.message.reply_text("🎁 Gift bo'limi tayyorlanmoqda.")
    elif t == "💰 Balans":
        await update.message.reply_text("💰 Balans: 0 so'm")
    elif t == "👤 Profil":
        await update.message.reply_text(f"👤 Telegram ID: {update.effective_user.id}")
    elif t == "📋 Buyurtma":
        await update.message.reply_text("📋 Buyurtmalar saqlanadi.")
    elif t == "🔵 Yordam":
        await update.message.reply_text(f"🔵 Yordam: {ADMIN}")
    elif t == "ℹ️ Ma'lumot":
        await update.message.reply_text("⭐ Stars Gift Shop")
    elif t == "⚙️ Sozlama":
        await update.message.reply_text("⚙️ Sozlama")

def main():
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN Railway Variables ga qo'yilmagan.")
    db()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text))
    print("BOT IS RUNNING")
    app.run_polling()

if __name__ == "__main__":
    main()
                  
