import os
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ContextTypes
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

TOPUP = [10000, 20000, 50000, 100000, 200000, 500000]
STAR_PACKS = [25, 50, 100, 125, 150, 175, 200, 300, 400, 500]


def db():
    con = sqlite3.connect("shop.db")
    con.execute(
        "CREATE TABLE IF NOT EXISTS users "
        "(user_id INTEGER PRIMARY KEY, balance INTEGER DEFAULT 0)"
    )
    con.execute(
        "CREATE TABLE IF NOT EXISTS orders "
        "(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, "
        "item TEXT, amount INTEGER, status TEXT)"
    )
    con.execute(
        "CREATE TABLE IF NOT EXISTS settings "
        "(name TEXT PRIMARY KEY, value TEXT)"
    )
    con.commit()
    return con


def get_balance(user_id):
    con = db()
    row = con.execute(
        "SELECT balance FROM users WHERE user_id=?", (user_id,)
    ).fetchone()

    if row is None:
        con.execute(
            "INSERT INTO users(user_id,balance) VALUES(?,0)", (user_id,)
        )
        con.commit()
        balance = 0
    else:
        balance = row[0]

    con.close()
    return balance


def main_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("⭐ Stars", callback_data="stars"),
            InlineKeyboardButton("🎁 Gift", callback_data="gift"),
            InlineKeyboardButton("💎 Premium", callback_data="premium"),
        ],
        [
            InlineKeyboardButton("💰 Balans", callback_data="balance"),
            InlineKeyboardButton("➕ Hisob to‘ldirish", callback_data="topup"),
            InlineKeyboardButton("👤 Profil", callback_data="profile"),
        ],
        [
            InlineKeyboardButton("📋 Buyurtmalarim", callback_data="orders"),
            InlineKeyboardButton("🔵 Yordam", callback_data="help"),
            InlineKeyboardButton("ℹ️ Ma'lumot", callback_data="info"),
        ],
        [
            InlineKeyboardButton("⚙️ Sozlamalar", callback_data="settings"),
        ],
    ])


def back_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ Orqaga", callback_data="back")]
    ])


def home_text():
    return (
        "╔══════════════════════╗\n"
        "     💙✨ STARGIFT SHOP ✨💙\n"
        "╚══════════════════════╝\n\n"
        "⭐ STARS   •   🎁 GIFTLAR   •   💎 PREMIUM\n\n"
        "⚡ Tez xizmat  •  🔐 Ishonchli  •  💳 So‘m\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🌟 Kerakli bo‘limni tanlang 👇\n"
        "━━━━━━━━━━━━━━━━━━━━━━"
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    image_path = "stargift_start.png"

    if os.path.exists(image_path):
        with open(image_path, "rb") as photo:
            await update.message.reply_photo(
                photo=photo,
                caption=home_text(),
                reply_markup=main_keyboard(),
            )
    else:
        await update.message.reply_text(
            home_text() + "\n\n⚠️ Rasm fayli topilmadi: stargift_start.png",
            reply_markup=main_keyboard(),
        )


async def orders_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    con = db()
    rows = con.execute(
        "SELECT id, item, amount, status FROM orders "
        "WHERE user_id=? ORDER BY id DESC LIMIT 10",
        (user_id,),
    ).fetchall()
    con.close()

    if not rows:
        await update.message.reply_text(
            "📋 BUYURTMALARIM\n\n"
            "🛍 Sizda hozircha buyurtma yo‘q.\n\n"
            "Buyurtma faqat to‘lov tasdiqlangandan keyin saqlanadi.",
            reply_markup=main_keyboard(),
        )
        return

    text = "📋 BUYURTMALARIM\n\n"
    for order_id, item, amount, status in rows:
        text += (
            f"📦 #{order_id}  •  {item}\n"
            f"💳 {amount:,} so‘m  •  📌 {status}\n\n"
        )

    await update.message.reply_text(text, reply_markup=main_keyboard())


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"🔵 YORDAM\n\n"
        f"Savol yoki muammo bo‘lsa:\n{ADMIN}\n\n"
        "⚡ O‘rtacha xizmat vaqti: 30 soniya",
        reply_markup=main_keyboard(),
    )


