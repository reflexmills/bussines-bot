import logging
from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    ContextTypes
)
import os
from threading import Thread
from flask import Flask
from dotenv import load_dotenv
import asyncio
import time
from datetime import datetime
import requests

def keep_alive():
    """
    Отправляет запросы каждые 5 минут, чтобы бот не засыпал на Render.
    """
    while True:
        try:
            # Замените URL на ваш (должен начинаться с https://)
            url = "https://bussines-bot-telegq.onrender.com"  
            response = requests.get(url)
            print(f"Keep-alive запрос отправлен. Статус: {response.status_code}")
        except Exception as e:
            print(f"Ошибка keep-alive: {e}")
        time.sleep(300)  # Интервал 5 минут (300 секунд)

# Запуск в отдельном потоке
Thread(target=keep_alive, daemon=True).start()

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Конфигурация бота
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден в переменных окружения")

class Config:
    SHOP_NAME = "🚂 Balon Rails Shop | Premium магазин для Dead Rails"
    SUPPORT_USERNAME = "@Balon_Manager"
    REVIEWS_CHANNEL = "https://t.me/BalonRails"
    PAYMENT_DETAILS = "Сбербанк: 2202208334143592"
    
    # Услуги с ценами и описанием
    SERVICES = {
        "Все классы и поезда - 90₽": {
            "price": 90,
            "emoji": "▪️▫️▪️",
            "desc": "Полный доступ ко всем классам и поездам"
        },
        "80км за 5 минут - 40₽": {
            "price": 40,
            "emoji": "▫️▫️▪️",
            "desc": "Быстрое продвижение в игре"
        },
        "Фарм бонд (с заходом на акк)": {
            "price": 0.20,
            "emoji": "▫️.▫️▫️▪️",
            "desc": "1 бонд = 0.20₽ (указать количество)"
        }
    }
    
    # Аккаунты с ценами и описанием
    ACCOUNTS = {
        "Аккаунт (есть все) - 79₽": {
            "price": 79,
            "emoji": "▪️▪️▪️",
            "desc": "Аккаунт с полным доступом"
        },
        "Аккаунт с 5000 бонд - 169₽": {
            "price": 169,
            "emoji": "▪️▫️▪️▪️",
            "desc": "Аккаунт + 5000 бондов"
        },
        "Аккаунт с 10000 бонд - 299₽": {
            "price": 299,
            "emoji": "▫️▪️▪️▪️",
            "desc": "Аккаунт + 10000 бондов"
        },
        "Аккаунт с 15000 бонд - 399₽": {
            "price": 399,
            "emoji": "▪️▪️▪️▪️",
            "desc": "Аккаунт + 15000 бондов"
        }
    }

# Состояния диалога
class States:
    BUY, SERVICE, ACCOUNT, CURRENCY_AMOUNT = range(4)

# Хранение данных пользователей
class UserData:
    _data = {}
    
    @classmethod
    def get_user(cls, user_id: int):
        if user_id not in cls._data:
            cls._data[user_id] = {
                'purchases': 0,
                'first_purchase': None,
                'last_purchase': None
            }
        return cls._data[user_id]
    
    @classmethod
    def add_purchase(cls, user_id: int):
        user = cls.get_user(user_id)
        user['purchases'] += 1
        now = datetime.now().strftime("%d.%m.%Y %H:%M")
        if not user['first_purchase']:
            user['first_purchase'] = now
        user['last_purchase'] = now

# Клавиатуры
class Keyboards:
    @staticmethod
    def main_menu():
        return ReplyKeyboardMarkup([
            ["🛒 Купить", "⭐ Отзывы"],
            ["🆘 Поддержка", "👤 Мой профиль"]
        ], resize_keyboard=True)
    
    @staticmethod
    def buy_menu():
        return ReplyKeyboardMarkup([
            ["🎮 Услуги", "👥 Аккаунты"],
            ["🔙 Назад"]
        ], resize_keyboard=True)
    
    @staticmethod
    def services_menu():
        return ReplyKeyboardMarkup(
            [[service] for service in Config.SERVICES.keys()] + [["🔙 Назад"]],
            resize_keyboard=True
        )
    
    @staticmethod
    def accounts_menu():
        return ReplyKeyboardMarkup(
            [[account] for account in Config.ACCOUNTS.keys()] + [["🔙 Назад"]],
            resize_keyboard=True
        )
    
    @staticmethod
    def cancel_menu():
        return ReplyKeyboardMarkup([["❌ Отмена"]], resize_keyboard=True)
    
    @staticmethod
    def back_menu():
        return ReplyKeyboardMarkup([["🔙 Назад"]], resize_keyboard=True)
    
    @staticmethod
    def back_to_main_menu():
        return ReplyKeyboardMarkup([["🔙 В главное меню"]], resize_keyboard=True)

