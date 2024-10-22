from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from dotenv import load_dotenv
import os
import shutil
from TerraYolo.TerraYolo import TerraYoloV5             # загружаем фреймворк TerraYolo
from Lesson import detection


'''Этот скрипт создает бота для Telegram, 
   который может отправлять сообщения с различными типами клавиатур (inline и reply), 
   обрабатывать нажатия на кнопки и текстовые сообщения. '''





# возьмем переменные окружения из .env
load_dotenv()

# загружаем токен бота
TOKEN =  os.environ.get("TOKEN") # ВАЖНО !!!!!

# инициализируем класс YOLO
WORK_DIR = r'C:/Users/Lenovo/Desktop/dev/Create_bot_OD'
os.makedirs(WORK_DIR, exist_ok=True)
yolov5 = TerraYoloV5(work_dir=WORK_DIR)

# функция команды /start
async def start(update, context):

    # создаем список Inline кнопок
    keyboard = [[InlineKeyboardButton("Люди", callback_data="0"),
                InlineKeyboardButton("Автомобили", callback_data="2"),
                InlineKeyboardButton("Корабли", callback_data="8")
                ]]
    
    # создаем Inline клавиатуру
    reply_markup = InlineKeyboardMarkup(keyboard)

    # прикрепляем клавиатуру к сообщению
    await update.message.reply_text('Выберите тип распознаваемого объекта', reply_markup=reply_markup)

async def detection(update, context, selected_class):
    # удаляем папку images с предыдущим загруженным изображением и папку runs с результатом предыдущего распознавания
    try:
        shutil.rmtree('images') 
        shutil.rmtree(f'{WORK_DIR}/yolov5/runs') 
    except:
        pass

    my_message = await update.message.reply_text('Мы получили от тебя фотографию. Идет распознавание объектов...')

    if update.message.photo:
        new_file = await update.message.photo[-1].get_file()
    elif update.message.document:
        new_file = await update.message.document.get_file()     

    # имя файла на сервере
    os.makedirs('images', exist_ok=True)
    image_name = str(new_file['file_path']).split("/")[-1]
    image_path = os.path.join('images', image_name)
    # скачиваем файл с сервера Telegram в папку images
    await new_file.download_to_drive(image_path)

    # создаем словарь с параметрами
    test_dict = dict()
    test_dict['weights'] = 'yolov5x.pt'     # Самые сильные веса yolov5x.pt, вы также можете загрузить версии: yolov5n.pt, yolov5s.pt, yolov5m.pt, yolov5l.pt (в порядке возрастания)

    test_dict['source'] = 'images'          # папка, в которую загружаются присланные в бота изображения
    test_dict['conf'] = 0.5              # порог распознавания

    test_dict['classes'] = int(selected_class)   

    # вызов функции detect из класса TerraYolo)
    yolov5.run(test_dict, exp_type='test') 

    # удаляем предыдущее сообщение от бота
    await context.bot.deleteMessage(message_id = my_message.message_id, # если не указать message_id, то удаляется последнее сообщение
                                    chat_id = update.message.chat_id) # если не указать chat_id, то удаляется последнее сообщение

    # отправляем пользователю результат
    await update.message.reply_text('Распознавание объектов завершено') # отправляем пользователю результат 
    await update.message.reply_photo(f"{WORK_DIR}/yolov5/runs/detect/exp/{image_name}") # отправляем пользователю результат изображение


# функция обработки нажатия на кнопки Inline клавиатуры
async def button(update, context):

    # параметры входящего запроса при нажатии на кнопку
    query = update.callback_query
    print(query.data)
    context.user_data['selected_class'] = query.data

    await query.edit_message_text('Пожалуйста, прикрепите фотографию.') 
    
    # отправка всплывающего уведомления
    # await query.answer('Всплывающее уведомление!')
    
    # редактирование сообщения
    # await query.edit_message_text(text=f"Вы нажали на кнопку: {query.data}")

async def handle_photo(update, context):
    selected_class = context.user_data.get('selected_class')

    await detection(update, context, selected_class)   


# функция команды /help
async def help(update, context):

    # создаем список кнопок
    keyboard = [["Кнопка 1","Кнопка 2"]]

    # создаем Reply клавиатуру
    reply_markup = ReplyKeyboardMarkup(keyboard, 
                                       resize_keyboard=True, 
                                       one_time_keyboard=True)

    # выводим клавиатуру с сообщением
    await update.message.reply_text('Пример Reply кнопок', reply_markup=reply_markup)


# функция для текстовых сообщений
async def text(update, context):
    await update.message.reply_text('Текстовое сообщение получено', reply_markup=ReplyKeyboardRemove())


def main():

    # точка входа в приложение
    application = Application.builder().token(TOKEN).build()
    print('Бот запущен...')

    # добавляем обработчик команды /start
    application.add_handler(CommandHandler("start", start))

    # добавляем обработчик нажатия Inline кнопок
    application.add_handler(CallbackQueryHandler(button))

    # добавляем обработчик команды /help
    application.add_handler(CommandHandler("help", help))

    # добавляем обработчик текстовых сообщений
    application.add_handler(MessageHandler(filters.TEXT, text))

    application.add_handler(MessageHandler(filters.PHOTO, handle_photo, block=False))

    application.add_handler(MessageHandler(filters.Document.IMAGE, handle_photo))

    # запуск приложения (для остановки нужно нажать Ctrl-C)
    application.run_polling()


if __name__ == "__main__":
    main()