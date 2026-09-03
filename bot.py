import os
import sqlite3
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    MenuButtonCommands,
    BotCommand,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

TOKEN = os.getenv("BOT_TOKEN")
ADMIN = "@Shamsbekman"
START_IMAGE = "stargift_start.png"

STAR_PRICE = 195
PREMIUM = [
    ("1 oy", 45000),
    ("3 oy", 164000),
    ("6 oy", 222000),
    ("12 oy", 377000),
]
TOPUP = [10000, 20000, 50000, 100000, 200000, 500000]


# ---------- DATABASE ----------
def db():
    con = sqlite3.connect("shop.db")
    con.execute("""
        CREATE TABLE IF NOT EXISTS users(
            user_id INTEGER PRIMARY KEY,
            balance INTEGER DEFAULT 0
        )
    """)
    con.execute("""
        CREATE TABLE IF NOT EXISTS orders(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            item TEXT NOT NULL,
            amount INTEGER NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at INTEGER DEFAULT (strftime('%s','now'))
        )
    """)
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


def get_balance(user_id):
    ensure_user(user_id)
    con = db()
    row = con.execute(
        "SELECT balance FROM users WHERE user_id=?",
        (user_id,),
    ).fetchone()
    con.close()
    return row[0] if row else 0


def create_order(user_id, item, amount):
    con = db()
    cur = con.execute(
        "INSERT INTO orders(user_id,item,amount,status) VALUES(?,?,?,'pending')",
        (user_id, item, amount),
    )
    con.commit()
    order_id = cur.lastrowid
    con.close()
    return order_id


# ---------- UNIQUE UI ----------
def home_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("⭐ STARS", callback_data="stars"),
            InlineKeyboardButton("🎁 GIFTS", callback_data="gift"),
        ],
        [
            InlineKeyboardButton("💎 PREMIUM", callback_data="premium"),
            InlineKeyboardButton("💰 BALANS", callback_data="balance"),
        ],
        [
            InlineKeyboardButton("➕ HISOB", callback_data="topup"),
            InlineKeyboardButton("📦 BUYURTMALAR", callback_data="orders"),
        ],
        [
            InlineKeyboardButton("👤 PROFIL", callback_data="profile"),
            InlineKeyboardButton("🔵 YORDAM", callback_data="help"),
        ],
        [
            InlineKeyboardButton("ℹ️ MA'LUMOT", callback_data="info"),
        ],
    ])


def stars_keyboard():
    packs = [25, 50, 100, 125, 150, 175, 200, 300, 400, 500]
    rows, row = [], []
    for n in packs:
        row.append(
            InlineKeyboardButton(
                f"⭐ {n} | {n*STAR_PRICE:,}".replace(",", " "),
                callback_data=f"star:{n}",
            )
        )
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([
        InlineKeyboardButton("↩️ ORQAGA", callback_data="home")
    ])
    return InlineKeyboardMarkup(rows)


def premium_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("💎 1 OY", callback_data="prem:0"),
            InlineKeyboardButton("45 000 so'm", callback_data="prem:0"),
        ],
        [
            InlineKeyboardButton("💎 3 OY", callback_data="prem:1"),
            InlineKeyboardButton("164 000 so'm", callback_data="prem:1"),
        ],
        [
            InlineKeyboardButton("💎 6 OY", callback_data="prem:2"),
            InlineKeyboardButton("222 000 so'm", callback_data="prem:2"),
        ],
        [
            InlineKeyboardButton("💎 12 OY", callback_data="prem:3"),
            InlineKeyboardButton("377 000 so'm", callback_data="prem:3"),
        ],
        [
            InlineKeyboardButton("↩️ ORQAGA", callback_data="home")
        ],
    ])


def topup_keyboard():
    rows, row = [], []
    for amount in TOPUP:
        row.append(
            InlineKeyboardButton(
                f"💳 {amount:,} so'm".replace(",", " "),
                callback_data=f"topup:{amount}",
            )
        )
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([
        InlineKeyboardButton("↩️ ORQAGA", callback_data="home")
    ])
    return InlineKeyboardMarkup(rows)


def back_keyboard(target="home"):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("↩️ ORQAGA", callback_data=target)],
        [InlineKeyboardButton("⌂ BOSH SAHIFA", callback_data="home")],
    ])


