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
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

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

DB_FILE = "stargift_modern.db"
START_IMAGE = "stargift_start.png"


def money(n):
    return f"{int(n):,}".replace(",", " ")


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


def ensure_user(uid):
    con = db()
    con.execute("INSERT OR IGNORE INTO users(user_id,balance) VALUES(?,0)", (uid,))
    con.commit()
    con.close()


def get_balance(uid):
    ensure_user(uid)
    con = db()
    row = con.execute("SELECT balance FROM users WHERE user_id=?", (uid,)).fetchone()
    con.close()
    return row[0] if row else 0


def has_orders(uid):
    con = db()
    row = con.execute("SELECT 1 FROM orders WHERE user_id=? LIMIT 1", (uid,)).fetchone()
    con.close()
    return row is not None


def create_order(uid, item, amount):
    con = db()
    cur = con.execute(
        "INSERT INTO orders(user_id,item,amount,status) VALUES(?,?,?,'pending')",
        (uid, item, amount),
    )
    con.commit()
    oid = cur.lastrowid
    con.close()
    return oid


def home_keyboard(uid):
    rows = [
        [
            InlineKeyboardButton("🌟 Yulduzlar", callback_data="stars"),
            InlineKeyboardButton("🎁 Sovg'alar", callback_data="gifts"),
        ],
        [
            InlineKeyboardButton("💎 Premium", callback_data="premium"),
            InlineKeyboardButton("💳 Hisob", callback_data="topup"),
        ],
        [
            InlineKeyboardButton("👤 Profil", callback_data="profile"),
            InlineKeyboardButton("💰 Balans", callback_data="balance"),
        ],
        [
            InlineKeyboardButton("🛟 Yordam", callback_data="help"),
            InlineKeyboardButton("✦ Biz haqimizda", callback_data="info"),
        ],
    ]
    # Buyurtmalar tugmasi faqat kamida bitta buyurtma bo'lsa chiqadi.
    if has_orders(uid):
        rows.insert(3, [
            InlineKeyboardButton("📦 Buyurtmalarim", callback_data="orders")
        ])
    return InlineKeyboardMarkup(rows)


def back(uid):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⌂ Bosh sahifa", callback_data="home")]
    ])


async def setup(app):
    # Telegramning doimiy menyu belgisi: faqat komandalar.
    await app.bot.set_my_commands([
        BotCommand("start", "Bosh sahifa"),
        BotCommand("services", "Xizmatlar"),
        BotCommand("balance", "Balans"),
        BotCommand("orders", "Buyurtmalarim"),
        BotCommand("help", "Yordam"),
    ])
    await app.bot.set_chat_menu_button(menu_button=MenuButtonCommands())


async def remove_old_keyboard(update):
    # Avvalgi ReplyKeyboard bo'lsa olib tashlaydi.
    if update.message:
        try:
            m = await update.message.reply_text("\u2063", reply_markup=ReplyKeyboardRemove())
            try:
                await m.delete()
            except Exception:
                pass
        except Exception:
            pass


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    ensure_user(uid)
    await remove_old_keyboard(update)

    text = (
        "✦  S T A R G I F T  S H O P  ✦\n\n"
        "Assalomu alaykum! 👋\n"
        "Raqamli sovg'alar va Premium xizmatlari bir joyda.\n\n"
        "🌟 Yulduzlar   •   🎁 Sovg'alar   •   💎 Premium\n"
        "⚡ Tezkor xizmat   •   🔐 Ishonchli   •   💳 So'mda\n"
        "⏱ O'rtacha bajarilish: 30 soniya\n\n"
        "Quyidan kerakli bo'limni tanlang:"
    )
    markup = home_keyboard(uid)

    if update.message:
        if os.path.isfile(START_IMAGE):
            try:
                with open(START_IMAGE, "rb") as photo:
                    await update.message.reply_photo(
                        photo=photo, caption=text, reply_markup=markup
                    )
                    return
            except Exception as e:
                print("START IMAGE ERROR:", repr(e))
        await update.message.reply_text(text, reply_markup=markup)


async def services(update, context):
    await start(update, context)


async def balance_command(update, context):
    uid = update.effective_user.id
    await update.message.reply_text(
        f"💰 BALANS\n\n"
        f"Joriy balans: {money(get_balance(uid))} so'm",
        reply_markup=back(uid),
    )


async def orders_command(update, context):
    await show_orders(update.message, update.effective_user.id)


async def help_command(update, context):
    uid = update.effective_user.id
    await update.message.reply_text(
        f"🛟 YORDAM\n\n"
        f"Administrator: {ADMIN}\n\n"
        "Savol yoki muammo bo'lsa yozing.\n"
        "⏱ O'rtacha javob: 30 soniya.",
        reply_markup=back(uid),
    )


async def safe_edit(message, text, markup):
    # Photo xabarini edit_text qila olmaydi; captionga o'tadi.
    try:
        if message.photo:
            await message.edit_caption(caption=text, reply_markup=markup)
        else:
            await message.edit_text(text, reply_markup=markup)
    except Exception as e:
        # Eski xabar o'zgartirib bo'lmasa, yangi xabar ochiladi.
        print("EDIT FALLBACK:", repr(e))
        await message.reply_text(text, reply_markup=markup)


