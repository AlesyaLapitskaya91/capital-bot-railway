import json
import os
import logging
from dotenv import load_dotenv
load_dotenv()  # Загружает переменные из .env файла
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


# Загрузка данных
def load_banks_data():
    try:
        with open('banks.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Ошибка загрузки banks.json: {e}")
        return {}


def load_banks_config():
    try:
        with open('banks_config.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Ошибка загрузки banks_config.json: {e}")
        return {}


BANKS = load_banks_data()
BANKS_CONFIG = load_banks_config()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not BANKS:
        await update.message.reply_text("❌ Данные банков не загружены")
        return

    keyboard = [[name] for name in BANKS.keys()]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text('Выберите банк:', reply_markup=reply_markup)


def main():
    # Получаем токен из переменных окружения
    token = os.getenv('BOT_TOKEN')

    if not token:
        logging.error("❌ BOT_TOKEN не найден!")
        logging.error("Для локального запуска создайте файл .env с BOT_TOKEN=ваш_токен")
        logging.error("Для Railway добавьте BOT_TOKEN в Variables")
        return

    # Проверяем загрузку данных
    logging.info(f"✅ Загружено банков: {len(BANKS)}")
    logging.info("✅ Токен загружен успешно")

    application = Application.builder().token(token).build()
    application.add_handler(CommandHandler("start", start))

    logging.info("🤖 Бот запускается...")
    application.run_polling()


if __name__ == '__main__':
    main()