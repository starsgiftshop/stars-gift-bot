import os
import sqlite3
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
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

# Narxlar
STAR_PRICE = 195

PREMIUM = [
    ("1 oy", 45000),
    ("3 oy", 164000),
    ("6 oy", 222000),
    ("12 oy", 377000),
]

TOPUPS = [10000, 20000, 50000, 100000, 200000, 500000]

# Yangi baza: eski test buyurtmalari bu bazaga o'tmaydi.
DB_FILE = "stargift_v2.db"

# GitHub/Railway ichida shu nomli rasm bo'lsa /start da chiqadi.
START_IMAGE = "stargift_start.png"


def money(amount: int) -> str:
    return f"{amount:,}".replace(",", " ")


def get_db():
    con = sqlite3.connect(DB_FILE)
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            balance INTEGER NOT NULL DEFAULT 0
        )
        """
    )
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            item TEXT NOT NULL,
            amount INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending'
        )
        """
    )
    con.commit()
    return con


def ensure_user(user_id: int):
    con = get_db()
    con.execute(
        "INSERT OR IGNORE INTO users(user_id, balance) VALUES(?, 0)",
        (user_id,),
    )
    con.commit()
    con.close()


def get_balance(user_id: int) -> int:
    ensure_user(user_id)
    con = get_db()
    row = con.execute(
        "SELECT balance FROM users WHERE user_id = ?",
        (user_id,),
    ).fetchone()
    con.close()
    return row[0] if row else 0


def create_order(user_id: int, item: str, amount: int) -> int:
    con = get_db()
    cur = con.execute(
        """
        INSERT INTO orders(user_id, item, amount, status)
        VALUES(?, ?, ?, 'pending')
        """,
        (user_id, item, amount),
    )
    con.commit()
    order_id = cur.lastrowid
    con.close()
    return order_id


def home_keyboard():
    # Pastki katta ReplyKeyboard YO'Q.
    # Faqat zamonaviy inline menyu.
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("⭐ Stars", callback_data="stars"),
                InlineKeyboardButton("🎁 Gifts", callback_data="gifts"),
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
                InlineKeyboardButton("👤 Profil", callback_data="profile"),
                InlineKeyboardButton("🔵 Yordam", callback_data="help"),
            ],
            [
                InlineKeyboardButton("ℹ️ Ma'lumot", callback_data="info"),
            ],
        ]
    )


def back_keyboard():
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("‹ Bosh sahifa", callback_data="home")]]
    )


async def setup_bot(app: Application):
    # Telegramdagi yuqoridagi/pastdagi 4 katakli MENU belgisi
    # komandalarni ochib turadi. ReplyKeyboard ishlatilmaydi.
    await app.bot.set_my_commands(
        [
            BotCommand("start", "Bosh sahifa"),
            BotCommand("services", "Bo'limlar"),
            BotCommand("balance", "Balansim"),
            BotCommand("orders", "Buyurtmalarim"),
            BotCommand("help", "Yordam"),
        ]
    )
    await app.bot.set_chat_menu_button(menu_button=MenuButtonCommands())


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    ensure_user(user.id)

    text = (
        "✦ STARGIFT SHOP ✦\n\n"
        "Xush kelibsiz! 🌟\n"
        "Stars, Gifts va Premium xizmatlari bir joyda.\n\n"
        "⚡ Tezkor xizmat   •   🔐 Ishonchli   •   💳 So'mda\n"
        "⏱ O'rtacha bajarilish vaqti: 30 soniya\n\n"
        "Kerakli bo'limni tanlang:"
    )

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


async def services(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✦ STARGIFT SHOP ✦\n\nKerakli bo'limni tanlang:",
        reply_markup=home_keyboard(),
    )


async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"💰 BALANS\n\n"
        f"Joriy balans: {money(get_balance(update.effective_user.id))} so'm",
        reply_markup=back_keyboard(),
    )


async def orders_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_orders(update.message, update.effective_user.id)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔵 YORDAM\n\n"
        "Savol yoki muammo bo'lsa, administratorga yozing:\n"
        f"{ADMIN}\n\n"
        "⏱ O'rtacha javob/bajarilish: 30 soniya.",
        reply_markup=back_keyboard(),
    )


async def show_orders(message, user_id: int):
    # MUHIM: faqat shu user_id ning buyurtmalari olinadi.
    con = get_db()
    rows = con.execute(
        """
        SELECT id, item, amount, status
        FROM orders
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT 30
        """,
        (user_id,),
    ).fetchall()
    con.close()

    if not rows:
        await message.edit_text(
            "📦 BUYURTMALARIM\n\n"
            "Hozircha hech qanday buyurtma bermagansiz. 😊\n\n"
            "Buyurtma berganingizdan keyin u faqat shu yerda "
            "sizga ko'rinadi.",
            reply_markup=back_keyboard(),
        )
        return

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

    await message.edit_text(text, reply_markup=back_keyboard())


