async def show_gifts(query, context):
    try:
        result = await context.bot.get_available_gifts()

        if not result or not result.gifts:
            await query.edit_message_text(
                "🎁 Hozircha Gift mavjud emas.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("◀️ Orqaga", callback_data="back")]
                ])
            )
            return

        gifts = result.gifts[:30]

        text = "🎁 <b>Giftlar</b>\n\n"
        entities = []

        # HTML teglarini hisobga olmasdan,
        # custom emoji joylashuvini alohida yig‘amiz.
        current_offset = len(text.encode("utf-16-le")) // 2

        buttons = []

        for index, gift in enumerate(gifts, 1):
            stars = gift.star_count
            price = gift_price(stars)

            sticker = gift.sticker

            if (
                sticker.type == "custom_emoji"
                and sticker.custom_emoji_id
                and sticker.emoji
            ):
                emoji = sticker.emoji

                line = (
                    f"{emoji} Gift {index} — "
                    f"{stars}⭐ | {price:,} so‘m\n"
                ).replace(",", " ")

                emoji_offset = current_offset

                entities.append(
                    MessageEntity(
                        type=MessageEntity.CUSTOM_EMOJI,
                        offset=emoji_offset,
                        length=len(
                            emoji.encode("utf-16-le")
                        ) // 2,
                        custom_emoji_id=sticker.custom_emoji_id,
                    )
                )

            else:
                line = (
                    f"🎁 Gift {index} — "
                    f"{stars}⭐ | {price:,} so‘m\n"
                ).replace(",", " ")

            text += line

            current_offset += (
                len(line.encode("utf-16-le")) // 2
            )

            buttons.append([
                InlineKeyboardButton(
                    f"Gift {index} — {stars}⭐",
                    callback_data=f"gift:{gift.id}"
                )
            ])

        buttons.append([
            InlineKeyboardButton(
                "◀️ Orqaga",
                callback_data="back"
            )
        ])

        await query.edit_message_text(
            text,
            parse_mode="HTML",
            entities=entities,
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    except Exception as e:
        print("GIFTS ERROR:", repr(e))

        try:
            await query.edit_message_text(
                "❌ Giftlarni yuklashda xatolik.",
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton(
                            "◀️ Orqaga",
                            callback_data="back"
                        )
                    ]
                ])
            )
        except Exception:
            pass
