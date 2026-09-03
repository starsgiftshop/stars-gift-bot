import os
import sqlite3
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    BotCommand,
    MenuButtonCommands,
    ReplyKeyboardRemove,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters,
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

DB_FILE = "stargift_v3.db"
START_IMAGE = "stargift_start.png"


def money(amount: int) -> str:
    return f"{amount:,}".replace(",", " ")


def get_db():
    con = sqlite3.connect(DB_FILE)
    con.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            balance INTEGER NOT NULL DEFAULT 0
        )
    """)
    con.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            item TEXT NOT NULL,
            amount INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending'
        )
    """)
    con.commit()
    return con


def ensure_user(user_id: int):
    con = get_db()
    con.execute(
        "INSERT OR IGNORE INTO users(user_id,balance) VALUES(?,0)",
        (user_id,),
    )
    con.commit()
    con.close()


def get_balance(user_id: int) -> int:
    ensure_user(user_id)
    con = get_db()
    row = con.execute(
        "SELECT balance FROM users WHERE user_id=?",
        (user_id,),
    ).fetchone()
    con.close()
    return row[0] if row else 0


def create_order(user_id: int, item: str, amount: int) -> int:
    con = get_db()
    cur = con.execute(
        "INSERT INTO orders(user_id,item,amount,status) VALUES(?,?,?,'pending')",
        (user_id, item, amount),
    )
    con.commit()
    order_id = cur.lastrowid
    con.close()
    return order_id


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
            InlineKeyboardButton("📦 Buyurtmalar", callback_data="orders"),
        ],
        [
            InlineKeyboardButton("👤 Profilim", callback_data="profile"),
            InlineKeyboardButton("🔵 Yordam", callback_data="help"),
        ],
        [
            InlineKeyboardButton("ℹ️ Ma'lumot", callback_data="info"),
        ],
    ])


def back_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("‹ Bosh sahifa", callback_data="home")]
    ])


async def edit_page(query, text, markup):
    """Photo bilan yuborilgan /start xabarini caption sifatida,
    oddiy xabarni esa text sifatida tahrirlaydi.
    Shu sababli /start rasmdan keyingi inline tugmalar ham ishlaydi."""
    if query.message and query.message.photo:
        await query.edit_message_caption(
            caption=text,
            reply_markup=markup,
        )
    else:
        await query.edit_message_text(
            text=text,
            reply_markup=markup,
        )


async def setup_bot(app: Application):
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
        "Stars, Gifts va Premium — bir joyda.\n\n"
        "⚡ Tezkor • 🔐 Ishonchli • 💳 So'mda\n"
        "⏱ O'rtacha bajarilish: 30 soniya\n\n"
        "Kerakli bo'limni tanlang:"
    )

    if not update.message:
        return

    # Old ReplyKeyboard (Yulduzlar/Balansim/Buyurtmalar...) ni majburan olib tashlaymiz.
    # Endi faqat Telegramning yuqoridagi Menu belgisi ishlatiladi.
    await update.message.reply_text(
        "✦ Yangi menyu yoqildi ✦",
        reply_markup=ReplyKeyboardRemove(),
    )

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


async def services(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✦ STARGIFT SHOP ✦\n\nKerakli bo'limni tanlang:",
        reply_markup=home_keyboard(),
    )


async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"💰 BALANSIM\n\nJoriy balans: {money(get_balance(update.effective_user.id))} so'm",
        reply_markup=back_keyboard(),
    )


async def orders_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_orders(update.message, update.effective_user.id, edit=False)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"🔵 YORDAM\n\nAdministrator: {ADMIN}\n\n"
        "Savol yoki muammo bo'lsa yozing.\n"
        "⏱ Javob/bajarilish: 30 soniya.",
        reply_markup=back_keyboard(),
    )


async def show_orders(message, user_id: int, edit=False):
    con = get_db()
    rows = con.execute(
        """
        SELECT id,item,amount,status
        FROM orders
        WHERE user_id=?
        ORDER BY id DESC
        LIMIT 30
        """,
        (user_id,),
    ).fetchall()
    con.close()

    if not rows:
        text = (
            "📦 BUYURTMALARIM\n\n"
            "Hozircha hech qanday buyurtma bermagansiz. 😊\n\n"
            "Buyurtma berganingizdan keyin shu yerda ko'rinadi."
        )
    else:
        text = "📦 BUYURTMALARIM\n\n"
        for order_id, item, amount, status in rows:
            status_text = {
                "pending": "⏳ Kutilmoqda",
                "paid": "✅ To'langan",
                "completed": "🎉 Bajarildi",
                "cancelled": "❌ Bekor qilingan",
            }.get(status, status)
            text += (
                f"№ {order_id}\n"
                f"• {item}\n"
                f"• {money(amount)} so'm\n"
                f"• {status_text}\n\n"
            )

    markup = back_keyboard()

    if edit:
        await edit_page(message, text, markup)
    else:
        await message.reply_text(text, reply_markup=markup)