async def stars_page(message):
    packages = [25, 50, 100, 125, 150, 175, 200, 300, 400, 500]
    rows = []

    for i in range(0, len(packages), 2):
        row = []
        for count in packages[i:i + 2]:
            row.append(
                InlineKeyboardButton(
                    f"⭐ {count} • {money(count * STAR_PRICE)} so'm",
                    callback_data=f"star:{count}",
                )
            )
        rows.append(row)

    rows.append(
        [InlineKeyboardButton("‹ Bosh sahifa", callback_data="home")]
    )

    await message.edit_text(
        "⭐ STARS\n\n"
        "Stars paketini tanlang.\n"
        "1 ⭐ = 195 so'm",
        reply_markup=InlineKeyboardMarkup(rows),
    )


async def premium_page(message):
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

    rows.append(
        [InlineKeyboardButton("‹ Bosh sahifa", callback_data="home")]
    )

    await message.edit_text(
        "💎 PREMIUM\n\n"
        "Premium muddatini tanlang:",
        reply_markup=InlineKeyboardMarkup(rows),
    )


async def topup_page(message):
    rows = []

    for i in range(0, len(TOPUPS), 2):
        row = []
        for amount in TOPUPS[i:i + 2]:
            row.append(
                InlineKeyboardButton(
                    f"💳 {money(amount)} so'm",
                    callback_data=f"top:{amount}",
                )
            )
        rows.append(row)

    rows.append(
        [InlineKeyboardButton("‹ Bosh sahifa", callback_data="home")]
    )

    await message.edit_text(
        "➕ HISOB TO'LDIRISH\n\n"
        "Kerakli summani tanlang.\n"
        "To'lov summalari so'mda.",
        reply_markup=InlineKeyboardMarkup(rows),
    )


async def gifts_page(message, context):
    try:
        result = await context.bot.get_available_gifts()
        gifts = list(result.gifts)
    except Exception as exc:
        print("GIFTS ERROR:", repr(exc))
        await message.edit_text(
            "🎁 GIFTS\n\n"
            "Sovg'alar ro'yxatini hozircha olish imkoni bo'lmadi.",
            reply_markup=back_keyboard(),
        )
        return

    if not gifts:
        await message.edit_text(
            "🎁 GIFTS\n\nHozircha mavjud sovg'a yo'q.",
            reply_markup=back_keyboard(),
        )
        return

    rows = []

    # 2 ustun: ekran tor bo'lsa ham chiroyli ko'rinadi.
    for i in range(0, min(len(gifts), 40), 2):
        row = []
        for gift in gifts[i:i + 2]:
            price = gift.star_count * STAR_PRICE

            # Bot API Gift obyektida "Uzuk/Ayiq" title maydoni yo'q.
            # Haqiqiy gift stickeri tanlanganda alohida yuboriladi.
            emoji = getattr(gift.sticker, "emoji", None) or "🎁"

            row.append(
                InlineKeyboardButton(
                    f"{emoji} {gift.star_count}⭐ • {money(price)} so'm",
                    callback_data=f"gift:{gift.id}",
                )
            )
        rows.append(row)

    rows.append(
        [InlineKeyboardButton("‹ Bosh sahifa", callback_data="home")]
    )

    await message.edit_text(
        "🎁 GIFTS\n\n"
        "Sovg'ani tanlang.\n"
        "Tanlaganingizda uning haqiqiy Telegram rasmi/stickeri chiqadi.",
        reply_markup=InlineKeyboardMarkup(rows),
    )


async def profile_page(message, user):
    username = f"@{user.username}" if user.username else "username yo'q"

    await message.edit_text(
        "👤 PROFIL\n\n"
        f"Username: {username}\n"
        f"ID: {user.id}\n"
        f"💰 Balans: {money(get_balance(user.id))} so'm",
        reply_markup=back_keyboard(),
    )


