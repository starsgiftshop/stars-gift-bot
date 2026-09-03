import os
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, BotCommand
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

TOKEN = os.getenv("BOT_TOKEN")
ADMIN = "@Shamsbekman"

STAR_PRICE = 195
PREMIUM = [
    ("1 oy", 45000),
    ("3 oy", 164000),
    ("6 oy", 222000),
    ("12 oy", 377000),
]
TOPUPS = [10000, 20000, 50000, 100000, 200000, 500000]

# Yangi baza: eski pending buyurtmalar aralashib ketmaydi.
DB_FILE = "stargift_v2.db"
START_IMAGE = "stargift_start.png"


def db():
    con = sqlite3.connect(DB_FILE)
    con.execute(
        "CREATE TABLE IF NOT EXISTS users "
        "(user_id INTEGER PRIMARY KEY, balance INTEGER NOT NULL DEFAULT 0)"
    )
    con.execute(
        "CREATE TABLE IF NOT EXISTS orders "
        "(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, "
        "item TEXT NOT NULL, amount INTEGER NOT NULL, status TEXT NOT NULL)"
    )
    con.commit()
    return con


def ensure_user(user_id):
    con = db()
    con.execute("INSERT OR IGNORE INTO users(user_id,balance) VALUES(?,0)", (user_id,))
    con.commit()
    con.close()


def balance(user_id):
    ensure_user(user_id)
    con = db()
    row = con.execute("SELECT balance FROM users WHERE user_id=?", (user_id,)).fetchone()
    con.close()
    return int(row[0]) if row else 0


def new_order(user_id, item, amount):
    con = db()
    cur = con.execute(
        "INSERT INTO orders(user_id,item,amount,status) VALUES(?,?,?,'pending')",
        (user_id, item, amount),
    )
    con.commit()
    oid = cur.lastrowid
    con.close()
    return oid


def menu():
    # Telegramdagi pastki doimiy menyu.
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton("⭐ Yulduzlar"), KeyboardButton("🎁 Sovg'alar")],
            [KeyboardButton("💎 Premium"), KeyboardButton("💰 Balansim")],
            [KeyboardButton("➕ Hisob to'ldirish"), KeyboardButton("📦 Buyurtmalar")],
            [KeyboardButton("👤 Profilim"), KeyboardButton("🔵 Yordam")],
            [KeyboardButton("ℹ️ Ma'lumot")],
        ],
        resize_keyboard=True,
        is_persistent=True,
        input_field_placeholder="Bo'limni tanlang...",
    )


def home_buttons():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⭐ Yulduzlar", callback_data="stars"),
         InlineKeyboardButton("🎁 Sovg'alar", callback_data="gifts")],
        [InlineKeyboardButton("💎 Premium", callback_data="premium"),
         InlineKeyboardButton("💰 Balansim", callback_data="balance")],
        [InlineKeyboardButton("➕ Hisob", callback_data="topup"),
         InlineKeyboardButton("📦 Buyurtmalar", callback_data="orders")],
        [InlineKeyboardButton("👤 Profil", callback_data="profile"),
         InlineKeyboardButton("🔵 Yordam", callback_data="help")],
        [InlineKeyboardButton("ℹ️ Ma'lumot", callback_data="info")],
    ])


def back():
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("↩️ Bosh sahifa", callback_data="home")]]
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ensure_user(update.effective_user.id)
    caption = (
        "🌌 STARGIFT SHOP\n\n"
        "⭐ Stars • 🎁 Sovg'alar • 💎 Premium\n\n"
        "⚡ Tezkor xizmat  •  🔐 Ishonchli  •  💳 So'm\n\n"
        "Quyidagi menyudan kerakli bo'limni tanlang."
    )
    if update.message is None:
        return
    if os.path.isfile(START_IMAGE):
        with open(START_IMAGE, "rb") as f:
            await update.message.reply_photo(
                photo=f, caption=caption, reply_markup=menu()
            )
    else:
        await update.message.reply_text(caption, reply_markup=menu())


async def stars_page(message):
    prices = [25, 50, 100, 125, 150, 175, 200, 300, 400, 500]
    rows = []
    for i in range(0, len(prices), 2):
        row = []
        for n in prices[i:i + 2]:
            row.append(InlineKeyboardButton(
                f"⭐ {n} • {n * STAR_PRICE:,} so'm".replace(",", " "),
                callback_data=f"star:{n}"
            ))
        rows.append(row)
    rows.append([InlineKeyboardButton("⌂ Bosh sahifa", callback_data="home")])
    await message.edit_text(
        "⭐ YULDUZLAR\n\nKerakli paketni tanlang:",
        reply_markup=InlineKeyboardMarkup(rows),
    )