async def stars_page(query):
    packages = [25, 50, 100, 125, 150, 175, 200, 300, 400, 500]
    rows = []
    for i in range(0, len(packages), 2):
        rows.append([
            InlineKeyboardButton(
                f"⭐ {count} • {money(count * STAR_PRICE)} so'm",
                callback_data=f"star:{count}",
            )
            for count in packages[i:i + 2]
        ])
    rows.append([InlineKeyboardButton("‹ Bosh sahifa", callback_data="home")])

    await edit_page(
        query,
        "⭐ YULDUZLAR\n\n"
        "Kerakli Stars paketini tanlang.\n"
        "1 ⭐ = 195 so'm",
        InlineKeyboardMarkup(rows),
    )


async def premium_page(query):
    rows = []
    for i in range(0, len(PREMIUM), 2):
        row = []
        for index in range(i, min(i + 2, len(PREMIUM))):
            name, price = PREMIUM[index]
            row.append(
                InlineKeyboardButton(
                    f"💎 {name} • {money(price)} so'm",
                    callback_data=f"prem:{index}",
                )
            )
        rows.append(row)
    rows.append([InlineKeyboardButton("‹ Bosh sahifa", callback_data="home")])

    await edit_page(
        query,
        "💎 PREMIUM\n\nPremium muddatini tanlang:",
        InlineKeyboardMarkup(rows),
    )


async def topup_page(query):
    rows = []
    for i in range(0, len(TOPUPS), 2):
        rows.append([
            InlineKeyboardButton(
                f"💳 {money(amount)} so'm",
                callback_data=f"top:{amount}",
            )
            for amount in TOPUPS[i:i + 2]
        ])
    rows.append([InlineKeyboardButton("‹ Bosh sahifa", callback_data="home")])

    await edit_page(
        query,
        "➕ HISOB TO'LDIRISH\n\nKerakli summani tanlang.\nTo'lov summalari so'mda.",
        InlineKeyboardMarkup(rows),
    )


async def gifts_page(query, context):
    try:
        result = await context.bot.get_available_gifts()
        gifts = list(result.gifts)
    except Exception as exc:
        print("GIFTS ERROR:", repr(exc))
        await edit_page(
            query,
            "🎁 SOVG'ALAR\n\nSovg'alar ro'yxatini hozircha olish imkoni bo'lmadi.",
            back_keyboard(),
        )
        return

    if not gifts:
        await edit_page(
            query,
            "🎁 SOVG'ALAR\n\nHozircha mavjud sovg'a yo'q.",
            back_keyboard(),
        )
        return

    rows = []
    for i in range(0, min(len(gifts), 40), 2):
        row = []
        for gift in gifts[i:i + 2]:
            price = gift.star_count * STAR_PRICE
            emoji = getattr(gift.sticker, "emoji", None) or "🎁"
            row.append(
                InlineKeyboardButton(
                    f"{emoji} {gift.star_count}⭐ • {money(price)} so'm",
                    callback_data=f"gift:{gift.id}",
                )
            )
        rows.append(row)

    rows.append([InlineKeyboardButton("‹ Bosh sahifa", callback_data="home")])

    await edit_page(
        query,
        "🎁 SOVG'ALAR\n\nSovg'ani tanlang.\n"
        "Tanlaganda haqiqiy Telegram gift stikeri yuboriladi.",
        InlineKeyboardMarkup(rows),
    )


async def profile_page(query, user):
    username = f"@{user.username}" if user.username else "username yo'q"
    await edit_page(
        query,
        "👤 PROFILIM\n\n"
        f"Username: {username}\n"
        f"ID: {user.id}\n"
        f"💰 Balans: {money(get_balance(user.id))} so'm",
        back_keyboard(),
    )


