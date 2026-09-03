import os
import sqlite3
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

TOKEN = os.getenv("BOT_TOKEN")
PAYMENT_URL = os.getenv("PAYMENT_URL", "")
ADMIN = "@Shamsbekman"
STAR_SOM = 195

STARS = [
    (25, 4875), (50, 9750), (100, 19500), (125, 24375),
    (150, 29250), (175, 34125), (200, 39000),
    (300, 58500), (400, 78000), (500, 97500)
]

PREMIUM = [
    ("1 oy", 45000),
    ("3 oy", 164000),
    ("6 oy", 222000),
    ("12 oy", 377000)
]

TOPUP = [10000, 20000, 50000, 100000, 200000, 500000]

def db():
    c = sqlite3.connect("shop.db")
    c.execute("""CREATE TABLE IF NOT EXISTS users(
        user_id INTEGER PRIMARY KEY,
        balance INTEGER DEFAULT 0
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS orders(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        product TEXT,
        amount INTEGER,
        status TEXT DEFAULT 'pending',
        created INTEGER
    )""")
    c.commit()
    c.close()

def balance(uid):
    c = sqlite3.connect("shop.db")
    row = c.execute("SELECT balance FROM users WHERE user_id=?", (uid,)).fetchone()
    if not row:
        c.execute("INSERT INTO users(user_id,balance) VALUES(?,0)", (uid,))
        c.commit()
        value = 0
    else:
        value = row[0]
    c.close()
    return value

def order(uid, product, amount):
    c = sqlite3.connect("shop.db")
    cur = c.cursor()
    cur.execute(
        "INSERT INTO orders(user_id,product,amount,created) VALUES(?,?,?,?)",
        (uid, product, amount, int(time.time()))
    )
    c.commit()
    oid = cur.lastrowid
    c.close()
    return oid

