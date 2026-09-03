import os
import sqlite3
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardRemove,
    BotCommand,
    MenuButtonCommands,
)
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

TOPUPS = [10000, 20000, 50000, 100000, 200000, 500000]

DB_FILE = "stargift_final.db"
START_IMAGE = "stargift_start.png"


def money(amount):
    return f"{int(amount):,}".replace(",", " ")


def db():
    con = sqlite3.connect(DB_FILE)
    con.execute(
        "CREATE TABLE IF NOT EXISTS users "
        "(user_id INTEGER PRIMARY KEY, balance INTEGER NOT NULL DEFAULT 0)"
    )
    con.execute(
        "CREATE TABLE IF NOT EXISTS orders "
        "(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, "
        "item TEXT NOT NULL, amount INTEGER NOT NULL, "
        "status TEXT NOT NULL DEFAULT 'pending')"
    )
    con.commit()
    return con


def ensure_user(user_id):
    con = db()
    con.execute(
        "INSERT OR IGNORE INTO users(user_id,balance) VALUES(?,0)",
        (user_id,),
    )
    con.commit()
    con.close()


def balance(user_id):
    ensure_user(user_id)
    con = db()
    row = con.execute(
        "SELECT balance FROM users WHERE user_id=?",
        (user_id,),
    ).fetchone()
    con.close()
    return row[0] if row else 0


def order(user_id, item, amount):
    con = db()
    cur = con.execute(
        "INSERT INTO orders(user_id,item,amount,status) VALUES(?,?,?,'pending')",
        (user_id, item, amount),
    )
    con.commit()
    n = cur.lastrowid
    con.close()
    return n


def home_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("⭐ Yulduzlar", callback_data="stars"),
            InlineKeyboardButton("🎁 Sovg'alar", callback_data="gifts"),
        ],
        [
            InlineKeyboardButton("💎 Premium", callback_data="premium"),
            InlineKeyboardButton("💰 Balansim", callback_data="balance"),
        ],
        [
            InlineKeyboardButton("➕ Hisob to'ldirish", callback_data="topup"),
            InlineKeyboardButton("👤 Profilim", callback_data="profile"),
        ],
        [
            InlineKeyboardButton("🔵 Yordam", callback_data="help"),
            InlineKeyboardButton("ℹ️ Ma'lumot", callback_data="info"),
        ],
    ])


def back_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("‹ Bosh sahifa", callback_data="home")]
    ])


async def replace_message(message, text, markup=None):
    """Works for both normal text messages and the photo sent by /start."""
    try:
        await message.edit_text(text, reply_markup=markup)
        return
    except Exception:
        pass

    try:
        await message.edit_caption(caption=text, reply_markup=markup)
        return
    except Exception:
        pass

    await message.reply_text(text, reply_markup=markup)


async def setup(app):
    await app.bot.set_my_commands([
        BotCommand("start", "Bosh sahifa"),
        BotCommand("services", "Bo'limlar"),
        BotCommand("balance", "Balansim"),
        BotCommand("orders", "Buyurtmalarim"),
        BotCommand("help", "Yordam"),
    ])
    await app.bot.set_chat_menu_button(menu_button=MenuButtonCommands())


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    ensure_user(user.id)

    text = (
        "✦ STARGIFT SHOP ✦\n\n"
        "Xush kelibsiz! 🌟\n"
        "⭐ Yulduzlar  •  🎁 Sovg'alar  •  💎 Premium\n\n"
        "⚡ Tezkor  •  🔐 Ishonchli  •  💳 So'mda\n"
        "⏱ O'rtacha bajarilish: 30 soniya\n\n"
        "Kerakli bo'limni tanlang:"
    )

    # Eski Reply Keyboard bo'lsa, shu bilan olib tashlanadi.
    remove = ReplyKeyboardRemove()

    if update.message:
        if os.path.isfile(START_IMAGE):
            with open(START_IMAGE, "rb") as photo:
                await update.message.reply_photo(
                    photo=photo,
                    caption=text,
                    reply_markup=home_keyboard(),
                )
        else:
            await update.message.reply_text(
                text,
                reply_markup=home_keyboard(),
            )
        # Telegram eski Reply Keyboardni keyingi xabarda olib tashlaydi.
        await update.message.reply_text(
            " ",
            reply_markup=remove,
        )


async def services(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✦ STARGIFT SHOP ✦\n\nKerakli bo'limni tanlang:",
        reply_markup=home_keyboard(),
    )
    await update.message.reply_text(" ", reply_markup=ReplyKeyboardRemove())


async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"💰 BALANSIM\n\nBalans: {money(balance(update.effective_user.id))} so'm",
        reply_markup=back_keyboard(),
    )


async def orders_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_orders(update.message, update.effective_user.id)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"🔵 YORDAM\n\nAdministrator: {ADMIN}\n\n"
        "Savol yoki muammo bo'lsa yozing.\n"
        "⏱ O'rtacha javob: 30 soniya.",
        reply_markup=back_keyboard(),
    )