async def show_stars(query):
    rows = []
    row = []

    for n in STAR_PACKS:
        row.append(
            InlineKeyboardButton(
                f"⭐ {n} — {n * STAR_PRICE:,} so‘m",
                callback_data=f"star_{n}",
            )
        )
        if len(row) == 2:
            rows.append(row)
            row = []

    if row:
        rows.append(row)

    rows.append([InlineKeyboardButton("⬅️ Orqaga", callback_data="back")])

    await query.edit_message_caption(
        caption=(
            "╔════════════════════╗\n"
            "        ⭐ STARS\n"
            "╚════════════════════╝\n\n"
            "💙 1 Star = 195 so‘m\n\n"
            "📦 Paketni tanlang 👇"
        ),
        reply_markup=InlineKeyboardMarkup(rows),
    )


async def show_gifts(query, context):
    try:
        gifts = await context.bot.get_available_gifts()
    except Exception:
        await query.edit_message_caption(
            caption=(
                "🎁 GIFTLAR\n\n"
                "Hozircha Giftlarni yuklab bo‘lmadi.\n"
                "Birozdan keyin qayta urinib ko‘ring."
            ),
            reply_markup=back_keyboard(),
        )
        return

    if not gifts.gifts:
        await query.edit_message_caption(
            caption="🎁 GIFTLAR\n\nHozircha mavjud Gift topilmadi.",
            reply_markup=back_keyboard(),
        )
        return

    rows = []
    row = []

    for i, gift in enumerate(gifts.gifts):
        emoji = getattr(gift.sticker, "emoji", None) or "🎁"
        price = gift.star_count * STAR_PRICE

        row.append(
            InlineKeyboardButton(
                f"{emoji} {gift.star_count}⭐ • {price:,}",
                callback_data=f"gift_{gift.id}",
            )
        )

        if len(row) == 2:
            rows.append(row)
            row = []

        if i >= 49:
            break

    if row:
        rows.append(row)

    rows.append([InlineKeyboardButton("⬅️ Orqaga", callback_data="back")])

    await query.edit_message_caption(
        caption=(
            "╔════════════════════╗\n"
            "        🎁 GIFTLAR\n"
            "╚════════════════════╝\n\n"
            "✨ Mavjud Giftlar\n"
            "💳 Narxlar so‘mda\n\n"
            "👇 O‘zingizga yoqqanini tanlang"
        ),
        reply_markup=InlineKeyboardMarkup(rows),
    )


async def gift_selected(query, context):
    gift_id = query.data[len("gift_"):]

    try:
        gifts = await context.bot.get_available_gifts()
        gift = next((g for g in gifts.gifts if g.id == gift_id), None)

        if gift is None:
            await query.answer("Gift topilmadi.", show_alert=True)
            return

        emoji = getattr(gift.sticker, "emoji", None) or "🎁"
        price = gift.star_count * STAR_PRICE

        # Tanlangan Giftning haqiqiy stickerini ko‘rsatamiz.
        try:
            await context.bot.send_sticker(
                chat_id=query.message.chat_id,
                sticker=gift.sticker.file_id,
            )
        except Exception:
            pass

        await query.message.reply_text(
            "╔════════════════════╗\n"
            "       🎁 GIFT TANLANDI\n"
            "╚════════════════════╝\n\n"
            f"{emoji} Gift: {gift.star_count} Stars\n"
            f"💳 Narxi: {price:,} so‘m\n\n"
            "🔐 Buyurtma to‘lov tasdiqlangandan keyin saqlanadi.\n"
            "⚡ O‘rtacha bajarilish: 30 soniya",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🎁 Giftlarga qaytish", callback_data="gift")],
                [InlineKeyboardButton("🏠 Bosh sahifa", callback_data="back")],
            ]),
        )
        await query.answer()

    except Exception:
        await query.answer("Giftni olishda xatolik yuz berdi.", show_alert=True)