async def show_orders(message, uid):
    con = db()
    rows = con.execute(
        "SELECT id,item,amount,status FROM orders "
        "WHERE user_id=? ORDER BY id DESC LIMIT 30",
        (uid,),
    ).fetchall()
    con.close()

    if not rows:
        text = (
            "📦 BUYURTMALARIM\n\n"
            "Hozircha buyurtma bermagansiz. 😊\n\n"
            "Buyurtma berganingizdan keyin bu bo'lim avtomatik paydo bo'ladi."
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
                f"№ {oid}  •  {st}\n"
                f"🛍 {item}\n"
                f"💳 {money(amount)} so'm\n\n"
            )

    await safe_edit(message, text, back(uid))


async def stars_page(message, uid):
    packs = [25, 50, 100, 125, 150, 175, 200, 300, 400, 500]
    rows = []
    for i in range(0, len(packs), 2):
        rows.append([
            InlineKeyboardButton(
                f"🌟 {n}  •  {money(n * STAR_PRICE)} so'm",
                callback_data=f"star:{n}",
            )
            for n in packs[i:i + 2]
        ])
    rows.append([InlineKeyboardButton("⌂ Bosh sahifa", callback_data="home")])
    await safe_edit(
        message,
        "🌟 YULDUZLAR\n\n"
        "1 🌟 = 195 so'm\n\n"
        "Paketni tanlang:",
        InlineKeyboardMarkup(rows),
    )


async def premium_page(message, uid):
    rows = []
    for i in range(0, len(PREMIUM), 2):
        rows.append([
            InlineKeyboardButton(
                f"💎 {name}  •  {money(price)} so'm",
                callback_data=f"prem:{i+j}",
            )
            for j, (name, price) in enumerate(PREMIUM[i:i + 2])
        ])
    rows.append([InlineKeyboardButton("⌂ Bosh sahifa", callback_data="home")])
    await safe_edit(
        message,
        "💎 PREMIUM\n\n"
        "Kerakli muddatni tanlang:",
        InlineKeyboardMarkup(rows),
    )


async def topup_page(message, uid):
    rows = []
    for i in range(0, len(TOPUPS), 2):
        rows.append([
            InlineKeyboardButton(
                f"💳 {money(n)} so'm",
                callback_data=f"top:{n}",
            )
            for n in TOPUPS[i:i + 2]
        ])
    rows.append([InlineKeyboardButton("⌂ Bosh sahifa", callback_data="home")])
    await safe_edit(
        message,
        "💳 HISOB TO'LDIRISH\n\n"
        "Kerakli summani tanlang.\n"
        "Barcha narxlar so'mda.",
        InlineKeyboardMarkup(rows),
    )


async def gifts_page(message, context, uid):
    try:
        result = await context.bot.get_available_gifts()
        gifts = list(result.gifts)
    except Exception as e:
        print("GIFTS ERROR:", repr(e))
        await safe_edit(
            message,
            "🎁 SOVG'ALAR\n\n"
            "Sovg'alar ro'yxatini olishda xatolik yuz berdi.",
            back(uid),
        )
        return

    if not gifts:
        await safe_edit(
            message,
            "🎁 SOVG'ALAR\n\nHozircha mavjud sovg'a yo'q.",
            back(uid),
        )
        return

    rows = []
    for i in range(0, min(len(gifts), 40), 2):
        row = []
        for gift in gifts[i:i + 2]:
            emoji = getattr(gift.sticker, "emoji", None) or "🎁"
            price = gift.star_count * STAR_PRICE
            row.append(InlineKeyboardButton(
                f"{emoji} {gift.star_count}🌟\n{money(price)} so'm",
                callback_data=f"gift:{gift.id}",
            ))
        rows.append(row)

    rows.append([InlineKeyboardButton("⌂ Bosh sahifa", callback_data="home")])

    await safe_edit(
        message,
        "🎁 SOVG'ALAR\n\n"
        "Har bir tanlovda haqiqiy Telegram sovg'a rasmi/stickeri ko'rsatiladi.\n\n"
        "Sovg'ani tanlang:",
        InlineKeyboardMarkup(rows),
    )


async def profile_page(message, user):
    uid = user.id
    username = f"@{user.username}" if user.username else "username yo'q"
    await safe_edit(
        message,
        "👤 PROFIL\n\n"
        f"Username: {username}\n"
        f"ID: {uid}\n"
        f"💰 Balans: {money(get_balance(uid))} so'm",
        back(uid),
    )