async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    ensure_user(user.id)

    try:
        await query.answer()
        data = query.data or ""

        if data == "home":
            await edit_page(
                query,
                "✦ STARGIFT SHOP ✦\n\n"
                "⭐ Yulduzlar • 🎁 Sovg'alar • 💎 Premium\n\n"
                "Kerakli bo'limni tanlang:",
                home_keyboard(),
            )

        elif data == "stars":
            await stars_page(query)

        elif data == "gifts":
            await gifts_page(query, context)

        elif data == "premium":
            await premium_page(query)

        elif data == "balance":
            await edit_page(
                query,
                f"💰 BALANSIM\n\nJoriy balans: {money(get_balance(user.id))} so'm",
                back_keyboard(),
            )

        elif data == "topup":
            await topup_page(query)

        elif data == "orders":
            await show_orders(query.message, user.id, edit=True)

        elif data == "profile":
            await profile_page(query, user)

        elif data == "help":
            await edit_page(
                query,
                f"🔵 YORDAM\n\nAdministrator: {ADMIN}\n\n"
                "Savol yoki muammo bo'lsa yozing.",
                back_keyboard(),
            )

        elif data == "info":
            await edit_page(
                query,
                "ℹ️ MA'LUMOT\n\n"
                "✦ STARGIFT SHOP\n"
                "⭐ Yulduzlar\n"
                "🎁 Telegram sovg'alari\n"
                "💎 Premium\n\n"
                "💳 Narxlar so'mda.\n"
                "⏱ O'rtacha bajarilish: 30 soniya.",
                back_keyboard(),
            )

        elif data.startswith("star:"):
            count = int(data.split(":", 1)[1])
            if count not in [25, 50, 100, 125, 150, 175, 200, 300, 400, 500]:
                raise ValueError("Noto'g'ri Stars paketi")
            amount = count * STAR_PRICE
            order_id = create_order(user.id, f"{count} Stars", amount)

            await edit_page(
                query,
                "⭐ BUYURTMA YARATILDI\n\n"
                f"Stars: {count} ⭐\n"
                f"Narx: {money(amount)} so'm\n"
                f"Buyurtma: №{order_id}\n"
                "Holat: ⏳ Kutilmoqda",
                InlineKeyboardMarkup([
                    [InlineKeyboardButton("📦 Buyurtmam", callback_data="orders")],
                    [InlineKeyboardButton("‹ Bosh sahifa", callback_data="home")],
                ]),
            )

        elif data.startswith("prem:"):
            index = int(data.split(":", 1)[1])
            if index < 0 or index >= len(PREMIUM):
                raise ValueError("Noto'g'ri Premium")
            name, amount = PREMIUM[index]
            order_id = create_order(user.id, f"Premium {name}", amount)

            await edit_page(
                query,
                "💎 PREMIUM BUYURTMASI\n\n"
                f"Muddat: {name}\n"
                f"Narx: {money(amount)} so'm\n"
                f"Buyurtma: №{order_id}\n"
                "Holat: ⏳ Kutilmoqda",
                InlineKeyboardMarkup([
                    [InlineKeyboardButton("📦 Buyurtmam", callback_data="orders")],
                    [InlineKeyboardButton("‹ Bosh sahifa", callback_data="home")],
                ]),
            )

        elif data.startswith("top:"):
            amount = int(data.split(":", 1)[1])
            if amount not in TOPUPS:
                raise ValueError("Noto'g'ri summa")
            order_id = create_order(user.id, "Hisob to'ldirish", amount)

            await edit_page(
                query,
                "➕ HISOB TO'LDIRISH\n\n"
                f"Summa: {money(amount)} so'm\n"
                f"Buyurtma: №{order_id}\n"
                "Holat: ⏳ Kutilmoqda\n\n"
                "To'lov tasdiqlangach hisob to'ldiriladi.",
                InlineKeyboardMarkup([
                    [InlineKeyboardButton("📦 Buyurtmam", callback_data="orders")],
                    [InlineKeyboardButton("‹ Bosh sahifa", callback_data="home")],
                ]),
            )

        elif data.startswith("gift:"):
            gift_id = data.split(":", 1)[1]
            result = await context.bot.get_available_gifts()
            gift = next(
                (g for g in result.gifts if str(g.id) == str(gift_id)),
                None,
            )
            if gift is None:
                raise ValueError("Gift topilmadi")

            amount = gift.star_count * STAR_PRICE
            order_id = create_order(
                user.id,
                f"Telegram Gift ({gift.star_count} Stars)",
                amount,
            )

            await query.message.reply_sticker(gift.sticker.file_id)
            await query.message.reply_text(
                "🎁 TANLANGAN SOVG'A\n\n"
                f"⭐ Qiymati: {gift.star_count} Stars\n"
                f"💳 Narxi: {money(amount)} so'm\n"
                f"📦 Buyurtma: №{order_id}\n"
                "⏳ Holat: Kutilmoqda",
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("🎁 Yana sovg'a", callback_data="gifts"),
                        InlineKeyboardButton("📦 Buyurtmam", callback_data="orders"),
                    ],
                    [InlineKeyboardButton("‹ Bosh sahifa", callback_data="home")],
                ]),
            )

    except Exception as exc:
        print("CALLBACK ERROR:", repr(exc))
        try:
            await query.answer("Xatolik yuz berdi", show_alert=False)
        except Exception:
            pass
        try:
            await query.message.reply_text(
                "⚠️ Xatolik yuz berdi.\nQaytadan urinib ko'ring.",
                reply_markup=back_keyboard(),
            )
        except Exception:
            pass