# ---------- START ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    ensure_user(user.id)

    text = (
        "✨ STARGIFT SHOP ✨\n\n"
        "Siz uchun yaratilgan zamonaviy raqamli do'kon.\n\n"
        "⭐ Stars   •   🎁 Gifts   •   💎 Premium\n"
        "⚡ Tezkor xizmat   •   🔐 Ishonchli\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "KERAKLI BO'LIMNI TANLANG\n"
        "━━━━━━━━━━━━━━━━━━"
    )

    if update.message:
        if os.path.exists(START_IMAGE):
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


# ---------- PAGES ----------
async def show_services(query):
    await query.edit_message_text(
        "🧩 XIZMATLAR\n\n"
        "Bir bo'limni tanlang — hammasi shu oynada boshqariladi.",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("⭐ STARS", callback_data="stars"),
                InlineKeyboardButton("🎁 GIFTS", callback_data="gift"),
            ],
            [
                InlineKeyboardButton("💎 PREMIUM", callback_data="premium"),
            ],
            [
                InlineKeyboardButton("↩️ BOSH SAHIFA", callback_data="home")
            ],
        ]),
    )


async def show_orders(query):
    user_id = query.from_user.id
    con = db()
    rows = con.execute(
        "SELECT id,item,amount,status FROM orders "
        "WHERE user_id=? ORDER BY id DESC LIMIT 20",
        (user_id,),
    ).fetchall()
    con.close()

    if not rows:
        await query.edit_message_text(
            "📦 BUYURTMALAR\n\n"
            "Hozircha bu yer bo'sh. 😊\n\n"
            "Birinchi buyurtmangiz shu yerda paydo bo'ladi.",
            reply_markup=back_keyboard(),
        )
        return

    lines = ["📦 BUYURTMALAR\n"]
    for order_id, item, amount, status in rows:
        lines.append(
            f"▸ #{order_id}  {item}\n"
            f"  💳 {amount:,} so'm   •   📌 {status}\n".replace(",", " ")
        )

    await query.edit_message_text(
        "\n".join(lines),
        reply_markup=back_keyboard(),
    )


async def show_balance(query):
    amount = get_balance(query.from_user.id)
    await query.edit_message_text(
        "💰 BALANS\n\n"
        f"Joriy balans:  {amount:,} so'm\n\n".replace(",", " ")
        + "Hisobingizni to'ldirish uchun pastdagi tugmani bosing.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ HISOBNI TO'LDIRISH", callback_data="topup")],
            [InlineKeyboardButton("⌂ BOSH SAHIFA", callback_data="home")],
        ]),
    )


async def show_profile(query):
    user = query.from_user
    username = f"@{user.username}" if user.username else "username yo'q"
    await query.edit_message_text(
        "👤 PROFIL\n\n"
        f"ID: {user.id}\n"
        f"Username: {username}\n"
        f"Balans: {get_balance(user.id):,} so'm".replace(",", " "),
        reply_markup=back_keyboard(),
    )


async def show_help(query):
    await query.edit_message_text(
        "🔵 YORDAM\n\n"
        "Savol yoki muammo bo'lsa operatorga yozing.\n\n"
        f"👨‍💻 Operator: {ADMIN}\n"
        "⏱ O'rtacha javob: 30 soniya",
        reply_markup=back_keyboard(),
    )


async def show_info(query):
    await query.edit_message_text(
        "ℹ️ STARGIFT SHOP\n\n"
        "⭐ Stars\n"
        "🎁 Telegram Gifts\n"
        "💎 Premium\n\n"
        "⚡ Tezkor xizmat\n"
        "🔐 Xavfsiz jarayon\n"
        "💳 So'mda hisob-kitob\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "SIFAT • TEZLIK • ISHONCH",
        reply_markup=back_keyboard(),
    )


