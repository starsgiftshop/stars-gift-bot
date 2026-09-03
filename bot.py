import os
import sqlite3
import hashlib
import time
from flask import Flask, request, jsonify
from threading import Thread

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = os.getenv("BOT_TOKEN")

# CLICK MA'LUMOTLARI — KEYIN QO'YAMIZ
CLICK_MERCHANT_ID = os.getenv("CLICK_MERCHANT_ID", "")
CLICK_SERVICE_ID = os.getenv("CLICK_SERVICE_ID", "")
CLICK_SECRET_KEY = os.getenv("CLICK_SECRET_KEY", "")
PAYMENT_URL = "https://my.click.uz/services/pay"

STARS_PRICE = 195

PACKAGES = {
    25: 4875,
    50: 9750,
    100: 19500,
    125: 24375,
    150: 29250,
    175: 34125,
    200: 39000,
    300: 58500,
    400: 78000,
    500: 97500,
}

PREMIUM = {
    "1 oy": 45000,
    "3 oy": 164000,
    "6 oy": 222000,
    "1 yil": 377000,
}

app_web = Flask(__name__)


def db():
    con = sqlite3.connect("shop.db")
    con.execute("""
        CREATE TABLE IF NOT EXISTS orders(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            product TEXT,
            amount INTEGER,
            status TEXT DEFAULT 'pending',
            created INTEGER
        )
    """)
    con.commit()
    return con


def create_order(user_id, product, amount):
    con = db()
    cur = con.cursor()
    cur.execute(
        "INSERT INTO orders(user_id,product,amount,created) VALUES(?,?,?,?,?)",
        (user_id, product, amount, int(time.time()))
    )
    con.commit()
    oid = cur.lastrowid
    con.close()
    return oid


def keyboard():
    return ReplyKeyboardMarkup([
        ["⭐ Stars", "🎁 Gift", "💎 Premium"],
        ["💰 Balans", "👤 Profil", "📋 Buyurtma"],
        ["🔵 Yordam", "ℹ️ Ma'lumot", "⚙️ Sozlama"]
    ], resize_keyboard=True)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⭐ Stars Gift Shop\n\nSo'mda to'lov qiling.",
        reply_markup=keyboard()
    )


async def stars(update: Update, context: ContextTypes.DEFAULT_TYPE):
    buttons = []
    for stars_count, price in PACKAGES.items():
        buttons.append([
            InlineKeyboardButton(
                f"⭐ {stars_count} Stars — {price:,} so'm",
                callback_data=f"star:{stars_count}"
            )
        ])

    await update.message.reply_text(
        "⭐ Stars paketini tanlang:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )


async def premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    buttons = []
    for name, price in PREMIUM.items():
        buttons.append([
            InlineKeyboardButton(
                f"💎 {name} — {price:,} so'm",
                callback_data=f"prem:{name}"
            )
        ])

    await update.message.reply_text(
        "💎 Premium tanlang:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )


async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    if q.data.startswith("star:"):
        count = int(q.data.split(":")[1])
        amount = PACKAGES[count]
        product = f"{count} Stars"

    elif q.data.startswith("prem:"):
        name = q.data.split(":", 1)[1]
        amount = PREMIUM[name]
        product = f"Premium {name}"

    else:
        return

    order_id = create_order(q.from_user.id, product, amount)

    if not CLICK_MERCHANT_ID or not CLICK_SERVICE_ID:
        await q.message.reply_text(
            f"🧾 Buyurtma #{order_id}\n"
            f"📦 {product}\n"
            f"💰 {amount:,} so'm\n\n"
            "💳 Click to'lovi hozircha ulanmagan.\n"
            "Click ma'lumotlari kelgach avtomatik ulanadi."
        )
        return

    url = (
        f"{PAYMENT_URL}"
        f"?service_id={CLICK_SERVICE_ID}"
        f"&merchant_id={CLICK_MERCHANT_ID}"
        f"&amount={amount}"
        f"&transaction_param={order_id}"
    )

    await q.message.reply_text(
        f"🧾 Buyurtma #{order_id}\n"
        f"📦 {product}\n"
        f"💰 {amount:,} so'm\n\n"
        f"💳 To'lov qilish:\n{url}"
    )


async def text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    t = update.message.text

    if t == "⭐ Stars":
        await stars(update, context)
    elif t == "💎 Premium":
        await premium(update, context)
    elif t == "🎁 Gift":
        await update.message.reply_text("🎁 Gift bo'limi tez orada.")
    elif t == "💰 Balans":
        await update.message.reply_text("💰 Balans: 0 so'm")
    elif t == "👤 Profil":
        await update.message.reply_text(f"👤 ID: {update.effective_user.id}")
    elif t == "📋 Buyurtma":
        await update.message.reply_text("📋 Buyurtmalaringiz shu yerda chiqadi.")
    elif t == "🔵 Yordam":
        await update.message.reply_text("🔵 Yordam: @Shamsbekman")
    elif t == "ℹ️ Ma'lumot":
        await update.message.reply_text("⭐ Stars Gift Shop")
    elif t == "⚙️ Sozlama":
        await update.message.reply_text("⚙️ Sozlamalar")


# Click prepare
@app_web.post("/click/prepare")
def click_prepare():
    data = request.form

    amount = float(data.get("amount", 0))
    order_id = data.get("merchant_trans_id")

    con = db()
    cur = con.cursor()
    cur.execute("SELECT amount FROM orders WHERE id=?", (order_id,))
    row = cur.fetchone()
    con.close()

    if not row or float(row[0]) != amount:
        return jsonify({
            "error": -2,
            "error_note": "Order not found"
        })

    return jsonify({
        "click_trans_id": data.get("click_trans_id"),
        "merchant_trans_id": order_id,
        "merchant_prepare_id": order_id,
        "error": 0,
        "error_note": "Success"
    })


# Click complete
@app_web.post("/click/complete")
def click_complete():
    data = request.form
    order_id = data.get("merchant_trans_id")

    con = db()
    con.execute(
        "UPDATE orders SET status='paid' WHERE id=?",
        (order_id,)
    )
    con.commit()
    con.close()

    return jsonify({
        "click_trans_id": data.get("click_trans_id"),
        "merchant_trans_id": order_id,
        "merchant_confirm_id": order_id,
        "error": 0,
        "error_note": "Success"
    })


def run_web():
    app_web.run(host="0.0.0.0", port=int(os.getenv("PORT", 8080)))


def main():
    db()

    Thread(target=run_web, daemon=True).start()

    bot = Application.builder().token(TOKEN).build()

    bot.add_handler(CommandHandler("start", start))
    bot.add_handler(CallbackQueryHandler(callback))
    bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text))

    print("BOT IS RUNNING")
    bot.run_polling()


if __name__ == "__main__":
    main()