async def callback(update, context):
    q = update.callback_query
    try:
        await q.answer()
    except Exception:
        pass

    data = q.data or ""
    uid = q.from_user.id
    ensure_user(uid)

    try:
        if data == "home":
            await safe_edit(
                q.message,
                "✦  S T A R G I F T  S H O P  ✦\n\n"
                "Kerakli bo'limni tanlang:\n\n"
                "🌟 Yulduzlar  •  🎁 Sovg'alar  •  💎 Premium\n"
                "💳 To'lovlar so'mda.",
                home_keyboard(uid),
            )

        elif data == "stars":
            await stars_page(q.message, uid)

        elif data == "gifts":
            await gifts_page(q.message, context, uid)

        elif data == "premium":
            await premium_page(q.message, uid)

        elif data == "balance":
            await safe_edit(
                q.message,
                f"💰 BALANS\n\nJoriy balans: {money(get_balance(uid))} so'm",
                back(uid),
            )

        elif data == "topup":
            await topup_page(q.message, uid)

        elif data == "orders":
            await show_orders(q.message, uid)

        elif data == "profile":
            await profile_page(q.message, q.from_user)

        elif data == "help":
            await safe_edit(
                q.message,
                f"🛟 YORDAM\n\nAdministrator: {ADMIN}\n\n"
                "Savol yoki muammo bo'lsa yozing.",
                back(uid),
            )

        elif data == "info":
            await safe_edit(
                q.message,
                "✦ STARGIFT SHOP\n\n"
                "🌟 Yulduzlar\n"
                "🎁 Telegram Sovg'alar\n"
                "💎 Premium\n\n"
                "💳 Narxlar so'mda\n"
                "⏱ O'rtacha bajarilish: 30 soniya",
                back(uid),
            )

        elif data.startswith("star:"):
            n = int(data.split(":", 1)[1])
            if n not in [25, 50, 100, 125, 150, 175, 200, 300, 400, 500]:
                raise ValueError("Stars package")
            amount = n * STAR_PRICE
            oid = create_order(uid, f"{n} Stars", amount)
            await safe_edit(
                q.message,
                "🌟 BUYURTMA YARATILDI\n\n"
                f"🌟 {n} Stars\n"
                f"💳 {money(amount)} so'm\n"
                f"📦 № {oid}\n"
                "⏳ Holat: Kutilmoqda",
                InlineKeyboardMarkup([
                    [InlineKeyboardButton("📦 Buyurtmam", callback_data="orders")],
                    [InlineKeyboardButton("⌂ Bosh sahifa", callback_data="home")],
                ]),
            )

        elif data.startswith("prem:"):
            idx = int(data.split(":", 1)[1])
            if not 0 <= idx < len(PREMIUM):
                raise ValueError("Premium index")
            name, amount = PREMIUM[idx]
            oid = create_order(uid, f"Premium {name}", amount)
            await safe_edit(
                q.message,
                "💎 BUYURTMA YARATILDI\n\n"
                f"💎 Premium: {name}\n"
                f"💳 {money(amount)} so'm\n"
                f"📦 № {oid}\n"
                "⏳ Holat: Kutilmoqda",
                InlineKeyboardMarkup([
                    [InlineKeyboardButton("📦 Buyurtmam", callback_data="orders")],
                    [InlineKeyboardButton("⌂ Bosh sahifa", callback_data="home")],
                ]),
            )

        elif data.startswith("top:"):
            amount = int(data.split(":", 1)[1])
            if amount not in TOPUPS:
                raise ValueError("Topup")
            oid = create_order(uid, "Hisob to'ldirish", amount)
            await safe_edit(
                q.message,
                "💳 TO'LOV SO'ROVI\n\n"
                f"Summa: {money(amount)} so'm\n"
                f"📦 № {oid}\n"
                "⏳ Holat: Kutilmoqda",
                InlineKeyboardMarkup([
                    [InlineKeyboardButton("📦 Buyurtmam", callback_data="orders")],
                    [InlineKeyboardButton("⌂ Bosh sahifa", callback_data="home")],
                ]),
            )

        elif data.startswith("gift:"):
            gift_id = data.split(":", 1)[1]
            result = await context.bot.get_available_gifts()
            gift = next((g for g in result.gifts if str(g.id) == gift_id), None)
            if gift is None:
                raise ValueError("Gift not found")

            amount = gift.star_count * STAR_PRICE
            oid = create_order(
                uid,
                f"Telegram Gift ({gift.star_count} Stars)",
                amount,
            )

            # Haqiqiy Telegram gift rasmi/stickeri.
            try:
                await q.message.reply_sticker(gift.sticker.file_id)
            except Exception as e:
                print("GIFT IMAGE ERROR:", repr(e))

            await q.message.reply_text(
                "🎁 SOVG'A TANLANDI\n\n"
                f"🌟 Qiymati: {gift.star_count} Stars\n"
                f"💳 Narxi: {money(amount)} so'm\n"
                f"📦 № {oid}\n"
                "⏳ Holat: Kutilmoqda",
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("🎁 Boshqa sovg'a", callback_data="gifts"),
                        InlineKeyboardButton("📦 Buyurtmam", callback_data="orders"),
                    ],
                    [InlineKeyboardButton("⌂ Bosh sahifa", callback_data="home")],
                ]),
            )

    except Exception as e:
        print("CALLBACK ERROR:", repr(e))
        try:
            await q.message.reply_text(
                "⚠️ Bo'limni ochishda xatolik yuz berdi.",
                reply_markup=back(uid),
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

    print("STARGIFT MODERN BOT RUNNING")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
            