# ---------- GIFTS ----------
async def show_gifts(query, bot):
    try:
        result = await bot.get_available_gifts()
        gifts = result.gifts
    except Exception:
        await query.edit_message_text(
            "🎁 GIFTS\n\n"
            "Giftlar hozircha yuklanmadi.\n"
            "Bir necha soniyadan keyin qayta urinib ko'ring.",
            reply_markup=back_keyboard(),
        )
        return

    if not gifts:
        await query.edit_message_text(
            "🎁 GIFTS\n\nHozircha mavjud Gift yo'q.",
            reply_markup=back_keyboard(),
        )
        return

    rows, row = [], []
    for gift in gifts[:30]:
        stars = gift.star_count
        price = stars * STAR_PRICE
        row.append(
            InlineKeyboardButton(
                f"🎁 {stars}⭐ | {price:,}".replace(",", " "),
                callback_data=f"gift_select:{gift.id}",
            )
        )
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)

    rows.append([
        InlineKeyboardButton("↩️ BOSH SAHIFA", callback_data="home")
    ])

    await query.edit_message_text(
        "🎁 GIFTS\n\n"
        "Kerakli Giftni tanlang.\n"
        "Tanlanganda Giftning haqiqiy Telegram stickeri ko'rsatiladi.",
        reply_markup=InlineKeyboardMarkup(rows),
    )


async def select_gift(query, gift_id, bot):
    try:
        result = await bot.get_available_gifts()
        gift = next(
            (g for g in result.gifts if str(g.id) == str(gift_id)),
            None,
        )
        if gift is None:
            raise ValueError("Gift topilmadi")

        stars = gift.star_count
        price = stars * STAR_PRICE

        # Gift rasmi/stickeri alohida xabar sifatida chiqadi.
        await query.message.reply_sticker(gift.sticker.file_id)

        order_id = create_order(
            query.from_user.id,
            f"Gift ({stars} Stars)",
            price,
        )

        await query.message.reply_text(
            "🎁 TANLANGAN GIFT\n\n"
            f"⭐ Qiymati: {stars} Stars\n"
            f"💳 Narxi: {price:,} so'm\n"
            f"📦 Buyurtma: #{order_id}\n"
            "⏱ O'rtacha: 30 soniya\n\n"
            "To'lov integratsiyasi ulangach, tasdiqlash avtomatik ishlaydi."
            .replace(",", " "),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🎁 BOSHQA GIFT", callback_data="gift")],
                [InlineKeyboardButton("⌂ BOSH SAHIFA", callback_data="home")],
            ]),
        )

    except Exception:
        await query.message.reply_text(
            "❌ Giftni ochishda xatolik yuz berdi.\n"
            "Qayta urinib ko'ring.",
            reply_markup=back_keyboard(),
        )


# ---------- CALLBACKS ----------
async def callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id
    ensure_user(user_id)

    if data == "home":
        await query.edit_message_text(
            "✨ STARGIFT SHOP ✨\n\n"
            "Zamonaviy boshqaruv paneli.\n"
            "Kerakli bo'limni tanlang:",
            reply_markup=home_keyboard(),
        )

    elif data == "services":
        await show_services(query)

    elif data == "stars":
        await query.edit_message_text(
            "⭐ STARS\n\n"
            f"1 Star = {STAR_PRICE} so'm\n"
            "Paketni tanlang:",
            reply_markup=stars_keyboard(),
        )

    elif data == "gift":
        await show_gifts(query, context.bot)

    elif data == "premium":
        await query.edit_message_text(
            "💎 PREMIUM\n\nMuddatni tanlang:",
            reply_markup=premium_keyboard(),
        )

    elif data == "balance":
        await show_balance(query)

    elif data == "topup":
        await query.edit_message_text(
            "➕ HISOB TO'LDIRISH\n\nSummani tanlang:",
            reply_markup=topup_keyboard(),
        )

    elif data == "orders":
        await show_orders(query)

    elif data == "profile":
        await show_profile(query)

    elif data == "help":
        await show_help(query)

    elif data == "info":
        await show_info(query)

    elif data.startswith("star:"):
        n = int(data.split(":")[1])
        amount = n * STAR_PRICE
        order_id = create_order(user_id, f"{n} Stars", amount)
        await query.edit_message_text(
            "⭐ STARS BUYURTMASI\n\n"
            f"📦 #{order_id}\n"
            f"⭐ {n} Stars\n"
            f"💳 {amount:,} so'm\n"
            "📌 pending\n\n"
            "To'lov integratsiyasi ulangach avtomatik tasdiqlanadi."
            .replace(",", " "),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⭐ BOSHQA PAKET", callback_data="stars")],
                [InlineKeyboardButton("⌂ BOSH SAHIFA", callback_data="home")],
            ]),
        )

    elif data.startswith("prem:"):
        index = int(data.split(":")[1])
        name, amount = PREMIUM[index]
        order_id = create_order(user_id, f"Premium {name}", amount)
        await query.edit_message_text(
            "💎 PREMIUM BUYURTMASI\n\n"
            f"📦 #{order_id}\n"
            f"💎 Premium {name}\n"
            f"💳 {amount:,} so'm\n"
            "📌 pending\n\n"
            "To'lov integratsiyasi ulangach avtomatik tasdiqlanadi."
            .replace(",", " "),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("💎 BOSHQA MUDDAT", callback_data="premium")],
                [InlineKeyboardButton("⌂ BOSH SAHIFA", callback_data="home")],
            ]),
        )

    elif data.startswith("topup:"):
        amount = int(data.split(":")[1])
        order_id = create_order(user_id, "Hisob to'ldirish", amount)
        await query.edit_message_text(
            "➕ HISOB TO'LDIRISH\n\n"
            f"📦 #{order_id}\n"
            f"💳 {amount:,} so'm\n"
            "📌 pending\n\n"
            "To'lov tizimi ulangach avtomatik tasdiqlanadi."
            .replace(",", " "),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ YANA TO'LDIRISH", callback_data="topup")],
                [InlineKeyboardButton("⌂ BOSH SAHIFA", callback_data="home")],
            ]),
        )

    elif data.startswith("gift_select:"):
        gift_id = data.split(":", 1)[1]
        await select_gift(query, gift_id, context.bot)