async def premium_page(message):
    rows = []
    for i in range(0, len(PREMIUM), 2):
        row = []
        for index in range(i, min(i + 2, len(PREMIUM))):
            name, price = PREMIUM[index]
            row.append(InlineKeyboardButton(
                f"💎 {name} • {price:,}".replace(",", " "),
                callback_data=f"prem:{index}"
            ))
        rows.append(row)
    rows.append([InlineKeyboardButton("⌂ Bosh sahifa", callback_data="home")])
    await message.edit_text(
        "💎 PREMIUM\n\nMuddatni tanlang:",
        reply_markup=InlineKeyboardMarkup(rows),
    )


async def topup_page(message):
    rows = []
    for i in range(0, len(TOPUPS), 2):
        rows.append([
            InlineKeyboardButton(
                f"💳 {a:,} so'm".replace(",", " "),
                callback_data=f"top:{a}"
            )
            for a in TOPUPS[i:i + 2]
        ])
    rows.append([InlineKeyboardButton("⌂ Bosh sahifa", callback_data="home")])
    await message.edit_text(
        "➕ HISOB TO'LDIRISH\n\nSummani tanlang:",
        reply_markup=InlineKeyboardMarkup(rows),
    )


async def orders_page(message):
    con = db()
    rows = con.execute(
        "SELECT id,item,amount,status FROM orders "
        "WHERE user_id=? ORDER BY id DESC LIMIT 20",
        (message.chat_id,),
    ).fetchall()
    con.close()

    if not rows:
        text = (
            "📦 BUYURTMALARIM\n\n"
            "Hozircha buyurtma yo'q. 😊\n\n"
            "Buyurtma berganingizdan keyin shu yerda chiqadi."
        )
    else:
        parts = ["📦 BUYURTMALARIM\n"]
        for oid, item, amount, status in rows:
            parts.append(
                f"№{oid} • {item}\n"
                f"💳 {amount:,} so'm • 📌 {status}\n".replace(",", " ")
            )
        text = "\n".join(parts)

    await message.edit_text(text, reply_markup=back())


async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data or ""

    if data == "home":
        await q.edit_message_text(
            "🌌 STARGIFT SHOP\n\nKerakli bo'limni tanlang:",
            reply_markup=home_buttons(),
        )
    elif data == "stars":
        await stars_page(q.message)
    elif data == "premium":
        await premium_page(q.message)
    elif data == "topup":
        await topup_page(q.message)
    elif data == "balance":
        await q.edit_message_text(
            f"💰 BALANSIM\n\nJoriy balans: "
            f"{balance(q.from_user.id):,} so'm".replace(",", " "),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ Hisob to'ldirish", callback_data="topup")],
                [InlineKeyboardButton("⌂ Bosh sahifa", callback_data="home")],
            ]),
        )
    elif data == "profile":
        u = q.from_user
        name = f"@{u.username}" if u.username else "username yo'q"
        await q.edit_message_text(
            "👤 PROFILIM\n\n"
            f"ID: {u.id}\n"
            f"Username: {name}\n"
            f"Balans: {balance(u.id):,} so'm".replace(",", " "),
            reply_markup=back(),
        )
    elif data == "help":
        await q.edit_message_text(
            f"🔵 YORDAM\n\nOperator: {ADMIN}\n"
            "⏱ O'rtacha javob vaqti: 30 soniya.",
            reply_markup=back(),
        )
    elif data == "info":
        await q.edit_message_text(
            "ℹ️ STARGIFT SHOP\n\n"
            "⭐ Stars\n🎁 Telegram sovg'alari\n💎 Premium\n\n"
            "⚡ Qulay • 🔐 Ishonchli • 💳 So'mda",
            reply_markup=back(),
        )
    elif data == "orders":
        await orders_page(q.message)
    elif data == "gifts":
        await gifts_page(q.message, context)
    elif data.startswith("star:"):
        n = int(data.split(":")[1])
        amount = n * STAR_PRICE
        oid = new_order(q.from_user.id, f"{n} Stars", amount)
        await q.edit_message_text(
            f"⭐ BUYURTMA QABUL QILINDI\n\n"
            f"📦 №{oid}\n⭐ {n} Stars\n"
            f"💳 {amount:,} so'm\n📌 Holat: pending".replace(",", " "),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⭐ Yana tanlash", callback_data="stars")],
                [InlineKeyboardButton("⌂ Bosh sahifa", callback_data="home")],
            ]),
        )
    elif data.startswith("prem:"):
        index = int(data.split(":")[1])
        name, amount = PREMIUM[index]
        oid = new_order(q.from_user.id, f"Premium {name}", amount)
        await q.edit_message_text(
            f"💎 BUYURTMA QABUL QILINDI\n\n"
            f"📦 №{oid}\n💎 Premium {name}\n"
            f"💳 {amount:,} so'm\n📌 Holat: pending".replace(",", " "),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("💎 Yana tanlash", callback_data="premium")],
                [InlineKeyboardButton("⌂ Bosh sahifa", callback_data="home")],
            ]),
        )
    elif data.startswith("top:"):
        amount = int(data.split(":")[1])
        oid = new_order(q.from_user.id, "Hisob to'ldirish", amount)
        await q.edit_message_text(
            f"➕ HISOB TO'LDIRISH\n\n"
            f"📦 №{oid}\n💳 {amount:,} so'm\n"
            "📌 Holat: pending".replace(",", " "),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ Yana to'ldirish", callback_data="topup")],
                [InlineKeyboardButton("⌂ Bosh sahifa", callback_data="home")],
            ]),
        )


