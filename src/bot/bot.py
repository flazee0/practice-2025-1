import telebot
from telebot import types
import requests
import json
from dotenv import load_dotenv
import os
from gigachat import GigaChat
print('Текущая директория:', os.getcwd())
print('Содержимое папки:', os.listdir('.'))
print('Путь к .env:', os.path.join(os.path.dirname(__file__), '.env'))
print('Содержимое .env:', open(os.path.join(os.path.dirname(__file__), '.env')).read())
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))
print("GIGACHAT_API_KEY:", os.getenv('GIGACHAT_API_KEY'))
TOKEN = '7870860662:AAFPVX47nNi3OHLLNgWNKrOoQaMl2p8sYME'
bot = telebot.TeleBot(TOKEN)
SYSTEM_PROMPT = """Ты - ассистент проекта нейрофоторамок. Твоя задача - отвечать на вопросы пользователей о проекте.
Проект нейрофоторамок - это инновационное решение, которое помогает подбирать одежду на основе погодных условий и предпочтений пользователя.
Система использует компьютерное зрение для распознавания предметов одежды, нейронные сети для анализа погодных условий и машинное обучение для понимания предпочтений пользователя.

Основная информация о проекте:
- Используемые технологии: OpenCV, TensorFlow, React Native, HTML5, CSS3, JavaScript
- Преимущества: экономия времени, учет погоды, персонализированные рекомендации
- Контакты: Телефон: +7 495 018-39-35, Email: i@texel.graphics, Адрес: Москва, Технополис

Отвечай кратко и по существу, используя эту информацию. Если вопрос не связан с проектом, вежливо сообщи об этом."""
QA = {
    'what_is': {
        'question': 'Что такое нейрофоторамки?',
        'answer': 'Нейрофоторамки - это инновационное решение, которое помогает подбирать одежду на основе погодных условий и предпочтений пользователя. Система анализирует текущую погоду и предлагает оптимальные варианты одежды из вашего гардероба.'
    },
    'how_works': {
        'question': 'Как работает система?',
        'answer': 'Система использует компьютерное зрение для распознавания предметов одежды, нейронные сети для анализа погодных условий и машинное обучение для понимания предпочтений пользователя. Все это позволяет создавать персонализированные рекомендации по выбору одежды.'
    },
    'technologies': {
        'question': 'Какие технологии используются?',
        'answer': 'В проекте используются:\n- Компьютерное зрение (OpenCV)\n- Нейронные сети (TensorFlow)\n- Машинное обучение\n- Мобильная разработка (React Native)\n- Веб-технологии (HTML5, CSS3, JavaScript)'
    },
    'benefits': {
        'question': 'Какие преимущества у нейрофоторамок?',
        'answer': 'Основные преимущества:\n- Экономия времени при выборе одежды\n- Учет погодных условий\n- Персонализированные рекомендации\n- Умное управление гардеробом\n- Экологичный подход к использованию одежды'
    },
    'contact': {
        'question': 'Как связаться с компанией Texel?',
        'answer': 'Вы можете связаться с нами:\nТелефон: +7 495 018-39-35\nEmail: i@texel.graphics\nАдрес: Москва, Технополис'
    }
}
def get_ai_response(question):
    try:
        api_key = "ZTU0ZGRiZGYtOWQ3NS00MjViLTlmNTgtZjE0MTEwNTBiOWNhOjdlY2ZhN2NiLWUwY2YtNGE4NC04OWY2LWZiNjM4OGUwN2E5Yg=="
        if not api_key:
            return "GigaChat API ключ не найден. Пожалуйста, добавьте его в .env."
        prompt = f"{SYSTEM_PROMPT}\n\nВопрос пользователя: {question}"
        with GigaChat(credentials=api_key, verify_ssl_certs=False) as giga:
            response = giga.chat(prompt)
            return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error getting GigaChat response: {e}")
        return "Извините, произошла ошибка при обработке вашего вопроса. Пожалуйста, попробуйте позже."
@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for key in QA.keys():
        markup.add(types.KeyboardButton(QA[key]['question']))
    bot.send_message(message.chat.id, 
                     "Добро пожаловать! Я бот проекта нейрофоторамок. "
                     "Выберите интересующий вас вопрос или задайте свой:",
                     reply_markup=markup)
@bot.message_handler(content_types=['text'])
def handle_text(message):
    for key, value in QA.items():
        if message.text == value['question']:
            bot.send_message(message.chat.id, value['answer'])
            return
    bot.send_message(message.chat.id, "Обрабатываю ваш вопрос...")
    response = get_ai_response(message.text)
    bot.send_message(message.chat.id, response)
if __name__ == '__main__':
    print("Bot started...")
    bot.polling(none_stop=True) 