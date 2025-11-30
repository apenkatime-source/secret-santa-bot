import random
from telegram import (
    Update, 
    InlineKeyboardButton, 
    InlineKeyboardMarkup, 
    ReplyKeyboardMarkup, 
    KeyboardButton,
    InputSticker
)
from telegram.ext import (
    ApplicationBuilder, 
    CommandHandler, 
    CallbackContext,
    MessageHandler,
    CallbackQueryHandler,
    filters
)

# ====== НАСТРОЙКИ ======
ADMIN_USERNAME = "penk_a3"
BOT_TOKEN = os.getenv("BOT_TOKEN")
BUDGET_TEXT = "🎁 Бюджет подарка: 25–30р (но не ограничен)"
# =======================

participants = {}  # user_id: {"name": "...", "wishes": "..."}


# --- Команда /start ---
async def start(update: Update, context: CallbackContext):
    user = update.effective_user

    keyboard = [
        [KeyboardButton("🎄 Участвовать")],
        [KeyboardButton("ℹ Показать бюджет")]
    ]
    reply_kb = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_sticker("CAACAgIAAxkBAAEIu_RlZsHw2pE18dQ")  # весёлый стикер (Telegram сам заменит)
    await update.message.reply_text(
        f"Привет, {user.first_name}! 🎅\n"
        f"Добро пожаловать в *Тайного Санту*!",
        parse_mode="Markdown",
        reply_markup=reply_kb
    )


# --- БЮДЖЕТ ---
async def budget(update: Update, context: CallbackContext):
    await update.message.reply_text(BUDGET_TEXT)


# --- УЧАСТИЕ ---
async def participate(update: Update, context: CallbackContext):
    user = update.effective_user

    await update.message.reply_animation("https://media.giphy.com/media/du3J3cXyzhj75IOgvA/giphy.gif")
    await update.message.reply_text(
        "Отлично! 🎄\nНапиши, пожалуйста, свои пожелания к подарку.\n"
        "_Если пожеланий нет — так и напиши:_ «нет»",
        parse_mode="Markdown"
    )

    context.user_data["waiting_wishes"] = True


# --- СБОР ПОЖЕЛАНИЙ ---
async def wishes(update: Update, context: CallbackContext):
    if not context.user_data.get("waiting_wishes"):
        return

    user = update.effective_user
    wish = update.message.text

    participants[user.id] = {
        "name": user.full_name,
        "wishes": wish
    }

    context.user_data["waiting_wishes"] = False

    await update.message.reply_sticker("CAACAgIAAxkBAAEIu_5lZsIWBXfD1F1w")
    await update.message.reply_text(
        "Ты успешно зарегистрирован! 🎅\n"
        "Жди жеребьёвки 😊"
    )


# --- СПИСОК УЧАСТНИКОВ (только админ) ---
async def list_participants(update: Update, context: CallbackContext):
    if update.effective_user.username != ADMIN_USERNAME:
        return

    if not participants:
        await update.message.reply_text("Пока никто не участвует 🥲")
        return

    text = "🎄 *Список участников:*\n\n"
    for p in participants.values():
        text += f"• {p['name']} — пожелания: “{p['wishes']}”\n"

    await update.message.reply_text(text, parse_mode="Markdown")


# --- ЖЕРЕБЬЁВКА ---
async def draw(update: Update, context: CallbackContext):
    if update.effective_user.username != ADMIN_USERNAME:
        return

    if len(participants) < 2:
        await update.message.reply_text("Недостаточно участников для жеребьёвки.")
        return

    user_ids = list(participants.keys())
    receivers = user_ids.copy()

    # Перетасовка без совпадения с самим собой
    while True:
        random.shuffle(receivers)
        if all(u != r for u, r in zip(user_ids, receivers)):
            break

    # Рассылка
    for giver, receiver in zip(user_ids, receivers):
        rec_data = participants[receiver]
        await context.bot.send_message(
            chat_id=giver,
            text=(
                "🎅 *Жеребьёвка состоялась!* 🎄\n\n"
                f"Ты даришь подарок: *{rec_data['name']}*\n\n"
                f"Пожелания: “{rec_data['wishes']}”"
            ),
            parse_mode="Markdown"
        )

    await update.message.reply_text("🎉 Жеребьёвка завершена! Все участники получили сообщения.")


# --- ГЛАВНЫЙ ХЕНДЛЕР ---
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("list", list_participants))
    app.add_handler(CommandHandler("draw", draw))

    app.add_handler(MessageHandler(filters.Regex("ℹ Показать бюджет"), budget))
    app.add_handler(MessageHandler(filters.Regex("🎄 Участвовать"), participate))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, wishes))

    print("Bot started!")
    app.run_polling()


if __name__ == "__main__":
    main()
