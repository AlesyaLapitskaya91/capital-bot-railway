from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, ConversationHandler, filters
import json

CHOOSE_BANK = 0
TOKEN = '8410306872:AAHBR2Jy6xxD8ZlNz9x9KFGtXFFtTm5xhT0'

# Загружаем конфиг банков
import os

base_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(base_dir, 'banks_config.json.py')

print("Ищу файл по пути:", config_path)
print("Существует ли файл:", os.path.exists(config_path))

with open(config_path, encoding='utf-8') as f:
   BANKS = json.load(f)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
   keyboard = [[name] for name in BANKS.keys()]
   reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
   await update.message.reply_text("Привет! Я бот для поиска нормативного капитала банков Беларуси.\n"
       "Выбери название банка, и я покажу его капитал.:", reply_markup=reply_markup)
   return CHOOSE_BANK

async def handle_bank_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
   bank_name = update.message.text
   if bank_name not in BANKS:
       await update.message.reply_text("Банк не найден. Попробуйте снова.")
       return CHOOSE_BANK

   url = BANKS[bank_name].get("disclosure_url")
   if not url:
       await update.message.reply_text("Для этого банка ссылка не задана.")
   else:
       await update.message.reply_text(f"Ссылка на нормативный капитал банка {bank_name}:\n{url}")

   return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
   await update.message.reply_text("Отменено.")
   return ConversationHandler.END

def main():
   app = ApplicationBuilder().token(TOKEN).build()

   conv_handler = ConversationHandler(
       entry_points=[CommandHandler('start', start)],
       states={
           CHOOSE_BANK: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_bank_choice)]
       },
       fallbacks=[CommandHandler('cancel', cancel)],
   )

   app.add_handler(conv_handler)
   print("Бот запущен.")
   app.run_polling()

if __name__ == '__main__':
   main()