# Веб-сервер для Render
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))

# Обработчики команд
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"""🌟 <b>Добро пожаловать в {Config.SHOP_NAME}!</b> 🌟

Здесь вы можете приобрести игровые ценности для Rail Nation.

Выберите действие:""",
        parse_mode='HTML',
        reply_markup=Keyboards.main_menu()
    )
    return ConversationHandler.END

async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        """🛒 <b>Меню покупок</b>

Выберите категорию товаров:""",
        parse_mode='HTML',
        reply_markup=Keyboards.buy_menu()
    )
    return States.BUY

async def handle_buy_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if "Услуги" in text:
        await update.message.reply_text(
            """🎮 <b>Доступные услуги</b>

Выберите нужную услугу:""",
            parse_mode='HTML',
            reply_markup=Keyboards.services_menu()
        )
        return States.SERVICE
    elif "Аккаунты" in text:
        await update.message.reply_text(
            """👥 <b>Доступные аккаунты</b>

Выберите нужный аккаунт:""",
            parse_mode='HTML',
            reply_markup=Keyboards.accounts_menu()
        )
        return States.ACCOUNT
    elif "Назад" in text:
        await start(update, context)
        return ConversationHandler.END
    
    await update.message.reply_text("Пожалуйста, используйте кнопки меню")
    return States.BUY

async def handle_service(update: Update, context: ContextTypes.DEFAULT_TYPE):
    service = update.message.text
    
    if "Назад" in service:
        await buy(update, context)
        return States.BUY
    
    if service in Config.SERVICES:
        service_info = Config.SERVICES[service]
        if "Фарм бонд" in service:
            context.user_data['selected_service'] = {
                'name': service,
                'price': service_info['price'],
                'type': 'bond'
            }
            await update.message.reply_text(
                """💵 <b>Фарм бондов</b>

1 бонд = 0.20₽
Введите количество бондов, которое хотите приобрести:""",
                parse_mode='HTML',
                reply_markup=Keyboards.cancel_menu()
            )
            return States.CURRENCY_AMOUNT
        else:
            await update.message.reply_text(
                f"""✅ <b>Вы выбрали:</b> {service}
📝 {service_info['desc']}

💸 <b>Цена:</b> {service_info['price']}₽

📌 <b>Реквизиты для оплаты:</b>
{Config.PAYMENT_DETAILS}

После оплаты отправьте скриншот в этот чат.""",
                parse_mode='HTML',
                reply_markup=Keyboards.back_to_main_menu()
            )
            UserData.add_purchase(update.message.from_user.id)
            return ConversationHandler.END
    
    await update.message.reply_text("Пожалуйста, выберите услугу из списка.")
    return States.SERVICE

async def handle_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    account = update.message.text
    
    if "Назад" in account:
        await buy(update, context)
        return States.BUY
    
    if account in Config.ACCOUNTS:
        account_info = Config.ACCOUNTS[account]
        await update.message.reply_text(
            f"""✅ <b>Вы выбрали:</b> {account}
📝 {account_info['desc']}

💸 <b>Цена:</b> {account_info['price']}₽

📌 <b>Реквизиты для оплаты:</b>
{Config.PAYMENT_DETAILS}

После оплаты отправьте скриншот в этот чат.""",
            parse_mode='HTML',
            reply_markup=Keyboards.back_to_main_menu()
        )
        UserData.add_purchase(update.message.from_user.id)
        return ConversationHandler.END
    
    await update.message.reply_text("Пожалуйста, выберите аккаунт из списка.")
    return States.ACCOUNT

async def handle_currency_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "Отмена" in update.message.text:
        await buy(update, context)
        return States.BUY
    
    try:
        amount = int(update.message.text)
        service = context.user_data['selected_service']
        
        if service['type'] == 'bond':
            total_price = amount * service['price']
            await update.message.reply_text(
                f"""💵 <b>Детали заказа</b>

Вы заказали: {amount} бондов
Цена за 1 бонд: 0.20₽
Итоговая сумма: {total_price:.2f}₽

📌 <b>Реквизиты для оплаты:</b>
{Config.PAYMENT_DETAILS}

После оплаты отправьте скриншот в этот чат.""",
                parse_mode='HTML',
                reply_markup=Keyboards.back_to_main_menu()
            )
            UserData.add_purchase(update.message.from_user.id)
            return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("Пожалуйста, введите число.")
        return States.CURRENCY_AMOUNT