def menu():
    return ReplyKeyboardMarkup([
        ["⭐ Stars", "🎁 Gift", "💎 Premium"],
        ["💰 Balans", "➕ Hisob to‘ldirish", "👤 Profil"],
        ["📋 Buyurtma", "🔵 Yordam", "ℹ️ Ma'lumot"],
        ["⚙️ Sozlama"]
    ], resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    balance(update.effective_user.id)
    await update.message.reply_text(
        "✨ Stars Gift Shop\n\nKerakli bo‘limni tanlang:",
        reply_markup=menu()
    )

async def stars(update: Update, context: ContextTypes.DEFAULT_TYPE):
    buttons = [
        InlineKeyboardButton(
            f"⭐ {n} — {price:,} so‘m",
            callback_data=f"S{n}"
        )
        for n, price in STARS
    ]
    rows = [buttons[i:i+2] for i in range(0, len(buttons), 2)]
    await update.message.reply_text(
        "⭐ STARS\n\n💰 1 Star = 195 so‘m\n\nPaketni tanlang:",
        reply_markup=InlineKeyboardMarkup(rows)
    )

async def premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    buttons = [
        InlineKeyboardButton(
            f"💎 {name} — {price:,} so‘m",
            callback_data=f"P{i}"
        )
        for i, (name, price) in enumerate(PREMIUM)
    ]
    rows = [buttons[i:i+2] for i in range(0, len(buttons), 2)]
    await update.message.reply_text(
        "💎 PREMIUM\n\nMuddatni tanlang:",
        reply_markup=InlineKeyboardMarkup(rows)
    )

async def gifts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        result = await context.bot.get_available_gifts()
        gifts = result.gifts

        if not gifts:
            await update.message.reply_text("🎁 Hozircha Gift mavjud emas.")
            return

        context.user_data["gifts"] = {g.id: g for g in gifts}

        buttons = []
        for g in gifts:
            stars = g.star_count
            som = stars * STAR_SOM
            emoji = getattr(g.sticker, "emoji", None) or "🎁"
            buttons.append(
                InlineKeyboardButton(
                    f"{emoji} {stars}⭐ · {som:,} so‘m",
                    callback_data=f"G{g.id}"
                )
            )

        rows = [buttons[i:i+2] for i in range(0, len(buttons), 2)]
        await update.message.reply_text(
            "🎁 GIFTLAR\n\n⭐ 1 Star = 195 so‘m\n\nGiftni tanlang:",
            reply_markup=InlineKeyboardMarkup(rows)
        )
    except Exception as e:
        print("GIFT ERROR:", repr(e))
        await update.message.reply_text("❌ Giftlarni yuklashda xatolik.")

async def show_payment(q, product, amount):
    oid = order(q.from_user.id, product, amount)

    text = (
        f"📦 {product}\n"
        f"💰 {amount:,} so‘m\n"
        f"🧾 Buyurtma #{oid}\n\n"
    )

    if PAYMENT_URL:
        url = PAYMENT_URL.replace("{order_id}", str(oid)).replace(
            "{amount}", str(amount)
        )
        kb = InlineKeyboardMarkup([[
            InlineKeyboardButton("💳 SO‘MDA TO‘LASH", url=url)
        ]])
        await q.message.reply_text(text + "To‘lovni amalga oshiring:", reply_markup=kb)
    else:
        await q.message.reply_text(
            text + "💳 To‘lov tizimi hali ulanmagan."
        )

async def topup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    buttons = [
        InlineKeyboardButton(
            f"💰 {amount:,} so‘m",
            callback_data=f"T{amount}"
        )
        for amount in TOPUP
    ]
    rows = [buttons[i:i+2] for i in range(0, len(buttons), 2)]
    await update.message.reply_text(
        "➕ HISOB TO‘LDIRISH\n\n"
        "Balansingizga qo‘shiladigan summani tanlang:",
        reply_markup=InlineKeyboardMarkup(rows)
    )

async def callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query

    try:
        await q.answer()

        data = q.data

        if data.startswith("S"):
            n = int(data[1:])
            price = dict(STARS)[n]
            await show_payment(q, f"⭐ {n} Stars", price)
            return

        if data.startswith("P"):
            i = int(data[1:])
            if i < 0 or i >= len(PREMIUM):
                raise ValueError("premium index")
            name, price = PREMIUM[i]
            await show_payment(q, f"💎 Premium {name}", price)
            return

        if data.startswith("T"):
            amount = int(data[1:])
            await show_payment(q, f"💰 Balans to‘ldirish", amount)
            return

        if data.startswith("G"):
            gid = data[1:]
            g = context.user_data.get("gifts", {}).get(gid)

            if g is None:
                result = await context.bot.get_available_gifts()
                g = next((x for x in result.gifts if x.id == gid), None)

            if g is None:
                await q.message.reply_text("❌ Gift topilmadi.")
                return

            stars = g.star_count
            price = stars * STAR_SOM
            emoji = getattr(g.sticker, "emoji", None) or "🎁"

            try:
                await q.message.reply_sticker(g.sticker.file_id)
            except Exception:
                pass

            await show_payment(q, f"{emoji} Gift — {stars} Stars", price)
            return

    except Exception as e:
        print("CALLBACK ERROR:", repr(e))
        try:
            await q.message.reply_text("❌ Xatolik yuz berdi. Qayta urinib ko‘ring.")
        except Exception:
            pass

async def text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    t = update.message.text
    uid = update.effective_user.id

    if t == "⭐ Stars":
        await stars(update, context)
    elif t == "🎁 Gift":
        await gifts(update, context)
    elif t == "💎 Premium":
        await premium(update, context)
    elif t == "💰 Balans":
        await update.message.reply_text(
            f"💰 Sizning balansingiz: {balance(uid):,} so‘m"
        )
    elif t == "➕ Hisob to‘ldirish":
        await topup(update, context)
    elif t == "👤 Profil":
        await update.message.reply_text(
            f"👤 Profil\n\nTelegram ID: {uid}\n💰 Balans: {balance(uid):,} so‘m"
        )
    elif t == "📋 Buyurtma":
        await update.message.reply_text("📋 Buyurtmalar shu yerda ko‘rinadi.")
    elif t == "🔵 Yordam":
        await update.message.reply_text(f"🔵 Yordam: {ADMIN}")
    elif t == "ℹ️ Ma'lumot":
        await update.message.reply_text(
            "✨ Stars Gift Shop\n\n⭐ 1 Star = 195 so‘m"
        )
    elif t == "⚙️ Sozlama":
        await update.message.reply_text("⚙️ Sozlamalar")

def main():
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN Railway Variables ga qo‘yilmagan.")
    db()

    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(callbacks))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text))

    print("BOT IS RUNNING")
    app.run_polling()

if __name__ == "__main__":
    main()