async def show_orders(message, user_id):
    con = db()
    rows = con.execute(
        "SELECT id,item,amount,status FROM orders "
        "WHERE user_id=? ORDER BY id DESC LIMIT 30",
        (user_id,),
    ).fetchall()
    con.close()

    if not rows:
        text = (
            "📦 BUYURTMALARIM\n\n"
            "Hozircha buyurtma bermagansiz. 😊\n\n"
            "Buyurtma berganingizdan keyin shu yerda ko'rinadi."
        )
    else:
        text = "📦 BUYURTMALARIM\n\n"
        for oid, item, amount, status in rows:
            st = {
                "pending": "⏳ Kutilmoqda",
                "paid": "✅ To'langan",
                "completed": "🎉 Bajarildi",
                "cancelled": "❌ Bekor qilingan",
            }.get(status, status)
            text += (
                f"№ {oid}\n"
                f"• {item}\n"
                f"• {money(amount)} so'm\n"
                f"• {st}\n\n"
            )

    await replace_message(message, text, back_keyboard())


async def stars_page(message):
    packages = [25, 50, 100, 125, 150, 175, 200, 300, 400, 500]
    rows = []
    for i in range(0, len(packages), 2):
        row = []
        for count in packages[i:i + 2]:
            row.append(InlineKeyboardButton(
                f"⭐ {count} • {money(count * STAR_PRICE)} so'm",
                callback_data=f"star:{count}",
            ))
        rows.append(row)
    rows.append([InlineKeyboardButton("‹ Bosh sahifa", callback_data="home")])
    await replace_message(
        message,
        "⭐ YULDUZLAR\n\n1 ⭐ = 195 so'm\nPaketni tanlang:",
        InlineKeyboardMarkup(rows),
    )


async def premium_page(message):
    rows = []
    for i in range(0, len(PREMIUM), 2):
        row = []
        for index in range(i, min(i + 2, len(PREMIUM))):
            name, price = PREMIUM[index]
            row.append(InlineKeyboardButton(
                f"💎 {name} • {money(price)} so'm",
                callback_data=f"prem:{index}",
            ))
        rows.append(row)
    rows.append([InlineKeyboardButton("‹ Bosh sahifa", callback_data="home")])
    await replace_message(
        message,
        "💎 PREMIUM\n\nMuddatni tanlang:",
        InlineKeyboardMarkup(rows),
    )


async def topup_page(message):
    rows = []
    for i in range(0, len(TOPUPS), 2):
        row = []
        for amount in TOPUPS[i:i + 2]:
            row.append(InlineKeyboardButton(
                f"💳 {money(amount)} so'm",
                callback_data=f"top:{amount}",
            ))
        rows.append(row)
    rows.append([InlineKeyboardButton("‹ Bosh sahifa", callback_data="home")])
    await replace_message(
        message,
        "➕ HISOB TO'LDIRISH\n\nSummani tanlang.\nTo'lovlar so'mda:",
        InlineKeyboardMarkup(rows),
    )


async def gifts_page(message, context):
    try:
        result = await context.bot.get_available_gifts()
        gifts = list(result.gifts)
    except Exception as e:
        print("GIFTS ERROR:", repr(e))
        await replace_message(
            message,
            "🎁 SOVG'ALAR\n\nSovg'alarni olishda xatolik yuz berdi.",
            back_keyboard(),
        )
        return

    if not gifts:
        await replace_message(
            message,
            "🎁 SOVG'ALAR\n\nHozircha mavjud sovg'a yo'q.",
            back_keyboard(),
        )
        return

    rows = []
    for i in range(0, min(40, len(gifts)), 2):
        row = []
        for gift in gifts[i:i + 2]:
            emoji = getattr(gift.sticker, "emoji", None) or "🎁"
            price = gift.star_count * STAR_PRICE
            row.append(InlineKeyboardButton(
                f"{emoji} {gift.star_count}⭐ • {money(price)} so'm",
                callback_data=f"gift:{gift.id}",
            ))
        rows.append(row)

    rows.append([InlineKeyboardButton("‹ Bosh sahifa", callback_data="home")])

    await replace_message(
        message,
        "🎁 SOVG'ALAR\n\n"
        "Quyidagi sovg'alardan birini tanlang.\n"
        "Tanlaganda haqiqiy Telegram gift rasmi chiqadi:",
        InlineKeyboardMarkup(rows),
    )


async def profile_page(message, user):
    username = f"@{user.username}" if user.username else "username yo'q"
    await replace_message(
        message,
        "👤 PROFILIM\n\n"
        f"Username: {username}\n"
        f"ID: {user.id}\n"
        f"💰 Balans: {money(balance(user.id))} so'm",
        back_keyboard(),
    )


