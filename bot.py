
import os, sqlite3, time
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
PREMIUM = [("1 oy",45000), ("3 oy",164000), ("6 oy",222000), ("1 yil",377000)]

def init_db():
    c = sqlite3.connect("shop.db")
    c.execute("""CREATE TABLE IF NOT EXISTS orders(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER, product TEXT, amount INTEGER,
        status TEXT DEFAULT 'pending', created INTEGER
    )""")
    c.commit(); c.close()

def add_order(uid, product, amount):
    c = sqlite3.connect("shop.db")
    cur = c.cursor()
    cur.execute("INSERT INTO orders(user_id,product,amount,created) VALUES(?,?,?,?,?)",
                (uid, product, amount, int(time.time())))
    c.commit(); oid = cur.lastrowid; c.close()
    return oid

def main_menu():
    return ReplyKeyboardMarkup([
        ["⭐ Stars", "🎁 Gift", "💎 Premium"],
        ["💰 Balans", "👤 Profil", "📋 Buyurtma"],
        ["🔵 Yordam", "ℹ️ Ma'lumot", "⚙️ Sozlama"]
    ], resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✨ Stars Gift Shop\n\nKerakli bo‘limni tanlang:",
        reply_markup=main_menu()
    )

async def stars_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # 2 ustun
    buttons = [
        InlineKeyboardButton(f"⭐ {n} — {p:,} so‘m", callback_data=f"S:{n}")
        for n, p in STARS
    ]
    rows = [buttons[i:i+2] for i in range(0, len(buttons), 2)]
    await update.message.reply_text(
        "⭐ STARS\n\n💰 1 Star = 195 so‘m\n\nPaketni tanlang:",
        reply_markup=InlineKeyboardMarkup(rows)
    )

async def premium_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    buttons = [
        InlineKeyboardButton(f"💎 {n} — {p:,} so‘m", callback_data=f"P:{i}")
        for i, (n, p) in enumerate(PREMIUM)
    ]
    rows = [buttons[i:i+2] for i in range(0, len(buttons), 2)]
    await update.message.reply_text(
        "💎 PREMIUM\n\nPaketni tanlang:",
        reply_markup=InlineKeyboardMarkup(rows)
    )

async def gift_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
                    callback_data=f"G:{g.id}"
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

async def payment(q, product, amount):
    oid = add_order(q.from_user.id, product, amount)
    text = (
        f"📦 {product}\n"
        f"💰 {amount:,} so‘m\n"
        f"🧾 Buyurtma #{oid}\n\n"
    )

    if PAYMENT_URL:
        url = PAYMENT_URL.replace("{order_id}", str(oid)).replace("{amount}", str(amount))
        await q.message.reply_text(
            text + "To‘lovni amalga oshiring:",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("💳 SO‘MDA TO‘LASH", url=url)
            ]])
        )
    else:
        await q.message.reply_text(
            text + "💳 So‘mda to‘lov tizimi hali ulanmagan."
        )

async def callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    try:
        if q.data.startswith("S:"):
            n = int(q.data[2:])
            price = dict(STARS)[n]
            await payment(q, f"⭐ {n} Stars", price)

        elif q.data.startswith("P:"):
            i = int(q.data[2:])
            name, price = PREMIUM[i]
            await payment(q, f"💎 Premium {name}", price)

        elif q.data.startswith("G:"):
            gid = q.data[2:]
            g = context.user_data.get("gifts", {}).get(gid)

            # Cache bo‘lmasa, bir marta qayta oladi
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

            await payment(q, f"{emoji} Gift — {stars} Stars", price)

    except Exception as e:
        print("CALLBACK ERROR:", repr(e))
        await q.message.reply_text("❌ Xatolik yuz berdi.")

async def text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    t = update.message.text

    if t == "⭐ Stars":
        await stars_menu(update, context)
    elif t == "🎁 Gift":
        await gift_menu(update, context)
    elif t == "💎 Premium":
        await premium_menu(update, context)
    elif t == "💰 Balans":
        await update.message.reply_text("💰 Balans: 0 so‘m")
    elif t == "👤 Profil":
        await update.message.reply_text(f"👤 Telegram ID: {update.effective_user.id}")
    elif t == "📋 Buyurtma":
        await update.message.reply_text("📋 Buyurtmalaringiz shu yerda ko‘rinadi.")
    elif t == "🔵 Yordam":
        await update.message.reply_text(f"🔵 Yordam: {ADMIN}")
    elif t == "ℹ️ Ma'lumot":
        await update.message.reply_text("✨ Stars Gift Shop")
    elif t == "⚙️ Sozlama":
        await update.message.reply_text("⚙️ Sozlamalar")

def main():
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN Railway Variables ga qo‘yilmagan.")
    init_db()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(callbacks))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text))
    print("BOT IS RUNNING")
    app.run_polling()

if __name__ == "__main__":
    main()
                    
