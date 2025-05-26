import logging
from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    ContextTypes,
    CallbackContext
)
import os
from threading import Thread
from flask import Flask

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Конфигурация бота
class Config:
    BOT_TOKEN = "8146633102:AAFeSmP93aUa2DFV5zhaFF5X7oQNTj5B8gs"
    SHOP_NAME = "Balon Rails Shop"
    SUPPORT_USERNAME = "@Balon_Manager"
    REVIEWS_CHANNEL = "https://t.me/BalonRails"
    PAYMENT_DETAILS = "Сбербанк: 2202208334143592"
    CURRENCY_RATE = 0.20
    
    ACCOUNTS = {
        "Аккаунт(есть все)": "▪️▪️▪️",
        "Аккаунт с 5000бонд": "▪️▫️▪️▪️",
        "Аккаунт с 10000бонд": "▫️▪️▪️▪️",
        "Аккаунт с 15000бонд": "▪️▪️▪️▪️"
    }
    
    SERVICES = {
        "Все классы и поезда": "▪️▫️▪️",
        "80км за 5 минут": "▫️▫️▪️",
        "Фарм бонд.(с заходом на акк) 1бонд": "▫️.▫️▫️▪️"
    }

# Состояния диалога
class States:
    BUY, SERVICE, ACCOUNT, CURRENCY_AMOUNT = range(4)

# Хранение данных пользователей
class UserData:
    _data = {}
    
    @classmethod
    def get_purchases(cls, user_id: int) -> int:
        return cls._data.get(user_id, {}).get('purchases', 0)
    
    @classmethod
    def add_purchase(cls, user_id: int):
        if user_id not in cls._data:
            cls._data[user_id] = {'purchases': 0}
        cls._data[user_id]['purchases'] += 1

# Веб-сервер для Render
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

# Клавиатуры
class Keyboards:
    @staticmethod
    def main_menu():
        return ReplyKeyboardMarkup([
            ["Купить", "Отзывы"],
            ["Поддержка", "Профиль"]
        ], resize_keyboard=True)
    
    @staticmethod
    def buy_menu():
        return ReplyKeyboardMarkup([
            ["Услуги", "Аккаунты"],
            ["Назад"]
        ], resize_keyboard=True)
    
    @staticmethod
    def services_menu():
        return ReplyKeyboardMarkup(
            [[service] for service in Config.SERVICES.keys()] + [["Назад"]],
            resize_keyboard=True
        )
    
    @staticmethod
    def accounts_menu():
        return ReplyKeyboardMarkup(
            [[account] for account in Config.ACCOUNTS.keys()] + [["Назад"]],
            resize_keyboard=True
        )
    
    @staticmethod
    def cancel_menu():
        return ReplyKeyboardMarkup([["Отмена"]], resize_keyboard=True)
    
    @staticmethod
    def back_menu():
        return ReplyKeyboardMarkup([["Назад"]], resize_keyboard=True)

# Обработчики команд
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"Добро пожаловать в {Config.SHOP_NAME}! Выберите действие:",
        reply_markup=Keyboards.main_menu()
    )

async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Выберите категорию:",
        reply_markup=Keyboards.buy_menu()
    )
    return States.BUY

async def services(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Выберите услугу:",
        reply_markup=Keyboards.services_menu()
    )
    return States.SERVICE

async def accounts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Выберите аккаунт:",
        reply_markup=Keyboards.accounts_menu()
    )
    return States.ACCOUNT

async def handle_service(update: Update, context: ContextTypes.DEFAULT_TYPE):
    service = update.message.text
    if service == "Назад":
        return await buy(update, context)
    
    if service in Config.SERVICES:
        context.user_data['selected_service'] = service
        await update.message.reply_text(
            f"Вы выбрали: {service}\nВведите количество валюты:",
            reply_markup=Keyboards.cancel_menu()
        )
        return States.CURRENCY_AMOUNT
    
    await update.message.reply_text("Пожалуйста, выберите услугу из списка.")
    return States.SERVICE

async def handle_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    account = update.message.text
    
    if account == "Назад":
        return await buy(update, context)
    
    if account in Config.ACCOUNTS:
        UserData.add_purchase(update.message.from_user.id)
        
        await update.message.reply_text(
            f"Вы выбрали: {account}\n"
            f"Оплатите на реквизиты: {Config.PAYMENT_DETAILS}\n"
            "После оплаты отправьте скриншот.",
            reply_markup=Keyboards.back_menu()
        )
        return ConversationHandler.END
    
    await update.message.reply_text("Пожалуйста, выберите аккаунт из списка.")
    return States.ACCOUNT

async def handle_currency_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = int(update.message.text)
        service = context.user_data.get('selected_service')
        total_price = amount * Config.CURRENCY_RATE
        
        UserData.add_purchase(update.message.from_user.id)
        
        await update.message.reply_text(
            f"Вы заказали {amount} валюты ({service})\n"
            f"Сумма к оплате: {total_price:.2f}₽\n"
            f"Реквизиты для оплаты: {Config.PAYMENT_DETAILS}\n"
            "После оплаты отправьте скриншот.",
            reply_markup=Keyboards.back_menu()
        )
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("Пожалуйста, введите число.")
        return States.CURRENCY_AMOUNT

async def reviews(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Наши отзывы: {Config.REVIEWS_CHANNEL}")

async def support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Напишите нам в поддержку: {Config.SUPPORT_USERNAME}")

async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    purchases = UserData.get_purchases(user_id)
    await update.message.reply_text(f"Ваш ID: {user_id}\nКоличество покупок: {purchases}")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)
    return ConversationHandler.END

def main():
    # Запуск Flask в отдельном потоке
    Thread(target=run_flask, daemon=True).start()
    
    # Создание и настройка приложения бота
    application = ApplicationBuilder().token(Config.BOT_TOKEN).build()
    
    # Регистрация обработчиков
    application.add_handler(CommandHandler("start", start))
    
    # Обработчики главного меню
    application.add_handler(MessageHandler(filters.Regex('^(Купить)$'), buy))
    application.add_handler(MessageHandler(filters.Regex('^(Отзывы)$'), reviews))
    application.add_handler(MessageHandler(filters.Regex('^(Поддержка)$'), support))
    application.add_handler(MessageHandler(filters.Regex('^(Профиль)$'), profile))
    
    # Обработчик диалога покупки
    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^(Купить)$'), buy)],
        states={
            States.BUY: [
                MessageHandler(filters.Regex('^(Услуги)$'), services),
                MessageHandler(filters.Regex('^(Аккаунты)$'), accounts),
                MessageHandler(filters.Regex('^(Назад)$'), start),
            ],
            States.SERVICE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_service),
            ],
            States.ACCOUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_account),
            ],
            States.CURRENCY_AMOUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_currency_amount),
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    
    application.add_handler(conv_handler)
    
    # Запуск бота
    application.run_polling()

if __name__ == '__main__':
    main()