async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
    except Exception:
        pass

    data = query.data or ""
    user = query.from_user
    ensure_user(user.id)

    try:
        if data == "home":
            await replace_message(
                query.message,
                "✦ STARGIFT SHOP ✦\n\n"
                "⭐ Yulduzlar • 🎁 Sovg'alar • 💎 Premium\n\n"
                "Kerakli bo'limni tanlang:",
                home_keyboard(),
            )

        elif data == "stars":
            await stars_page(query.message)

        elif data == "gifts":
            await gifts_page(query.message, context)

        elif data == "premium":
            await premium_page(query.message)

        elif data == "balance":
            await replace_message(
                query.message,
                f"💰 BALANSIM\n\nBalans: {money(balance(user.id))} so'm",
                back_keyboard(),
            )

        elif data == "topup":
            await topup_page(query.message)

        elif data == "orders":
            await show_orders(query.message, user.id)

        elif data == "profile":
            await profile_page(query.message, user)

        elif data == "help":
            await replace_message(
                query.message,
                f"🔵 YORDAM\n\nAdministrator: {ADMIN}\n\n"
                "Savol yoki muammo bo'lsa yozing.",
                back_keyboard(),
            )

        elif data == "info":
            await replace_message(
                query.message,
                "ℹ️ MA'LUMOT\n\n"
                "✦ STARGIFT SHOP\n"
                "⭐ Yulduzlar\n"
                "🎁 Telegram Sovg'alar\n"
                "💎 Premium\n\n"
                "💳 Narxlar so'mda\n"
                "⏱ O'rtacha bajarilish: 30 soniya",
                back_keyboard(),
            )

        elif data.startswith("star:"):
            count = int(data.split(":", 1)[1])
            amount = count * STAR_PRICE
            oid = order(user.id, f"{count} Stars", amount)
            await replace_message(
                query.message,
                "⭐ BUYURTMA\n\n"
                f"{count} ⭐\n"
                f"Narx: {money(amount)} so'm\n"
                f"№ {oid}\n"
                "⏳ Kutilmoqda",
                InlineKeyboardMarkup([
                    [InlineKeyboardButton("📦 Buyurtmam", callback_data="orders")],
                    [InlineKeyboardButton("‹ Bosh sahifa", callback_data="home")],
                ]),
            )

        elif data.startswith("prem:"):
            index = int(data.split(":", 1)[1])
            if index < 0 or index >= len(PREMIUM):
                raise ValueError("Premium index")
            name, amount = PREMIUM[index]
            oid = order(user.id, f"Premium {name}", amount)
            await replace_message(
                query.message,
                "💎 PREMIUM BUYURTMA\n\n"
                f"Muddat: {name}\n"
                f"Narx: {money(amount)} so'm\n"
                f"№ {oid}\n"
                "⏳ Kutilmoqda",
                InlineKeyboardMarkup([
                    [InlineKeyboardButton("📦 Buyurtmam", callback_data="orders")],
                    [InlineKeyboardButton("‹ Bosh sahifa", callback_data="home")],
                ]),
            )

        elif data.startswith("top:"):
            amount = int(data.split(":", 1)[1])
            if amount not in TOPUPS:
                raise ValueError("Topup amount")
            oid = order(user.id, "Hisob to'ldirish", amount)
            await replace_message(
                query.message,
                "➕ HISOB TO'LDIRISH\n\n"
                f"Summa: {money(amount)} so'm\n"
                f"№ {oid}\n"
                "⏳ Kutilmoqda",
                InlineKeyboardMarkup([
                    [InlineKeyboardButton("📦 Buyurtmam", callback_data="orders")],
                    [InlineKeyboardButton("‹ Bosh sahifa", callback_data="home")],
                ]),
            )

        elif data.startswith("gift:"):
            gift_id = data.split(":", 1)[1]
            result = await context.bot.get_available_gifts()
            gift = next(
                (g for g in result.gifts if str(g.id) == gift_id),
                None,
            )
            if gift is None:
                raise ValueError("Gift topilmadi")

            amount = gift.star_count * STAR_PRICE
            oid = order(
                user.id,
                f"Telegram Gift ({gift.star_count} Stars)",
                amount,
            )

            # Haqiqiy gift sticker/rasmi.
            try:
                await query.message.reply_sticker(gift.sticker.file_id)
            except Exception as e:
                print("GIFT STICKER ERROR:", repr(e))

            await query.message.reply_text(
                "🎁 TANLANGAN SOVG'A\n\n"
                f"⭐ Qiymati: {gift.star_count} Stars\n"
                f"💳 Narxi: {money(amount)} so'm\n"
                f"📦 Buyurtma: №{oid}\n"
                "⏳ Holat: Kutilmoqda",
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("🎁 Yana sovg'a", callback_data="gifts"),
                        InlineKeyboardButton("📦 Buyurtmam", callback_data="orders"),
                    ],
                    [InlineKeyboardButton("‹ Bosh sahifa", callback_data="home")],
                ]),
            )

    except Exception as e:
        print("CALLBACK ERROR:", repr(e))
        try:
            await query.message.reply_text(
                "⚠️ Xatolik yuz berdi. Qaytadan urinib ko'ring.",
                reply_markup=back_keyboard(),
            )
        except Exception:
            pass


def main():
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN Railway Variables ichida yo'q.")

    app = (
        Application.builder()
        .token(TOKEN)
        .post_init(setup)
        .build()
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("services", services))
    app.add_handler(CommandHandler("balance", balance_command))
    app.add_handler(CommandHandler("orders", orders_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CallbackQueryHandler(callback))

    print("STARGIFT SHOP FINAL BOT RUNNING")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
        
