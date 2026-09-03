import os
import sqlite3
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
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

# GitHub repo ichiga shu nomli start rasmini ham joylasangiz, /start da rasm chiqadi.
START_IMAGE = "stargift_start.png"

STAR_PRICE = 195
PREMIUM = [
    ("1 oy", 45000),
    ("3 oy", 164000),
    ("6 oy", 222000),
    ("12 oy", 377000),
]
TOPUP = [10000, 20000, 50000, 100000, 200000, 500000]


# ================= DATABASE =================
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
            status TEXT DEFAULT 'pending'
        )
    """)
    con.commit()
    return con


def ensure_user(user_id):
    con = db()
    con.execute(
        "INSERT OR IGNORE INTO users(user_id,balance) VALUES(?,0)",
        (user_id,)
    )
    con.commit()
    con.close()


def get_balance(user_id):
    ensure_user(user_id)
    con = db()
    row = con.execute(
        "SELECT balance FROM users WHERE user_id=?",
        (user_id,)
    ).fetchone()
    con.close()
    return row[0] if row else 0


def create_order(user_id, item, amount):
    con = db()
    cur = con.execute(
        "INSERT INTO orders(user_id,item,amount,status) VALUES(?,?,?,'pending')",
        (user_id, item, amount)
    )
    con.commit()
    order_id = cur.lastrowid
    con.close()
    return order_id


# ================= PASTDA DOIMIY MENYU =================
# Neo SMM matnlari ko'chirilmagan.
# Joylashish esa Telegramning reply-keyboard ko'rinishida.
def main_keyboard():
    return ReplyKeyboardMarkup(
        [
            [
                KeyboardButton("⭐ Yulduzlar"),
                KeyboardButton("🎁 Sovg'alar"),
            ],
            [
                KeyboardButton("💎 Premium"),
                KeyboardButton("💰 Mening balansim"),
            ],
            [
                KeyboardButton("➕ Hisobimni to'ldirish"),
                KeyboardButton("📦 Buyurtmalarim"),
            ],
            [
                KeyboardButton("👤 Kabinetim"),
                KeyboardButton("🔵 Ko'mak"),
            ],
            [
                KeyboardButton("ℹ️ Biz haqimizda"),
            ],
        ],
        resize_keyboard=True,
        is_persistent=True,
        input_field_placeholder="Bo'limni tanlang...",
    )


def home_inline():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("⭐ Yulduzlar", callback_data="stars"),
            InlineKeyboardButton("🎁 Sovg'alar", callback_data="gift"),
        ],
        [
            InlineKeyboardButton("💎 Premium", callback_data="premium"),
            InlineKeyboardButton("💰 Balans", callback_data="balance"),
        ],
        [
            InlineKeyboardButton("➕ Hisob", callback_data="topup"),
            InlineKeyboardButton("📦 Buyurtmalar", callback_data="orders"),
        ],
        [
            InlineKeyboardButton("👤 Kabinet", callback_data="profile"),
            InlineKeyboardButton("🔵 Ko'mak", callback_data="help"),
        ],
        [
            InlineKeyboardButton("ℹ️ Ma'lumot", callback_data="info"),
        ],
    ])


def back_inline():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("↩️ Ortga", callback_data="home")]
    ])


# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    ensure_user(user.id)

    text = (
        "🌌 STARGIFT SHOP\n\n"
        "Raqamli sovg'alar va Premium xizmatlari uchun "
        "zamonaviy do'kon.\n\n"
        "⚡ Tezkor xizmat  •  🔐 Ishonchli  •  💳 So'mda\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "Pastdagi menyudan kerakli bo'limni tanlang."
    )

    if os.path.exists(START_IMAGE):
        with open(START_IMAGE, "rb") as photo:
            await update.message.reply_photo(
                photo=photo,
                caption=text,
                reply_markup=main_keyboard(),
            )
    else:
        await update.message.reply_text(
            text,
            reply_markup=main_keyboard(),
        )


# ================= PAGES =================
async def show_stars(target):
    await target.edit_message_text(
        "⭐ YULDUZLAR\n\n"
        "Kerakli paketni tanlang:",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("⭐ 25", callback_data="star:25"),
                InlineKeyboardButton("⭐ 50", callback_data="star:50"),
            ],
            [
                InlineKeyboardButton("⭐ 100", callback_data="star:100"),
                InlineKeyboardButton("⭐ 125", callback_data="star:125"),
            ],
            [
                InlineKeyboardButton("⭐ 150", callback_data="star:150"),
                InlineKeyboardButton("⭐ 175", callback_data="star:175"),
            ],
            [
                InlineKeyboardButton("⭐ 200", callback_data="star:200"),
                InlineKeyboardButton("⭐ 300", callback_data="star:300"),
            ],
            [
                InlineKeyboardButton("⭐ 400", callback_data="star:400"),
                InlineKeyboardButton("⭐ 500", callback_data="star:500"),
            ],
            [InlineKeyboardButton("⌂ BOSH SAHIFA", callback_data="home")],
        ])
    )


async def show_premium(target):
    await target.edit_message_text(
        "💎 PREMIUM\n\n"
        "O'zingizga mos muddatni tanlang:",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("💎 1 OY • 45 000", callback_data="prem:0"),
                InlineKeyboardButton("💎 3 OY • 164 000", callback_data="prem:1"),
            ],
            [
                InlineKeyboardButton("💎 6 OY • 222 000", callback_data="prem:2"),
                InlineKeyboardButton("💎 12 OY • 377 000", callback_data="prem:3"),
            ],
            [InlineKeyboardButton("⌂ BOSH SAHIFA", callback_data="home")],
        ])
    )


async def show_topup(target):
    rows = []
    row = []
    for amount in TOPUP:
        row.append(
            InlineKeyboardButton(
                f"{amount:,} so'm".replace(",", " "),
                callback_data=f"topup:{amount}"
            )
        )
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton("⌂ BOSH SAHIFA", callback_data="home")])

    await target.edit_message_text(
        "➕ HISOBNI TO'LDIRISH\n\n"
        "Kerakli summani belgilang:",
        reply_markup=InlineKeyboardMarkup(rows)
    )


async def show_balance(target):
    amount = get_balance(target.from_user.id)
    await target.edit_message_text(
        "💰 MENING BALANSIM\n\n"
        f"Joriy mablag': {amount:,} so'm".replace(",", " "),
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ HISOBNI TO'LDIRISH", callback_data="topup")],
            [InlineKeyboardButton("⌂ BOSH SAHIFA", callback_data="home")],
        ])
    )


async def show_profile(target):
    user = target.from_user
    username = f"@{user.username}" if user.username else "ko'rsatilmagan"
    await target.edit_message_text(
        "👤 KABINETIM\n\n"
        f"ID: {user.id}\n"
        f"Username: {username}\n"
        f"Balans: {get_balance(user.id):,} so'm".replace(",", " "),
        reply_markup=back_inline()
    )


async def show_help(target):
    await target.edit_message_text(
        "🔵 KO'MAK MARKAZI\n\n"
        f"Operator: {ADMIN}\n"
        "⏱ O'rtacha javob vaqti: 30 soniya\n\n"
        "Muammo bo'lsa, operatorga yozing.",
        reply_markup=back_inline()
    )


async def show_info(target):
    await target.edit_message_text(
        "ℹ️ STARGIFT SHOP HAQIDA\n\n"
        "⭐ Stars paketlari\n"
        "🎁 Telegram sovg'alari\n"
        "💎 Premium xizmatlari\n\n"
        "⚡ Qulay foydalanish\n"
        "🔐 Ishonchli jarayon\n"
        "💳 So'mdagi hisob-kitob",
        reply_markup=back_inline()
    )


async def show_orders(target):
    user_id = target.from_user.id
    con = db()
    rows = con.execute(
        "SELECT id,item,amount,status FROM orders "
        "WHERE user_id=? ORDER BY id DESC LIMIT 20",
        (user_id,)
    ).fetchall()
    con.close()

    if not rows:
        await target.edit_message_text(
            "📦 BUYURTMALARIM\n\n"
            "Hozircha bu bo'limda hech qanday buyurtma yo'q. 😊\n\n"
            "Buyurtma berganingizdan keyin shu yerda ko'rinadi.",
            reply_markup=back_inline()
        )
        return

    lines = ["📦 BUYURTMALARIM\n"]
    for oid, item, amount, status in rows:
        lines.append(
            f"№{oid} • {item}\n"
            f"💳 {amount:,} so'm • 📌 {status}\n".replace(",", " ")
        )

    await target.edit_message_text(
        "\n".join(lines),
        reply_markup=back_inline()
    )


# ================= GIFTS =================
async def show_gifts(target, bot):
    try:
        result = await bot.get_available_gifts()
        gifts = result.gifts
    except Exception:
        await target.edit_message_text(
            "🎁 SOVG'ALAR\n\n"
            "Sovg'alar ro'yxatini yuklashda muammo bo'ldi.\n"
            "Birozdan keyin yana urinib ko'ring.",
            reply_markup=back_inline()
        )
        return

    if not gifts:
        await target.edit_message_text(
            "🎁 SOVG'ALAR\n\nHozircha mavjud sovg'a topilmadi.",
            reply_markup=back_inline()
        )
        return

    rows = []
    row = []
    for gift in gifts[:30]:
        stars = gift.star_count
        price = stars * STAR_PRICE
        row.append(
            InlineKeyboardButton(
                f"🎁 {stars}⭐ • {price:,}".replace(",", " "),
                callback_data=f"gift:{gift.id}"
            )
        )
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton("⌂ BOSH SAHIFA", callback_data="home")])

    await target.edit_message_text(
        "🎁 SOVG'ALAR\n\n"
        "Sizga yoqqan sovg'ani tanlang.\n"
        "Tanlanganda uning haqiqiy Telegram stickeri ko'rsatiladi.",
        reply_markup=InlineKeyboardMarkup(rows)
    )


async def select_gift(query, gift_id, bot):
    try:
        result = await bot.get_available_gifts()
        gift = next(
            (g for g in result.gifts if str(g.id) == str(gift_id)),
            None
        )
        if gift is None:
            raise ValueError("Gift topilmadi")

        stars = gift.star_count
        price = stars * STAR_PRICE
        order_id = create_order(
            query.from_user.id,
            f"Sovg'a • {stars} Stars",
            price
        )

        await query.message.reply_sticker(gift.sticker.file_id)
        await query.message.reply_text(
            "🎁 TANLANGAN SOVG'A\n\n"
            f"⭐ Qiymati: {stars} Stars\n"
            f"💳 Narxi: {price:,} so'm\n"
            f"📦 Buyurtma №{order_id}\n"
            "⏱ O'rtacha: 30 soniya".replace(",", " "),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🎁 YANA TANLASH", callback_data="gift")],
                [InlineKeyboardButton("⌂ BOSH SAHIFA", callback_data="home")],
            ])
        )
    except Exception:
        await query.message.reply_text(
            "❌ Sovg'ani ochishda xatolik yuz berdi.",
            reply_markup=back_inline()
        )


# ================= CALLBACKS =================
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "home":
        await query.edit_message_text(
            "🌌 STARGIFT SHOP\n\n"
            "Kerakli bo'limni tanlang.\n"
            "Pastdagi doimiy menyu ham ochiq:",
            reply_markup=home_inline()
        )

    elif data == "stars":
        await show_stars(query)

    elif data == "gift":
        await show_gifts(query, context.bot)

    elif data == "premium":
        await show_premium(query)

    elif data == "balance":
        await show_balance(query)

    elif data == "topup":
        await show_topup(query)

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
        order_id = create_order(query.from_user.id, f"{n} Stars", amount)

        await query.edit_message_text(
            "⭐ YULDUZLAR BUYURTMASI\n\n"
            f"📦 №{order_id}\n"
            f"⭐ {n} Stars\n"
            f"💳 {amount:,} so'm\n"
            "📌 Holat: kutilmoqda".replace(",", " "),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⭐ YANA TANLASH", callback_data="stars")],
                [InlineKeyboardButton("⌂ BOSH SAHIFA", callback_data="home")],
            ])
        )

    elif data.startswith("prem:"):
        index = int(data.split(":")[1])
        name, amount = PREMIUM[index]
        order_id = create_order(
            query.from_user.id,
            f"Premium {name}",
            amount
        )

        await query.edit_message_text(
            "💎 PREMIUM BUYURTMASI\n\n"
            f"📦 №{order_id}\n"
            f"💎 Premium {name}\n"
            f"💳 {amount:,} so'm\n"
            "📌 Holat: kutilmoqda".replace(",", " "),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("💎 YANA TANLASH", callback_data="premium")],
                [InlineKeyboardButton("⌂ BOSH SAHIFA", callback_data="home")],
            ])
        )

    elif data.startswith("topup:"):
        amount = int(data.split(":")[1])
        order_id = create_order(
            query.from_user.id,
            "Hisob to'ldirish",
            amount
        )

        await query.edit_message_text(
            "➕ HISOB TO'LDIRISH\n\n"
            f"📦 №{order_id}\n"
            f"💳 {amount:,} so'm\n"
            "📌 Holat: kutilmoqda".replace(",", " "),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ YANA TO'LDIRISH", callback_data="topup")],
                [InlineKeyboardButton("⌂ BOSH SAHIFA", callback_data="home")],
            ])
        )

    elif data.startswith("gift:"):
        await select_gift(
            query,
            data.split(":", 1)[1],
            context.bot
        )


# ================= REPLY KEYBOARD BOSILGANDA =================
async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").strip()

    if text == "⭐ Yulduzlar":
        await update.message.reply_text(
            "⭐ YULDUZLAR\n\nPaketni tanlang:",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("⭐ 25", callback_data="star:25"),
                    InlineKeyboardButton("⭐ 50", callback_data="star:50"),
                ],
                [
                    InlineKeyboardButton("⭐ 100", callback_data="star:100"),
                    InlineKeyboardButton("⭐ 200", callback_data="star:200"),
                ],
                [
                    InlineKeyboardButton("⭐ 500", callback_data="star:500"),
                ],
            ])
        )

    elif text == "🎁 Sovg'alar":
        # Reply tugmasi bosilganda yangi xabar emas, bitta menyu ochiladi.
        await update.message.reply_text(
            "🎁 SOVG'ALAR\n\nSovg'alar ro'yxatini ochish uchun bosing:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🎁 SOVG'ALARNI OCHISH", callback_data="gift")]
            ])
        )

    elif text == "💎 Premium":
        await update.message.reply_text(
            "💎 PREMIUM\n\nMuddatni tanlang:",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("1 OY • 45 000", callback_data="prem:0"),
                    InlineKeyboardButton("3 OY • 164 000", callback_data="prem:1"),
                ],
                [
                    InlineKeyboardButton("6 OY • 222 000", callback_data="prem:2"),
                    InlineKeyboardButton("12 OY • 377 000", callback_data="prem:3"),
                ],
            ])
        )

    elif text == "💰 Mening balansim":
        await update.message.reply_text(
            f"💰 MENING BALANSIM\n\n"
            f"{get_balance(update.effective_user.id):,} so'm".replace(",", " "),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ HISOBNI TO'LDIRISH", callback_data="topup")]
            ])
        )

    elif text == "➕ Hisobimni to'ldirish":
        await update.message.reply_text(
            "➕ HISOBNI TO'LDIRISH\n\nSummani tanlang:",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("10 000", callback_data="topup:10000"),
                    InlineKeyboardButton("20 000", callback_data="topup:20000"),
                ],
                [
                    InlineKeyboardButton("50 000", callback_data="topup:50000"),
                    InlineKeyboardButton("100 000", callback_data="topup:100000"),
                ],
                [
                    InlineKeyboardButton("200 000", callback_data="topup:200000"),
                    InlineKeyboardButton("500 000", callback_data="topup:500000"),
                ],
            ])
        )

    elif text == "📦 Buyurtmalarim":
        user_id = update.effective_user.id
        con = db()
        rows = con.execute(
            "SELECT id,item,amount,status FROM orders "
            "WHERE user_id=? ORDER BY id DESC LIMIT 20",
            (user_id,)
        ).fetchall()
        con.close()

        if not rows:
            await update.message.reply_text(
                "📦 BUYURTMALARIM\n\n"
                "Hozircha hech qanday buyurtma yo'q. 😊"
            )
        else:
            lines = ["📦 BUYURTMALARIM\n"]
            for oid, item, amount, status in rows:
                lines.append(
                    f"№{oid} • {item}\n"
                    f"💳 {amount:,} so'm • 📌 {status}\n".replace(",", " ")
                )
            await update.message.reply_text("\n".join(lines))

    elif text == "👤 Kabinetim":
        user = update.effective_user
        username = f"@{user.username}" if user.username else "ko'rsatilmagan"
        await update.message.reply_text(
            "👤 KABINETIM\n\n"
            f"ID: {user.id}\n"
            f"Username: {username}\n"
            f"Balans: {get_balance(user.id):,} so'm".replace(",", " ")
        )

    elif text == "🔵 Ko'mak":
        await update.message.reply_text(
            "🔵 KO'MAK\n\n"
            f"Operator: {ADMIN}\n"
            "⏱ O'rtacha javob: 30 soniya"
        )

    elif text == "ℹ️ Biz haqimizda":
        await update.message.reply_text(
            "ℹ️ STARGIFT SHOP\n\n"
            "⭐ Stars • 🎁 Sovg'alar • 💎 Premium\n"
            "⚡ Tezkor • 🔐 Ishonchli • 💳 So'm"
        )

    else:
        await update.message.reply_text(
            "🌌 STARGIFT SHOP\n\n"
            "Pastdagi menyudan kerakli bo'limni tanlang.",
            reply_markup=main_keyboard()
        )


# ================= COMMANDS =================
async def 