async def gifts_page(message, context):
    try:
        result = await context.bot.get_available_gifts()
        gifts = list(result.gifts)
    except Exception as e:
        print("GIFT ERROR:", repr(e))
        await message.edit_text(
            "🎁 SOVG'ALAR\n\n"
            "Hozircha sovg'alar ro'yxatini olishning iloji bo'lmadi.",
            reply_markup=back(),
        )
        return

    if not gifts:
        await message.edit_text(
            "🎁 SOVG'ALAR\n\nHozircha mavjud sovg'a yo'q.",
            reply_markup=back(),
        )
        return

    rows = []
    for i in range(0, min(len(gifts), 30), 2):
        row = []
        for gift in gifts[i:i + 2]:
            row.append(InlineKeyboardButton(
                f"🎁 {gift.star_count}⭐ • {gift.star_count * STAR_PRICE:,}".replace(",", " "),
                callback_data=f"gift:{gift.id}",
            ))
        rows.append(row)
    rows.append([InlineKeyboardButton("⌂ Bosh sahifa", callback_data="home")])
    await message.edit_text(
        "🎁 SOVG'ALAR\n\nO'zingizga yoqqan sovg'ani tanlang:",
        reply_markup=InlineKeyboardMarkup(rows),
    )


async def gift_selected(update, context, gift_id):
    q = update.callback_query
    try:
        result = await context.bot.get_available_gifts()
        gift = next((g for g in result.gifts if str(g.id) == str(gift_id)), None)
        if gift is None:
            raise ValueError("Gift topilmadi")

        price = gift.star_count * STAR_PRICE
        oid = new_order(q.from_user.id, f"Sovg'a {gift.star_count} Stars", price)

        # Telegram gift stickeri.
        await q.message.reply_sticker(sticker=gift.sticker.file_id)
        await q.message.reply_text(
            f"🎁 TANLANGAN SOVG'A\n\n"
            f"⭐ {gift.star_count} Stars\n"
            f"💳 {price:,} so'm\n"
            f"📦 №{oid}\n📌 Holat: pending".replace(",", " "),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🎁 Yana tanlash", callback_data="gifts")],
                [InlineKeyboardButton("⌂ Bosh sahifa", callback_data="home")],
            ]),
        )
    except Exception as e:
        print("GIFT SELECT ERROR:", repr(e))
        await q.message.reply_text(
            "❌ Sovg'ani ko'rsatishda xatolik yuz berdi.",
            reply_markup=back(),
        )


# Gift callbackni umumiy callbackdan oldin alohida handler qilamiz.
async def gift_callback(update, context):
    q = update.callback_query
    await q.answer()
    await gift_selected(update, context, q.data.split(":", 1)[1])