async def legacy_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Eski ReplyKeyboard qolib ketgan bo'lsa, uning tugmalarini ham ishlatadi.
    Birinchi ishlatishda eski klaviaturani olib tashlaydi."""
    message = update.message
    if not message:
        return

    await message.reply_text(
        "✦ STARGIFT SHOP ✦\n\n"
        "Eski menyu yangilandi. Endi menyu yuqoridagi ⠿ belgisi orqali ochiladi.",
        reply_markup=ReplyKeyboardRemove(),
    )

    text = (message.text or "").strip().lower()

    # Eski tugmalarni yangi sahifalarga yo'naltiramiz.
    if text in {"⭐ yulduzlar", "yulduzlar", "⭐ stars", "stars"}:
        await message.reply_text(
            "⭐ YULDUZLAR\n\nKerakli Stars paketini tanlang.\n1 ⭐ = 195 so'm",
            reply_markup=stars_keyboard(),
        )
    elif text in {"🎁 sovg'alar", "sovg'alar", "🎁 gifts", "gifts"}:
        await message.reply_text(
            "🎁 SOVG'ALAR\n\nSovg'alar ro'yxatini ochish uchun bosing:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🎁 Sovg'alarni ochish", callback_data="gifts")],
                [InlineKeyboardButton("‹ Bosh sahifa", callback_data="home")],
            ]),
        )
    elif text in {"💎 premium", "premium"}:
        await message.reply_text(
            "💎 PREMIUM\n\nPremium muddatini tanlang:",
            reply_markup=premium_keyboard(),
        )
    elif text in {"💰 balansim", "balansim", "💰 balans", "balans"}:
        await message.reply_text(
            f"💰 BALANSIM\n\nJoriy balans: {money(get_balance(update.effective_user.id))} so'm",
            reply_markup=back_keyboard(),
        )
    elif text in {"➕ hisob to'ldirish", "hisob to'ldirish", "hisob", "➕ hisob"}:
        await message.reply_text(
            "➕ HISOB TO'LDIRISH\n\nKerakli summani tanlang:",
            reply_markup=topup_keyboard(),
        )
    elif text in {"📦 buyurtmalar", "buyurtmalar", "📦 buyurtmalarim", "buyurtmalarim"}:
        await show_orders(message, update.effective_user.id, edit=False)
    elif text in {"👤 profilim", "profilim", "profil"}:
        user = update.effective_user
        username = f"@{user.username}" if user.username else "username yo'q"
        await message.reply_text(
            "👤 PROFILIM\n\n"
            f"Username: {username}\n"
            f"ID: {user.id}\n"
            f"💰 Balans: {money(get_balance(user.id))} so'm",
            reply_markup=back_keyboard(),
        )
    elif text in {"🔵 yordam", "yordam"}:
        await message.reply_text(
            f"🔵 YORDAM\n\nAdministrator: {ADMIN}\n\nSavol yoki muammo bo'lsa yozing.",
            reply_markup=back_keyboard(),
        )
    elif text in {"ℹ️ ma'lumot", "ma'lumot", "ma'lumot"}:
        await message.reply_text(
            "ℹ️ MA'LUMOT\n\n"
            "✦ STARGIFT SHOP\n"
            "⭐ Yulduzlar\n🎁 Telegram sovg'alari\n💎 Premium\n\n"
            "💳 Narxlar so'mda.\n⏱ O'rtacha bajarilish: 30 soniya.",
            reply_markup=back_keyboard(),
        )


def stars_keyboard():
    packages = [25, 50, 100, 125, 150, 175, 200, 300, 400, 500]
    rows = []
    for i in range(0, len(packages), 2):
        rows.append([
            InlineKeyboardButton(
                f"⭐ {count} • {money(count * STAR_PRICE)} so'm",
                callback_data=f"star:{count}",
            )
            for count in packages[i:i+2]
        ])
    rows.append([InlineKeyboardButton("‹ Bosh sahifa", callback_data="home")])
    return InlineKeyboardMarkup(rows)


def pre
