import telebot
from telebot import types
import random
import logging
import os

# --------------------------------------------
# НАСТРОЙКИ
# --------------------------------------------
BOT_TOKEN = os.getenv("BOT_TOKEN")  # Render переменная окружения
ADMIN_ID = 338271592                # твой Telegram ID

bot = telebot.TeleBot(BOT_TOKEN)

# --------------------------------------------
# ЛОГИРОВАНИЕ
# --------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# --------------------------------------------
# ДАННЫЕ (в ОЗУ, без базы)
# --------------------------------------------
participants = {}      # user_id: {"name": str, "wish": str}
assignments = {}       # user_id: whom_to_gift_id

# --------------------------------------------
# СТИКЕРЫ / АНИМАЦИИ
# --------------------------------------------
WELCOME_STICKER = "CAACAgIAAxkBAAEBx9hmBYsQKqk5WmHuu9Bd39WmQ5cCsAACswIAAuXjqUs4Q3NbQobRQTUE"
GIFT_ANIMATION = "https://media.giphy.com/media/26u4cqiYI30juCOGY/giphy.gif"
DRAW_ANIMATION = "https://media.giphy.com/media/l0HlNQ03J5JxX6lva/giphy.gif"


# -----------------------------------------------------
# КРАСИВОЕ ГЛАВНОЕ МЕНЮ
# -----------------------------------------------------
def main_menu():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("🎁 Участвовать")
    btn2 = types.KeyboardButton("📝 Мои данные")
    btn3 = types.KeyboardButton("🎅 Кому я дарю?")
    btn4 = types.KeyboardButton("📋 Список участников")  # новая кнопка
    keyboard.add(btn1)
    keyboard.add(btn2)
    keyboard.add(btn3)
    keyboard.add(btn4)
    return keyboard


# -----------------------------------------------------
# АДМИН-МЕНЮ
# -----------------------------------------------------
def admin_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("📋 Полный список участников", "🔄 Запустить жеребьёвку")
    kb.add("❌ Удалить участника", "💬 Логи")
    kb.add("⬅️ Назад")
    return kb


# -----------------------------------------------------
# /start
# -----------------------------------------------------
@bot.message_handler(commands=["start"])
def start(msg):
    bot.send_sticker(msg.chat.id, WELCOME_STICKER)
    bot.send_animation(msg.chat.id, GIFT_ANIMATION)
    bot.send_message(
        msg.chat.id,
        "🎄 **Добро пожаловать в Тайного Санту!** 🎅\n\n"
        "Нажимай «🎁 Участвовать», чтобы присоединиться!",
        parse_mode="Markdown",
        reply_markup=main_menu()
    )


# -----------------------------------------------------
# УЧАСТИЕ
# -----------------------------------------------------
@bot.message_handler(func=lambda m: m.text == "🎁 Участвовать")
def participate(msg):
    user_id = msg.from_user.id

    if user_id in participants:
        bot.send_message(user_id, "❗ Ты уже зарегистрирован!")
        return

    bot.send_message(
        user_id,
        "🎁 Отлично!\n\nНапиши, пожалуйста, **своё имя и фамилию**"
    )
    bot.register_next_step_handler(msg, save_name)


def save_name(msg):
    name = msg.text.strip()
    user_id = msg.from_user.id

    participants[user_id] = {"name": name, "wish": ""}

    bot.send_message(
        user_id,
        "✨ Отлично! Теперь напиши свои пожелания к подарку.\n"
        "_Если пожеланий нет — просто напиши «нет»._",
        parse_mode="Markdown"
    )
    bot.register_next_step_handler(msg, save_wish)


def save_wish(msg):
    wish = msg.text.strip()
    user_id = msg.from_user.id

    participants[user_id]["wish"] = wish

    bot.send_animation(user_id, GIFT_ANIMATION)
    bot.send_message(
        user_id,
        "🎉 Ты успешно зарегистрирован!\n\n"
        "**Бюджет: 25–30 рублей, но не ограничен.**",
        parse_mode="Markdown",
        reply_markup=main_menu()
    )

    logging.info(f"USER REGISTERED: {user_id} ({participants[user_id]})")


# -----------------------------------------------------
# МОИ ДАННЫЕ
# -----------------------------------------------------
@bot.message_handler(func=lambda m: m.text == "📝 Мои данные")
def my_data(msg):
    user_id = msg.from_user.id
    if user_id not in participants:
        bot.send_message(user_id, "❗ Ты ещё не зарегистрирован.")
        return

    data = participants[user_id]

    bot.send_message(
        user_id,
        f"📝 *Твои данные:*\n\n"
        f"👤 Имя: {data['name']}\n"
        f"🎀 Пожелания: {data['wish']}",
        parse_mode="Markdown"
    )