async def text_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    t = (update.message.text or "").strip()
    uid = update.effective_user.id
    ensure_user(uid)

    if t == "⭐ Yulduzlar":
        await update.message.reply_text(
            "⭐ YULDUZLAR\n\nPaketni tanlang:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⭐ 25", callback_data="star:25"),
                 InlineKeyboardButton("⭐ 50", callback_data="star:50")],
                [InlineKeyboardButton("⭐ 100", callback_data="star:100"),
                 InlineKeyboardButton("⭐ 200", callback_data="star:200")],
                [InlineKeyboardButton("⭐ 500", callback_data="star:500")],
            ]),
        )
    elif t == "🎁 Sovg'alar":
        await update.message.reply_text(
            "🎁 SOVG'ALAR\n\nRo'yxatni oching:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🎁 Sovg'alarni ochish", callback_data="gifts")]
            ]),
        )
    elif t == "💎 Premium":
        await update.message.reply_text(
            "💎 PREMIUM\n\nMuddatni tanlang:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("1 oy • 45 000", callback_data="prem:0"),
                 InlineKeyboardButton("3 oy • 164 000", callback_data="prem:1")],
                [InlineKeyboardButton("6 oy • 222 000", callback_data="prem:2"),
                 InlineKeyboardButton("12 oy • 377 000", callback_data="prem:3")],
            ]),
        )
    elif t == "💰 Balansim":
        await update.message.reply_text(
            f"💰 BALANSIM\n\n{balance(uid):,} so'm".replace(",", " "),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ Hisob to'ldirish", callback_data="topup")]
            ]),
        )
    elif t == "➕ Hisob to'ldirish":
        await update.message.reply_text(
            "➕ HISOB TO'LDIRISH\n\nSummani tanlang:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("10 000", callback_data="top:10000"),
                 InlineKeyboardButton("20 000", callback_data="top:20000")],
                [InlineKeyboardButton("50 000", callback_data="top:50000"),
                 InlineKeyboardButton("100 000", callback_data="top:100000")],
                [InlineKeyboardButton("200 000", callback_data="top:200000"),
                 InlineKeyboardButton("500 000", callback_data="top:500000")],
            ]),
        )
    elif t == "📦 Buyurtmalar":
        con = db()
        rows = con.execute(
            "SELECT id,item,amount,status FROM orders WHERE user_id=? "
            "ORDER BY id DESC LIMIT 20", (uid,)
        ).fetchall()
        con.close()
        if not rows:
            await update.message.reply_text(
                "📦 BUYURTMALARIM\n\nHozircha buyurtma yo'q. 😊"
            )
        else:
            text = "📦 BUYURTMALARIM\n\n"
            for oid, item, amount, status in rows:
                text += f"№{oid} • {item}\n💳 {amount:,} so'm • 📌 {status}\n\n".replace(",", " ")
            await update.message.reply_text(text)
    elif t == "👤 Profilim":
        u = update.effective_user
        username = f"@{u.username}" if u.username else "username yo'q"
        await update.message.reply_text(
            f"👤 PROFILIM\n\nID: {u.id}\nUsername: {username}\n"
            f"Balans: {balance(uid):,} so'm".replace(",", " ")
        )
    elif t == "🔵 Yordam":
        await update.message.reply_text(
            f"🔵 YORDAM\n\nOperator: {ADMIN}\n⏱ Javob vaqti: 30 soniya"
        )
    elif t == "ℹ️ Ma'lumot":
        await update.message.reply_text(
            "ℹ️ STARGIFT SHOP\n\n"
            "⭐ Stars • 🎁 Sovg'alar • 💎 Premium\n"
            "⚡ Tezkor • 🔐 Ishonchli • 💳 So'mda"
        )
    else:
        await update.message.reply_text(
            "🌌 STARGIFT SHOP\n\nMenyudan kerakli bo'limni tanlang.",
            reply_markup=menu(),
        )


async def set_commands(app):
    await app.bot.set_my_commands([
        BotCommand("start", "Bosh sahifa"),
        BotCommand("services", "Bo'limlar"),
        BotCommand("balance", "Balans"),
        BotCommand("orders", "Buyurtmalar"),
        BotCommand("help", "Yordam"),
    ])


async def services(update, context):
    await update.message.reply_text(
        "🧩 BO'LIMLAR\n\nKerakli bo'limni pastdagi menyudan tanlang.",
        reply_markup=menu(),
    )


async def balance_command(update, context):
    await update.message.reply_text(
        f"💰 BALANSIM\n\n{balance(update.effective_user.id):,} so'm".replace(",", " "),
        reply_markup=menu(),
    )


async def orders_command(update, context):
    await text_menu(update, context)


async def help_command(update, context):
    await update.message.reply_text(
        f"🔵 YORDAM\n\nOperator: {ADMIN}\n⏱ Javob vaqti: 30 soniya",
        reply_markup=menu(),
    )


async def error_handler(update, context):
    print("STARGIFT ERROR:", repr(context.error))


def main():
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN topilmadi. Railway Variables ga BOT_TOKEN qo'ying.")

    db()
    app = Application.builder().token(TOKEN).post_init(set_commands).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("services", services))
    app.add_handler(CommandHandler("balance", balance_command))
    app.add_handler(CommandHandler("orders", orders_command))
    app.add_handler(CommandHandler("help", help_command))

    app.add_handler(CallbackQueryHandler(gift_callback, pattern=r"^gift:"))
    app.add_handler(CallbackQueryHandler(callback))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_menu))
    app.add_error_handler(error_handler)

    print("STARGIFT SHOP IS RUNNING")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
    
