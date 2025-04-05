
import logging
import os
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    ConversationHandler,
    filters,
)

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Состояния для ConversationHandler
ASK_USERNAME, ASK_PASSWORD = range(2)

# Путь к файлу с данными пользователей
USERS_FILE = "users.json"

# Загрузка пользователей
def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    return {}

# Сохранение пользователей
def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f)

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("🔐 Войти в Threads", callback_data="login")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Привет! Я помогу тебе отложенно постить в Threads.", reply_markup=reply_markup)

# Обработка кнопки "Войти в Threads"
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "login":
        await query.edit_message_text("Введите логин от Threads:")
        return ASK_USERNAME

# Получение логина
async def ask_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["username"] = update.message.text
    await update.message.reply_text("Теперь введите пароль от Threads:")
    return ASK_PASSWORD

# Получение пароля и завершение авторизации
async def ask_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    username = context.user_data.get("username")
    password = update.message.text

    users = load_users()
    users[user_id] = {"username": username, "password": password}
    save_users(users)

    await update.message.reply_text("✅ Авторизация сохранена! Скоро добавим планировщик.")
    return ConversationHandler.END

# Отмена
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Операция отменена.")
    return ConversationHandler.END

def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN не найден")

    app = ApplicationBuilder().token(token).build()

    # Conversation для логина
    login_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_handler)],
        states={
            ASK_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_username)],
            ASK_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_password)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    # Хэндлеры
    app.add_handler(CommandHandler("start", start))
    app.add_handler(login_conv)

    print("✅ Bot is running with login flow...")
    app.run_polling()

if __name__ == "__main__":
    main()
