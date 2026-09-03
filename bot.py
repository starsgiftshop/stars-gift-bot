
import os
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

TOKEN = os.getenv("BOT_TOKEN")
PAYMENT_URL = os.getenv("PAYMENT_URL", "")
STARS_PRICE = 195
ADMIN = "@Shamsbekman"

PACKAGES = {
    25:4875, 50:9750, 100:19500, 125:24375, 150:29250,
    175:34125, 200:39000, 300:58500, 400:78000, 500:97500
}
PREMIUM = {"1 oy":45000, "3 oy":164000, "6 oy":222000, "1 yil":377000}

def db():
    c = sqlite3.connect("shop.db")
    c.execute("""CREATE TABLE IF NOT EXISTS orders(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER, product TEXT, amount INTEGER,
        status TEXT DEFAULT 'pending'
    )""")
    c.commit()
    return c

def new_order(uid, product, amount):
    c = db()
    x = c.cursor()
    x.execute(
        "INSERT INTO orders(user_id,product,amount) VALUES(?,?,?)",
        (uid, product, amount)
    )
    c.commit()
    oid = x.lastrowid
    c.close()
    return oid

def main_menu():
    return ReplyKeyboardMarkup([
        ["⭐ Stars", "🎁 Gift", "💎 Premium"],
        ["💰 Balans", "👤 Profil", "📋 Buyurtma"],
        ["🔵 Yordam", "ℹ️ Ma'lumot", "⚙️ Sozlama"]
    ], resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⭐ Stars Gift Shop\n\nKerakli bo‘limni tanlang:",
        reply_markup=main_menu()
    )

async def stars(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rows = [
        [InlineKeyboardButton(
            f"⭐ {n} — {p:,} so‘m",
            callback_data=f"star:{n}"
        )]
        for n, p in PACKAGES.items()
    ]
    await update.message.reply_text(
        "⭐ Stars paketini tanlang:",
        reply_markup=InlineKeyboardMarkup(rows)
    )

async def premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rows = [
        [InlineKeyboardButton(
            f"💎 {n} — {p:,} so‘m",
            callback_data=f"prem:{n}"
        )]
        for n, p in PREMIUM.items()
    ]
    await update.message.reply_text(
        "💎 Premium paketini tanlang:",
        reply_markup=InlineKeyboardMarkup(rows)
    )

async def gifts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        result = await context.bot.get_available_gifts()
        gifts_list = result.gifts

        if not gifts_list:
            await update.message.reply_text("🎁 Hozircha Gift mavjud emas.")
            return

        # 3 USTUN — bitta ixcham menyu
        buttons = []
        for gift in gifts_list:
            stars = gift.star_count
            som = stars * STARS_PRICE

            # Giftning o'z stickeridagi emoji ishlatiladi.
            emoji = getattr(gift.sticker, "emoji", None) or "🎁"

            # Tugma qisqa bo'lishi uchun nom + Stars + so'm
            label = f"{emoji} {stars}⭐\n{som:,} so‘m"
            buttons.append(
                InlineKeyboardButton(label, callback_data=f"gift:{gift.id}")
            )

        rows = [buttons[i:i+3] for i in range(0, len(buttons), 3)]

        await update.message.reply_text(
            "🎁  GIFTLAR\n\n"
            f"⭐ 1 Star = {STARS_PRICE:,} so‘m\n\n"
            "Kerakli Giftni tanlang:",
            reply_markup=InlineKeyboardMarkup(rows)
        )

    except Exception as e:
        print("GIFTS ERROR:", repr(e))
        await update.message.reply_text(
            "❌ Giftlarni yuklashda xatolik.\n"
            "Railway logini tekshiring."
        )

async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    if q.data.startswith("star:"):
        n = int(q.data.split(":")[1])
        await show_payment(q, f"⭐ {n} Stars", PACKAGES[n])
        return

    if q.data.startswith("prem:"):
        name = q.data[5:]
        await show_payment(q, f"💎 Premium {name}", PREMIUM[name])
        return

    if q.data.startswith("gift:"):
        gid = q.data.split(":", 1)[1]

        try:
            result = await context.bot.get_available_gifts()
            gift = next((g for g in result.gifts if g.id == gid), None)

            if not gift:
                await q.message.reply_text("❌ Bu Gift hozir mavjud emas.")
                return

            stars = gift.star_count
            som = stars * STARS_PRICE
            emoji = getattr(gift.sticker, "emoji", None) or "🎁"

            # Tanlangan Giftning haqiqiy rasmini/stickerini ko‘rsatadi.
            try:
                await q.message.reply_sticker(gift.sticker.file_id)
            except Exception:
                pass

            await show_payment(
                q,
                f"{emoji} Gift — {stars} Stars",
                som
            )

        except Exception as e:
            print("GIFT ERROR:", repr(e))
            await q.message.reply_text("❌ Giftni ochishda xatolik.")

async def show_payment(q, product, amount):
    oid = new_order(q.from_user.id, product, amount)

    text = (
        f"📦 {product}\n"
        f"💰 {amount:,} so‘m\n"
        f"🧾 Buyurtma #{oid}\n\n"
    )

    if PAYMENT_URL:
        url = (
            PAYMENT_URL
            .replace("{order_id}", str(oid))
            .replace("{amount}", str(amount))
        )
        kb = InlineKeyboardMarkup([[
            InlineKeyboardButton("💳 SO‘MDA TO‘LASH", url=url)
        ]])
        await q.message.reply_text(text + "To‘lovni amalga oshiring:", reply_markup=kb)
    else:
        await q.message.reply_text(
            text +
            "💳 So‘mda to‘lov tugmasi Click/Payme API ulanganda ishlaydi."
        )

async def text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    t = update.message.text

    if t == "⭐ Stars":
        await stars(update, context)
    elif t == "🎁 Gift":
        await gifts(update, context)
    elif t == "💎 Premium":
        await premium(update, context)
    elif t == "💰 Balans":
        await update.message.reply_text("💰 Balans: 0 so‘m")
    elif t == "👤 Profil":
        await update.message.reply_text(
            f"👤 Telegram ID: {update.effective_user.id}"
        )
    elif t == "📋 Buyurtma":
        await update.message.reply_text("📋 Buyurtmalar shu yerda saqlanadi.")
    elif t == "🔵 Yordam":
        await update.message.reply_text(f"🔵 Yordam: {ADMIN}")
    elif t == "ℹ️ Ma'lumot":
        await update.message.reply_text("⭐ Stars Gift Shop")
    elif t == "⚙️ Sozlama":
        await update.message.reply_text("⚙️ Sozlama")

def main():
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN Railway Variables ga qo‘yilmagan.")

    db()

    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text))

    print("BOT IS RUNNING")
    app.run_polling()

if __name__ == "__main__":
    main()
        