async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data or ""
    user = query.from_user
    ensure_user(user.id)

    try:
        if data == "home":
            await query.edit_message_text(
                "✦ STARGIFT SHOP ✦\n\n"
                "Kerakli bo'limni tanlang:",
                reply_markup=home_keyboard(),
            )

        elif data == "stars":
            await stars_page(query.message)

        elif data == "gifts":
            await gifts_page(query.message, context)

        elif data == "premium":
            await premium_page(query.message)

        elif data == "balance":
            await query.edit_message_text(
                "💰 BALANS\n\n"
                f"Joriy balans: {money(get_balance(user.id))} so'm",
                reply_markup=back_keyboard(),
            )

        elif data == "topup":
            await topup_page(query.message)

        elif data == "orders":
            await show_orders(query.message, user.id)

        elif data == "profile":
            await profile_page(query.message, user)

        elif data == "help":
            await query.edit_message_text(
                "🔵 YORDAM\n\n"
                f"Administrator: {ADMIN}\n\n"
                "Savol bo'lsa yozing.",
                reply_markup=back_keyboard(),
            )

        elif data == "info":
            await query.edit_message_text(
                "ℹ️ MA'LUMOT\n\n"
                "✦ STARGIFT SHOP\n"
                "⭐ Stars\n"
                "🎁 Telegram Gifts\n"
                "💎 Premium\n\n"
                "💳 Narxlar so'mda.\n"
                "⏱ O'rtacha bajarilish: 30 soniya.",
                reply_markup=back_keyboard(),
            )

        elif data.startswith("star:"):
            count = int(data.split(":", 1)[1])
            amount = count * STAR_PRICE
            order_id = create_order(
                user.id,
                f"{count} Stars",
                amount,
            )

            await query.edit_message_text(
                "⭐ STARS BUYURTMASI\n\n"
                f"Stars: {count} ⭐\n"
                f"Narx: {money(amount)} so'm\n"
                f"Buyurtma: №{order_id}\n"
                "Holat: ⏳ Kutilmoqda\n\n"
                "To'lov tasdiqlangach buyurtma bajariladi.",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "📦 Buyurtmam",
                                callback_data="orders",
                            )
                        ],
                        [
                            InlineKeyboardButton(
                                "‹ Bosh sahifa",
                                callback_data="home",
                            )
                        ],
                    ]
                ),
            )

        elif data.startswith("prem:"):
            index = int(data.split(":", 1)[1])
            name, amount = PREMIUM[index]
            order_id = create_order(
                user.id,
                f"Premium {name}",
                amount,
            )

            await query.edit_message_text(
                "💎 PREMIUM BUYURTMASI\n\n"
                f"Muddat: {name}\n"
                f"Narx: {money(amount)} so'm\n"
                f"Buyurtma: №{order_id}\n"
                "Holat: ⏳ Kutilmoqda\n\n"
                "To'lov tasdiqlangach buyurtma bajariladi.",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "📦 Buyurtmam",
                                callback_data="orders",
                            )
                        ],
                        [
                            InlineKeyboardButton(
                                "‹ Bosh sahifa",
                                callback_data="home",
                            )
                        ],
                    ]
                ),
            )

        elif data.startswith("top:"):
            amount = int(data.split(":", 1)[1])
            order_id = create_order(
                user.id,
                "Hisob to'ldirish",
                amount,
            )

            await query.edit_message_text(
                "➕ HISOB TO'LDIRISH\n\n"
                f"Summa: {money(amount)} so'm\n"
                f"Buyurtma: №{order_id}\n"
                "Holat: ⏳ Kutilmoqda\n\n"
                "To'lov tizimi ulanishi bilan avtomatik tasdiqlanadi.",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "📦 Buyurtmam",
                                callback_data="orders",
                            )
                        ],
                        [
                            InlineKeyboardButton(
                                "‹ Bosh sahifa",
                                callback_data="home",
                            )
                        ],
                    ]
                ),
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

            # Buyurtma aynan shu odamga yoziladi.
            order_id = create_order(
                user.id,
                f"Telegram Gift ({gift.star_count} Stars)",
                amount,
            )

            # Haqiqiy gift rasmi/stickeri.
            await query.message.reply_sticker(
                gift.sticker.file_id
            )

            await query.message.reply_text(
                "🎁 TANLANGAN GIFT\n\n"
                f"⭐ Qiymati: {gift.star_count} Stars\n"
                f"💳 Narxi: {money(amount)} so'm\n"
                f"📦 Buyurtma: №{order_id}\n"
                "⏳ Holat: Kutilmoqda",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "🎁 Yana gift",
                                callback_data="gifts",
                            ),
                            InlineKeyboardButton(
                                "📦 Buyurtmam",
                                callback_data="orders",
                            ),
                        ],
                        [
                            InlineKeyboardButton(
                                "‹ Bosh sahifa",
                                callback_data="home",
                            )
                        ],
                    ]
                ),
            )

    except Exception as exc:
        print("CALLBACK ERROR:", repr(exc))
        try:
            await query.message.reply_text(
                "⚠️ Xatolik yuz berdi. Qaytadan urinib ko'ring.",
                reply_markup=back_keyboard(),
            )
        except Exception:
            pass


def main():
    if not TOKEN:
        raise RuntimeError(
            "BOT_TOKEN topilmadi. Railway Variables ichiga BOT_TOKEN qo'ying."
        )

    app = (
        Application.builder()
        .token(TOKEN)
        .post_init(setup_bot)
        .build()
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("services", services))
    app.add_handler(CommandHandler("balance", balance_command))
    app.add_handler(CommandHandler("orders", orders_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CallbackQueryHandler(callback))

    print("STARGIFT SHOP BOT IS RUNNING")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
    