async def support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        """🆘 <b>Центр поддержки</b>

Если у вас возникли вопросы или проблемы:
- С оплатой заказа
- С получением товара
- Любые другие вопросы

Или вы уже совершили перевод и ожидаете получение товара, напишите нам в поддержку!

⏳ <b>Время ответа:</b> 5-15 минут (10:00-22:00 МСК)
📩 <b>Контакты:</b> @{}

<b>Обязательно укажите:</b>
1. Скриншот оплаты
2. Ваш Telegram ID
3. Название заказанного товара

Мы всегда рады помочь!""".format(Config.SUPPORT_USERNAME),
        parse_mode='HTML',
        reply_markup=Keyboards.back_to_main_menu()
    )
    return ConversationHandler.END

async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_data = UserData.get_user(user_id)
    
    status = "🥉 Новый клиент"
    if user_data['purchases'] >= 10:
        status = "🥇 VIP клиент"
    elif user_data['purchases'] >= 3:
        status = "🥈 Постоянный клиент"
    
    await update.message.reply_text(
        f"""👤 <b>Ваш профиль</b>

🆔 ID: <code>{user_id}</code>
📊 Статус: {status}
📦 Совершено покупок: {user_data['purchases']}

📅 Первая покупка: {user_data['first_purchase'] or 'еще нет'}
📅 Последняя покупка: {user_data['last_purchase'] or 'еще нет'}

💡 <b>Советы:</b>
- Сохраните ваш ID для быстрой помощи
- При проблемах сразу пишите в поддержку
- Чем больше покупок - выше ваш статус!""",
        parse_mode='HTML',
        reply_markup=Keyboards.back_to_main_menu()
    )
    return ConversationHandler.END

async def reviews(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        """⭐ <b>Отзывы наших клиентов</b>

Мы ценим каждого клиента и дорожим своей репутацией!

📢 Официальный канал с отзывами: {}
(Реальные скриншоты и видеоотчеты)

💬 <b>Примеры отзывов:</b>
- "Заказал аккаунт, получил через 3 минуты после оплаты!"
- "Лучший магазин по Rail Nation, все честно!"
- "Поддержка помогла решить вопрос за 5 минут"

После покупки вы тоже можете оставить отзыв и получить бонус к следующему заказу!""".format(Config.REVIEWS_CHANNEL),
        parse_mode='HTML',
        reply_markup=Keyboards.back_to_main_menu()
    )
    return ConversationHandler.END

async def back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)
    return ConversationHandler.END

async def run_bot():
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Регистрация обработчиков
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Regex('^(⭐ Отзывы)$'), reviews))
    application.add_handler(MessageHandler(filters.Regex('^(🆘 Поддержка)$'), support))
    application.add_handler(MessageHandler(filters.Regex('^(👤 Мой профиль)$'), profile))
    application.add_handler(MessageHandler(filters.Regex('^(🔙 В главное меню)$'), back_to_main))
    
    # Обработчик диалога покупки
    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^(🛒 Купить)$'), buy)],
        states={
            States.BUY: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    handle_buy_menu
                ),
            ],
            States.SERVICE: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    handle_service
                ),
            ],
            States.ACCOUNT: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    handle_account
                ),
            ],
            States.CURRENCY_AMOUNT: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    handle_currency_amount
                ),
            ],
        },
        fallbacks=[
            CommandHandler('cancel', cancel),
            MessageHandler(filters.Regex('^(🔙 Назад|❌ Отмена|🔙 В главное меню)$'), start),
            MessageHandler(filters.Regex('^(🛒 Купить)$'), buy)
        ],
        allow_reentry=True,
        per_user=True,
        per_chat=True
    )
    
    application.add_handler(conv_handler)
    
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    
    return application

async def shutdown(application):
    await application.updater.stop()
    await application.stop()
    await application.shutdown()

def main():
    # Запуск Flask в отдельном потоке
    Thread(target=run_flask, daemon=True).start()
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    while True:
        try:
            logger.info("Запуск бота...")
            application = loop.run_until_complete(run_bot())
            loop.run_forever()
        except Exception as e:
            logger.error(f"Ошибка в работе бота: {str(e)}")
            if 'application' in locals():
                loop.run_until_complete(shutdown(application))
            logger.info("Перезапуск через 10 секунд...")
            time.sleep(10)
        except KeyboardInterrupt:
            logger.info("Остановка бота...")
            if 'application' in locals():
                loop.run_until_complete(shutdown(application))
            break
        finally:
            loop.close()

if __name__ == '__main__':
    main()
