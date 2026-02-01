import os
import telebot
import speech_recognition as sr
from fastapi import FastAPI
import uvicorn

# Получаем токен бота из переменных окружения Render
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
bot = telebot.TeleBot(BOT_TOKEN)

# Инициализируем FastAPI приложение
app = FastAPI()

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(
        message,
        "Привет! В этом боте ты легко транскрибируешь голос в текст.\nПросто пришли ему голосовое сообщение или запись голоса и получи текст."
    )

def transcribe_audio(audio_file):
    """Транскрибирование аудио в текст."""
    recognizer = sr.Recognizer()
    with sr.AudioFile(audio_file) as source:
        audio = recognizer.record(source)
    try:
        text = recognizer.recognize_google(audio, language="ru-RU")
        return text
    except sr.UnknownValueError:
        return "Не удалось распознать речь."
    except sr.RequestError:
        return "Ошибка при запросе к сервису распознавания речи."

@bot.message_handler(content_types=['voice'])
def handle_voice(message):
    # Отправляем промежуточное сообщение о транскрибировании
    temp_msg = bot.send_message(message.chat.id, "Транскрибирую в текст...")
    
    try:
        # Скачиваем голосовое сообщение
        file_info = bot.get_file(message.voice.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        # Сохраняем файл
        with open('voice.ogg', 'wb') as new_file:
            new_file.write(downloaded_file)
        
        # Транскрибируем аудио
        text = transcribe_audio('voice.ogg')
        
        # Удаляем промежуточное сообщение
        bot.delete_message(temp_msg.chat.id, temp_msg.message_id)
        
        # Отправляем полученный текст
        bot.send_message(message.chat.id, text)
        
        # Завершаем обработку сообщением благодарности
        bot.send_message(message.chat.id, "Спасибо за использование нашего бота!")
    except Exception as e:
        print(e)
        bot.reply_to(message, "Что-то пошло не так при обработке вашего сообщения :(")

# Запускаем бота
bot.infinity_polling()

# Настройка FastAPI для прослушивания порта
@app.get("/")
async def root():
    return {"message": "Telegram Voice to Text Bot is running!"}

if __name__ == "__main__":
    PORT = int(os.getenv('PORT', 8080))
    uvicorn.run(app, host="0.0.0.0", port=PORT)