# ---------- COMMANDS ----------
async def commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)


async def unknown_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✨ STARGIFT SHOP\n\n"
        "Bo'limlarni pastdagi bot menyusi orqali tanlang yoki /start bosing."
    )


# ---------- STARTUP ----------
async def post_init(app: Application):
    await app.bot.set_my_commands([
        BotCommand("start", "Bosh sahifa"),
        BotCommand("services", "Xizmatlar"),
        BotCommand("balance", "Balans"),
        BotCommand("orders", "Buyurtmalarim"),
        BotCommand("help", "Yordam"),
    ])
    # Telegram chatida menyu belgisi doim mavjud bo'lishi uchun
    # standart bot menu tugmasini Commands rejimiga o'tkazamiz.
    await app.bot.set_chat_menu_button(
        menu_button=MenuButtonCommands()
    )


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    print("STARGIFT ERROR:", repr(context.error))


def main():
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN Railway Variables ichida topilmadi.")

    db()

    app = (
        Application.builder()
        .token(TOKEN)
        .post_init(post_init)
        .build()
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("services", show_services_command))
    app.add_handler(CommandHandler("balance", balance_command))
    app.add_handler(CommandHandler("orders", orders_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CallbackQueryHandler(callbacks))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, unknown_text))
    app.add_error_handler(error_handler)

    print("STARGIFT SHOP — MODERN UI — RUNNING")
    app.run_polling(drop_pending_updates=True)


async def show_services_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🧩 XIZMATLAR\n\nBo'limni tanlang:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⭐ STARS", callback_data="stars"),
             InlineKeyboardButton("🎁 GIFTS", callback_data="gift")],
            [InlineKeyboardButton("💎 PREMIUM", callback_data="premium")],
        ])
    )


async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ensure_user(update.effective_user.id)
    await update.message.reply_text(
        f"💰 BALANS\n\n{get_balance(update.effective_user.id):,} so'm".replace(",", " "),
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ HISOB TO'LDIRISH", callback_data="topup")],
            [InlineKeyboardButton("⌂ BOSH SAHIFA", callback_data="home")],
        ])
    )


async def orders_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Command uchun CallbackQuery talab qilinmagani sabab alohida ko'rsatamiz.
    user_id = update.effective_user.id
    con = db()
    rows = con.execute(
        "SELECT id,item,amount,status FROM orders WHERE user_id=? ORDER BY id DESC LIMIT 20",
        (user_id,),
    ).fetchall()
    con.close()
    if not rows:
        await update.message.reply_text(
            "📦 BUYURTMALAR\n\nHozircha buyurtma yo'q."
        )
        return
    text = ["📦 BUYURTMALAR\n"]
    for oid, item, amount, status in rows:
        text.append(f"▸ #{oid} {item} — {amount:,} so'm — {status}".replace(",", " "))
    await update.message.reply_text("\n".join(text))


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔵 YORDAM\n\n"
        f"Operator: {ADMIN}\n"
        "⏱ O'rtacha javob: 30 soniya"
    )


if __name__ == "__main__":
    main()
    
