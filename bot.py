
import os
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

TOKEN = os.getenv("BOT_TOKEN")
PAYMENT_URL = os.getenv("PAYMENT_URL", "")  # Masalan: https://saytingiz.uz/pay?order_id={order_id}&amount={amount}
ADMIN = "@Shamsbekman"
STARS_PRICE = 195

PACKAGES = {
    25: 4875, 50: 9750, 100: 19500, 125: 24375,
    150: 29250, 175: 34125, 200: 39000,
    300: 58500, 400: 78000, 500: 97500
}
PREMIUM = {"1 oy":45000, "3 oy":164000, "6 oy":222000, "1 yil":377000}

def db():
    con = sqlite3.connect("shop.db")
    con.execute("""CREATE TABLE IF NOT EXISTS orders(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER, product TEXT, amount INTEGER,
        status TEXT DEFAULT 'pending'
    )""")
    con.commit()
    return con

def new_order(user_id, product, amount):
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
        ["⭐ Stars","🎁 Gift","💎 Premium"],
        ["💰 Balans","👤 Profil","📋 Buyurtma"],
        ["🔵 Yordam","ℹ️ Ma'lumot","⚙️ Sozlama"]
    ], resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⭐ Stars Gift Shop\n\nSo'mda to'lov qilish uchun bo'limni tanlang.",
        reply_markup=menu()
    )

async def stars(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rows = [[InlineKeyboardButton(f"⭐ {n} Stars — {p:,} so'm",
                                  callback_data=f"star:{n}")]
            for n,p in PACKAGES.items()]
    await update.message.reply_text("⭐ Stars paketini tanlang:",
                                    reply_markup=InlineKeyboardMarkup(rows))

async def premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rows = [[InlineKeyboardButton(f"💎 {n} — {p:,} so'm",
                                  callback_data=f"prem:{n}")]
            for n,p in PREMIUM.items()]
    await update.message.reply_text("💎 Premium paketini tanlang:",
                                    reply_markup=InlineKeyboardMarkup(rows))

async def gifts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        result = await context.bot.get_available_gifts()
        gifts_list = result.gifts

        if not gifts_list:
            await update.message.reply_text("🎁 Hozircha Gift mavjud emas.")
            return

        await update.message.reply_text(
            f"🎁 Mavjud Giftlar: {len(gifts_list)} ta\n"
            f"💰 Narx avtomatik hisoblanadi: 1 Star = {STARS_PRICE} so'm"
        )

        for gift in gifts_list:
            stars = gift.star_count
            som = stars * STARS_PRICE
            name = getattr(gift, "name", None) or "Telegram Gift"

            # Giftning Telegramdagi rasmini/stickerini yuboramiz
            try:
                await update.message.reply_sticker(
                    sticker=gift.sticker.file_id
                )
            except Exception:
                pass

            kb = InlineKeyboardMarkup([[
                InlineKeyboardButton(
                    f"💳 {som:,} so'mda to'lash",
                    callback_data=f"gift:{gift.id}"
                )
            ]])

            await update.message.reply_text(
                f"🎁 {name}\n"
                f"⭐ {stars} Stars\n"
                f"💰 {som:,} so'm",
                reply_markup=kb
            )

    except Exception as e:
        print("GIFTS ERROR:", e)
        await update.message.reply_text(
            "🎁 Giftlarni olishda xatolik yuz berdi. Keyinroq urinib ko'ring."
        )

async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    if q.data.startswith("star:"):
        n = int(q.data.split(":")[1])
        product, amount = f"{n} Stars", PACKAGES[n]

    elif q.data.startswith("prem:"):
        name = q.data[5:]
        product, amount = f"Premium {name}", PREMIUM[name]

    elif q.data.startswith("gift:"):
        gift_id = q.data.split(":",1)[1]
        try:
            result = await context.bot.get_available_gifts()
            gift = next((g for g in result.gifts if g.id == gift_id), None)
            if not gift:
                await q.message.reply_text("❌ Bu Gift hozir mavjud emas.")
                return
            product = f"Gift {gift.id}"
            amount = gift.star_count * STARS_PRICE
        except Exception:
            await q.message.reply_text("❌ Gift ma'lumotini olishda xatolik.")
            return
    else:
        return

    oid = new_order(q.from_user.id, product, amount)

    if PAYMENT_URL:
        url = (PAYMENT_URL.replace("{order_id}", str(oid))
                         .replace("{amount}", str(amount)))
        kb = InlineKeyboardMarkup([[
            InlineKeyboardButton("💳 SO'MDA TO'LASH", url=url)
        ]])
        await q.message.reply_text(
            f"🧾 Buyurtma #{oid}\n"
            f"📦 {product}\n"
            f"💰 {amount:,} so'm\n\n"
            "To'lovni tugating.",
            reply_markup=kb
        )
    else:
        await q.message.reply_text(
            f"🧾 Buyurtma #{oid}\n"
            f"📦 {product}\n"
            f"💰 {amount:,} so'm\n\n"
            "💳 So'mda to'lov tugmasi Click/Payme API "
            "ulanganidan keyin ishlaydi."
        )

async def text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    t = update.message.text
    if t == "⭐ Stars": await stars(update, context)
    elif t == "🎁 Gift": await gifts(update, context)
    elif t == "💎 Premium": await premium(update, context)
    elif t == "💰 Balans": await update.message.reply_text("💰 Balans: 0 so'm")
    elif t == "👤 Profil": await update.message.reply_text(f"👤 Telegram ID: {update.effective_user.id}")
    elif t == "📋 Buyurtma": await update.message.reply_text("📋 Buyurtmalar shu yerda saqlanadi.")
    elif t == "🔵 Yordam": await update.message.reply_text(f"🔵 Yordam: {ADMIN}")
    elif t == "ℹ️ Ma'lumot": await update.message.reply_text("⭐ Stars Gift Shop")
    elif t == "⚙️ Sozlama": await update.message.reply_text("⚙️ Sozlama")

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
            