async def show_premium(query):
    rows = []

    for i, (period, price) in enumerate(PREMIUM):
        rows.append([
            InlineKeyboardButton(
                f"💎 {period}  •  {price:,} so‘m",
                callback_data=f"premium_{i}",
            )
        ])

    rows.append([InlineKeyboardButton("⬅️ Orqaga", callback_data="back")])

    await query.edit_message_caption(
        caption=(
            "╔════════════════════╗\n"
            "       💎 PREMIUM\n"
            "╚════════════════════╝\n\n"
            "✨ Premium muddatini tanlang 👇"
        ),
        reply_markup=InlineKeyboardMarkup(rows),
    )


async def show_balance(query):
    balance = get_balance(query.from_user.id)

    await query.edit_message_caption(
        caption=(
            "╔════════════════════╗\n"
            "         💰 BALANS\n"
            "╚════════════════════╝\n\n"
            f"💳 Sizning balansingiz:\n"
            f"✨ {balance:,} so‘m\n\n"
            "Hisobingizni istalgan payt to‘ldirishingiz mumkin."
        ),
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ Hisob to‘ldirish", callback_data="topup")],
            [InlineKeyboardButton("⬅️ Orqaga", callback_data="back")],
        ]),
    )


async def show_topup(query):
    rows = []
    row = []

    for amount in TOPUP:
        row.append(
            InlineKeyboardButton(
                f"💳 {amount:,} so‘m",
                callback_data=f"topup_{amount}",
            )
        )
        if len(row) == 2:
            rows.append(row)
            row = []

    if row:
        rows.append(row)

    rows.append([InlineKeyboardButton("⬅️ Orqaga", callback_data="back")])

    await query.edit_message_caption(
        caption=(
            "╔════════════════════╗\n"
            "    ➕ HISOB TO‘LDIRISH\n"
            "╚════════════════════╝\n\n"
            "💳 Kerakli summani tanlang 👇"
        ),
        reply_markup=InlineKeyboardMarkup(rows),
    )


