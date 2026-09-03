
import os
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

TOKEN = os.getenv("BOT_TOKEN")
PAYMENT_URL = os.getenv("PAYMENT_URL", "")
ADMIN = "@Shamsbekman"
STARS_PRICE = 195

PACKAGES = {25:4875,50:9750,100:19500,125:24375,150:29250,175:34125,200:39000,300:58500,400:78000,500:97500}
PREMIUM = {"1 oy":45000,"3 oy":164000,"6 oy":222000,"1 yil":377000}

def db():
    c=sqlite3.connect("shop.db")
    c.execute("""CREATE TABLE IF NOT EXISTS orders(
        id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER,
        product TEXT,amount INTEGER,status TEXT DEFAULT 'pending')""")
    c.commit()
    return c

def new_order(uid,product,amount):
    c=db(); x=c.cursor()
    x.execute("INSERT INTO orders(user_id,product,amount) VALUES(?,?,?)",(uid,product,amount))
    c.commit(); oid=x.lastrowid; c.close()
    return oid

def menu():
    return ReplyKeyboardMarkup([
        ["⭐ Stars","🎁 Gift","💎 Premium"],
        ["💰 Balans","👤 Profil","📋 Buyurtma"],
        ["🔵 Yordam","ℹ️ Ma'lumot","⚙️ Sozlama"]
    ],resize_keyboard=True)

async def start(u:Update,ctx:ContextTypes.DEFAULT_TYPE):
    await u.message.reply_text("⭐ Stars Gift Shop\n\nKerakli bo‘limni tanlang:",reply_markup=menu())

async def stars(u:Update,ctx:ContextTypes.DEFAULT_TYPE):
    rows=[[InlineKeyboardButton(f"⭐ {n} — {p:,} so‘m",callback_data=f"star:{n}")]
          for n,p in PACKAGES.items()]
    await u.message.reply_text("⭐ Stars paketini tanlang:",reply_markup=InlineKeyboardMarkup(rows))

async def premium(u:Update,ctx:ContextTypes.DEFAULT_TYPE):
    rows=[[InlineKeyboardButton(f"💎 {n} — {p:,} so‘m",callback_data=f"prem:{n}")]
          for n,p in PREMIUM.items()]
    await u.message.reply_text("💎 Premium paketini tanlang:",reply_markup=InlineKeyboardMarkup(rows))

async def gifts(u:Update,ctx:ContextTypes.DEFAULT_TYPE):
    try:
        r=await ctx.bot.get_available_gifts()
        gs=r.gifts
        if not gs:
            await u.message.reply_text("🎁 Hozircha Gift mavjud emas.")
            return

        # Bitta xabarda ixcham ro‘yxat: 2 ta ustun
        buttons=[]
        for g in gs:
            som=g.star_count*STARS_PRICE
            buttons.append(InlineKeyboardButton(
                f"🎁 {g.star_count} ⭐ — {som:,} so‘m",
                callback_data=f"gift:{g.id}"
            ))

        rows=[buttons[i:i+2] for i in range(0,len(buttons),2)]
        await u.message.reply_text(
            f"🎁 Giftlar\n\n⭐ 1 Star = {STARS_PRICE} so‘m\n\nGiftni tanlang:",
            reply_markup=InlineKeyboardMarkup(rows)
        )
    except Exception as e:
        print("GIFTS ERROR:",e)
        await u.message.reply_text("❌ Giftlarni olishda xatolik.")

async def callback(u:Update,ctx:ContextTypes.DEFAULT_TYPE):
    q=u.callback_query
    await q.answer()

    if q.data.startswith("star:"):
        n=int(q.data.split(":")[1]); product=f"{n} Stars"; amount=PACKAGES[n]
        await show_payment(q,product,amount)
        return

    if q.data.startswith("prem:"):
        n=q.data[5:]; product=f"Premium {n}"; amount=PREMIUM[n]
        await show_payment(q,product,amount)
        return

    if q.data.startswith("gift:"):
        gid=q.data.split(":",1)[1]
        try:
            r=await ctx.bot.get_available_gifts()
            g=next((x for x in r.gifts if x.id==gid),None)
            if not g:
                await q.message.reply_text("❌ Bu Gift hozir mavjud emas.")
                return

            som=g.star_count*STARS_PRICE

            # Tanlangan Giftning rasmini/stickerini ko‘rsatish
            try:
                await q.message.reply_sticker(g.sticker.file_id)
            except Exception:
                pass

            await show_payment(q,f"Gift ({g.star_count} Stars)",som)
        except Exception as e:
            print("GIFT ERROR:",e)
            await q.message.reply_text("❌ Giftni ochishda xatolik.")

async def show_payment(q,product,amount):
    oid=new_order(q.from_user.id,product,amount)
    text=f"🎁 {product}\n💰 {amount:,} so‘m\n🧾 Buyurtma #{oid}\n\n"

    if PAYMENT_URL:
        url=PAYMENT_URL.replace("{order_id}",str(oid)).replace("{amount}",str(amount))
        kb=InlineKeyboardMarkup([[InlineKeyboardButton("💳 SO‘MDA TO‘LASH",url=url)]])
        text+="To‘lovni amalga oshiring:"
        await q.message.reply_text(text,reply_markup=kb)
    else:
        text+="💳 So‘mda to‘lov tizimi ulanmagan.\nClick/Payme API ulanganda tugma ishlaydi."
        await q.message.reply_text(text)

async def text(u:Update,ctx:ContextTypes.DEFAULT_TYPE):
    t=u.message.text
    if t=="⭐ Stars": await stars(u,ctx)
    elif t=="🎁 Gift": await gifts(u,ctx)
    elif t=="💎 Premium": await premium(u,ctx)
    elif t=="💰 Balans": await u.message.reply_text("💰 Balans: 0 so‘m")
    elif t=="👤 Profil": await u.message.reply_text(f"👤 Telegram ID: {u.effective_user.id}")
    elif t=="📋 Buyurtma": await u.message.reply_text("📋 Buyurtmalar shu yerda saqlanadi.")
    elif t=="🔵 Yordam": await u.message.reply_text(f"🔵 Yordam: {ADMIN}")
    elif t=="ℹ️ Ma’lumot": await u.message.reply_text("⭐ Stars Gift Shop")
    elif t=="⚙️ Sozlama": await u.message.reply_text("⚙️ Sozlama")

def main():
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN Railway Variables ga qo‘yilmagan.")
    db()
    app=Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start",start))
    app.add_handler(CallbackQueryHandler(callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,text))
    print("BOT IS RUNNING")
    app.run_polling()

if __name__=="__main__":
    main()
            