# -----------------------------------------------------
# ПРОВЕРИТЬ, КОМУ ДАРЮ
# -----------------------------------------------------
@bot.message_handler(func=lambda m: m.text == "🎅 Кому я дарю?")
def who_i_gift(msg):
    user_id = msg.from_user.id

    if user_id not in assignments:
        bot.send_message(user_id, "🎁 Жеребьёвка ещё не проведена!")
        return

    target_id = assignments[user_id]
    target = participants[target_id]

    bot.send_message(
        user_id,
        f"🎅 Ты даришь подарок:\n\n"
        f"👤 *{target['name']}*\n"
        f"🎀 Пожелания: {target['wish']}",
        parse_mode="Markdown"
    )


# -----------------------------------------------------
# СПИСОК УЧАСТНИКОВ (только ИМЕНА)
# -----------------------------------------------------
@bot.message_handler(func=lambda m: m.text == "📋 Список участников")
def show_participants(msg):
    if not participants:
        bot.send_message(msg.chat.id, "Пока никто не зарегистрирован 🥲")
        return

    text = "🎄 *Список участников:*\n\n"
    for data in participants.values():
        text += f"• {data['name']}\n"

    bot.send_message(msg.chat.id, text, parse_mode="Markdown")


# -----------------------------------------------------
# АДМИН — ВХОД
# -----------------------------------------------------
@bot.message_handler(commands=["admin"])
def admin(msg):
    if msg.from_user.id != ADMIN_ID:
        bot.send_message(msg.chat.id, "❌ У тебя нет доступа.")
        return

    bot.send_message(msg.chat.id, "🔧 Админ-панель:", reply_markup=admin_menu())


# -----------------------------------------------------
# АДМИН — ПОЛНЫЙ СПИСОК
# -----------------------------------------------------
@bot.message_handler(func=lambda m: m.text == "📋 Полный список участников")
def admin_list(msg):
    if msg.from_user.id != ADMIN_ID:
        return

    if not participants:
        bot.send_message(msg.chat.id, "Список пуст.")
        return

    text = "📋 *Участники:*\n\n"
    for uid, data in participants.items():
        text += f"{data['name']} — {uid} — Пожелания: {data['wish']}\n"

    bot.send_message(msg.chat.id, text, parse_mode="Markdown")


# -----------------------------------------------------
# АДМИН — УДАЛЕНИЕ
# -----------------------------------------------------
@bot.message_handler(func=lambda m: m.text == "❌ Удалить участника")
def admin_delete(msg):
    if msg.from_user.id != ADMIN_ID:
        return

    bot.send_message(
        msg.chat.id,
        "Введи *ID участника*, которого нужно удалить:",
        parse_mode="Markdown"
    )
    bot.register_next_step_handler(msg, admin_delete_do)


def admin_delete_do(msg):
    if msg.from_user.id != ADMIN_ID:
        return

    try:
        uid = int(msg.text)
        if uid in participants:
            del participants[uid]
            bot.send_message(msg.chat.id, "Удалён.")
        else:
            bot.send_message(msg.chat.id, "ID не найден.")
    except:
        bot.send_message(msg.chat.id, "Неверный формат ID.")


# -----------------------------------------------------
# АДМИН — ЛОГИ
# -----------------------------------------------------
@bot.message_handler(func=lambda m: m.text == "💬 Логи")
def admin_logs(msg):
    if msg.from_user.id != ADMIN_ID:
        return
    bot.send_message(msg.chat.id, "Логи хранятся в консоли Render.")


# -----------------------------------------------------
# АДМИН — ЖЕРЕБЬЁВКА
# -----------------------------------------------------
@bot.message_handler(func=lambda m: m.text == "🔄 Запустить жеребьёвку")
def run_draw(msg):
    if msg.from_user.id != ADMIN_ID:
        return

    if len(participants) < 2:
        bot.send_message(msg.chat.id, "Недостаточно участников.")
        return

    bot.send_animation(msg.chat.id, DRAW_ANIMATION)
    bot.send_message(msg.chat.id, "🎲 Провожу жеребьёвку...")

    users = list(participants.keys())
    targets = users.copy()

    while True:
        random.shuffle(targets)
        if all(u != t for u, t in zip(users, targets)):
            break

    for u, t in zip(users, targets):
        assignments[u] = t
        bot.send_message(
            u,
            "🎅 *Жеребьёвка прошла!* Вот кому ты даришь подарок:",
            parse_mode="Markdown"
        )
        # отправка сразу деталей
        target = participants[t]
        bot.send_message(
            u,
            f"👤 *{target['name']}*\n🎀 Пожелания: {target['wish']}",
            parse_mode="Markdown"
        )

    bot.send_message(msg.chat.id, "✔ Готово! Рассылка выполнена.")
    logging.info("DRAW COMPLETED: assignments = %s", assignments)


# -----------------------------------------------------
# НАЗАД В МЕНЮ
# -----------------------------------------------------
@bot.message_handler(func=lambda m: m.text == "⬅️ Назад")
def back(msg):
    if msg.from_user.id != ADMIN_ID:
        return
    bot.send_message(msg.chat.id, "Возвращаюсь...", reply_markup=main_menu())


# -----------------------------------------------------
# ЗАПУСК
# -----------------------------------------------------
bot.infinity_polling()