async def show_orders(query):
    user_id = query.from_user.id
    con = db()
    rows = con.execute(
        "SELECT id, item, amount, status FROM orders "
        "WHERE user_id=? ORDER BY id DESC LIMIT 10",
        (user_id,),
    ).fetchall()
    con.close()

    if not rows:
        text = (
            "╔════════════════════╗\n"
            "      📋 BUYURTMALARIM\n"
            "╚════════════════════╝\n\n"
            "🛍 Sizda hozircha buyurtma yo‘q. 😊\n\n"
            "Buyurtma faqat to‘lov tasdiqlangandan keyin saqlanadi."
        )
    else:
        text = "📋 BUYURTMALARIM\n\n"
        for order_id, item, amount, status in rows:
            text += (
                f"📦 #{order_id}\n"
                f"🛍 {item}\n"
                f"💳 {amount:,} so‘m\n"
                f"📌 {status}\n\n"
            )

    await query.edit_message_caption(
        caption=text,
        reply_markup=back_keyboard(),
    )


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "back":
        await query.edit_message_caption(
            caption=home_text(),
            reply_markup=main_keyboard(),
        )

    elif data == "stars":
        await show_stars(query)

    elif data.startswith("star_"):
        n = int(data.split("_")[1])
        amount = n * STAR_PRICE

        # Hozircha faqat mahsulot ma'lumotini ko‘rsatadi.
        # To‘lov tasdiqlanmaguncha order DB ga yozilmaydi.
        await query.edit_message_caption(
            caption=(
                "⭐ STARS PAKETI\n\n"
                f"⭐ Miqdor: {n} Stars\n"
                f"💳 Narxi: {amount:,} so‘m\n\n"
                "🔐 To‘lov tasdiqlangandan keyin buyurtma yaratiladi."
            ),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⭐ Paketlarga qaytish", callback_data="stars")],
                [InlineKeyboardButton("🏠 Bosh sahifa", callback_data="back")],
            ]),
        )

    elif data == "gift":
        await show_gifts(query, context)

    elif data.startswith("gift_"):
        await gift_selected(query, context)

    elif data == "premium":
        await show_premium(query)

    elif data.startswith("premium_"):
        index = int(data.split("_")[1])
        period, price = PREMIUM[index]

        await query.edit_message_caption(
            caption=(
                "💎 PREMIUM TANLANDI\n\n"
                f"📅 Muddat: {period}\n"
                f"💳 Narxi: {price:,} so‘m\n\n"
                "🔐 To‘lov tasdiqlangandan keyin buyurtma saqlanadi."
            ),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("💎 Premiumga qaytish", callback_data="premium")],
                [InlineKeyboardButton("🏠 Bosh sahifa", callback_data="back")],
            ]),
        )

    elif data == "balance":
        await show_balance(query)

    elif data == "topup":
        await show_topup(query)

    elif data.startswith("topup_"):
        amount = int(data.split("_")[1])

        await query.edit_message_caption(
            caption=(
                "➕ HISOB TO‘LDIRISH\n\n"
                f"💳 Summa: {amount:,} so‘m\n\n"
                "🔐 To‘lov tasdiqlangandan keyin balansga qo‘shiladi.\n"
                "Hozircha buyurtma saqlanmaydi."
            ),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("💳 Summalarga qaytish", callback_data="topup")],
                [InlineKeyboardButton("🏠 Bosh sahifa", callback_data="back")],
            ]),
        )

    elif data == "profile":
        balance = get_balance(query.from_user.id)

        await query.edit_message_caption(
            caption=(
                "╔════════════════════╗\n"
                "          👤 PROFIL\n"
                "╚════════════════════╝\n\n"
                f"🆔 ID: {query.from_user.id}\n"
                f"💰 Balans: {balance:,} so‘m\n\n"
                "🌟 STARGIFT SHOP"
            ),
            reply_markup=back_keyboard(),
        )

    elif data == "help":
        await query.edit_message_caption(
            caption=(
                "╔════════════════════╗\n"
                "          🔵 YORDAM\n"
                "╚════════════════════╝\n\n"
                f"💬 Operator: {ADMIN}\n\n"
                "⚡ O‘rtacha javob/xizmat vaqti: 30 soniya"
            ),
            reply_markup=back_keyboard(),
        )

    elif data == "info":
        await query.edit_message_caption(
            caption=(
                "╔════════════════════╗\n"
                "       ℹ️ MA'LUMOT\n"
                "╚════════════════════╝\n\n"
                "💙 STARGIFT SHOP\n\n"
                "⭐ Stars\n"
                "🎁 Telegram Gifts\n"
                "💎 Premium\n\n"
                "⚡ Tez • 🔐 Ishonchli • 💳 So‘m\n"
                "⏱ O‘rtacha bajarilish: 30 soniya"
            ),
            reply_markup=back_keyboard(),
        )

    elif data == "orders":
        await show_orders(query)

    elif data == "settings":
        await query.edit_message_caption(
            caption=(
                "╔════════════════════╗\n"
                "       ⚙️ SOZLAMALAR\n"
                "╚════════════════════╝\n\n"
                "🌐 Til: O‘zbekcha\n"
                "💳 Valyuta: SO‘M\n"
                "🔔 Bildirishnomalar: Yoqilgan"
            ),
            reply_markup=back_keyboard(),
        )


async def post_init(app):
    await app.bot.set_my_commands([
        ("start", "🏠 Bosh sahifa"),
        ("orders", "📋 Buyurtmalarim"),
        ("help", "🔵 Yordam"),
    ])


def main():
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN topilmadi.")

    db()

    # Eski test buyurtmalarini faqat BIR MARTA tozalaydi.
    con = db()
    done = con.execute(
        "SELECT value FROM settings WHERE name='old_orders_cleared'"
    ).fetchone()

    if done is None:
        con.execute("DELETE FROM orders")
        con.execute(
            "INSERT INTO settings(name,value) VALUES('old_orders_cleared','1')"
        )
        con.commit()

    con.close()

    app = (
        Application.builder()
        .token(TOKEN)
        .post_init(post_init)
        .build()
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("orders", orders_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CallbackQueryHandler(button))

    app.run_polling()


if __name__ == "__main__":
    main()
                         
