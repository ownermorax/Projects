import os
import html
import telebot
from threading import Thread
from openai import OpenAI
from threading import Thread
import time
from telebot import types

BOT_TOKEN = "your_token"

bot = telebot.TeleBot(BOT_TOKEN)

client = OpenAI(api_key='your_api', base_url="https://openrouter.ai/api/v1",)

chat_contexts = {}
gpt_typing = {}
waiting_for_file = {}

def typing(chat_id):
    while gpt_typing.get(chat_id, 1) == 0:
        bot.send_chat_action(chat_id, "typing")
        time.sleep(5)

def create_main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    explain_btn = types.KeyboardButton("📝 Объяснить код")
    analyze_btn = types.KeyboardButton("🔍 Анализ кода")
    reset_btn = types.KeyboardButton("🔄 Сбросить диалог")
    markup.add(explain_btn, analyze_btn, reset_btn)
    return markup

def create_reset_button(chat_id):
    markup = types.InlineKeyboardMarkup()
    reset_button = types.InlineKeyboardButton("🔄 Сбросить диалог", callback_data=f"reset_{chat_id}")
    markup.add(reset_button)
    return markup

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = """
👋 Привет! Я — @GodOfCodeRobot, твой AI-ассистент.

Я могу:
- 🔍 Анализировать код (Python, JavaScript и др.)
- 📚 Объяснять алгоритмы и концепции
- ⚡ Оптимизировать код
- 💡 Объяснять IT-концепции и уязвимости

Просто отправь мне код или вопрос, и я помогу!

Команды:
/start - показать это сообщение
/reset - сбросить контекст диалога

Используй кнопки ниже для быстрого доступа к функциям:
"""
    with open('image.jpg', 'rb') as photo:
        bot.send_photo(message.chat.id, photo, welcome_text, reply_markup=create_main_menu())

@bot.message_handler(commands=['reset'])
def reset_conversation(message):
    chat_id = message.chat.id
    if chat_id in chat_contexts:
        del chat_contexts[chat_id]
    if chat_id in waiting_for_file:
        del waiting_for_file[chat_id]
    bot.reply_to(message, "🔄 Контекст диалога сброшен. Начинаем новый диалог.", reply_markup=create_main_menu())

@bot.callback_query_handler(func=lambda call: call.data.startswith('reset_'))
def reset_callback(call):
    chat_id = int(call.data.split('_')[1])
    if chat_id in chat_contexts:
        del chat_contexts[chat_id]
    if chat_id in waiting_for_file:
        del waiting_for_file[chat_id]
    bot.send_message(chat_id, "🔄 Контекст диалога сброшен. Начинаем новый диалог.", reply_markup=create_main_menu())
    bot.answer_callback_query(call.id)

@bot.message_handler(func=lambda message: message.text == "📝 Объяснить код")
def request_code_explanation(message):
    chat_id = message.chat.id
    waiting_for_file[chat_id] = "explain"
    bot.send_message(chat_id, "📎 Пожалуйста, отправьте файл с кодом, который нужно объяснить.", reply_markup=types.ReplyKeyboardRemove())

@bot.message_handler(func=lambda message: message.text == "🔍 Анализ кода")
def request_code_analysis(message):
    chat_id = message.chat.id
    waiting_for_file[chat_id] = "analyze"
    bot.send_message(chat_id, "📎 Пожалуйста, отправьте файл с кодом для анализа.", reply_markup=types.ReplyKeyboardRemove())

@bot.message_handler(func=lambda message: message.text == "🔄 Сбросить диалог")
def reset_conversation_button(message):
    reset_conversation(message)

def process_code_file(chat_id, file_content, action):
    if chat_id not in chat_contexts:
        chat_contexts[chat_id] = [
            {"role": "system", "content": """Ты — ассистент для разработчиков и IT-специалистов. 
            Ты умеешь:
            1. Анализировать код на разных языках программирования
            2. Находить ошибки и предлагать оптимизации
            3. Объяснять алгоритмы и концепции программирования
            4. Объяснять IT-концепции, уязвимости, принципы работы технологий
            
            Отвечай подробно и понятно, с примерами когда это уместно."""}
        ]
    
    if action == "explain":
        user_message = f"Объясни этот код построчно и подробно:\n```\n{file_content}\n```"
    else: 
        user_message = f"Проанализируй этот код, найди ошибки и предложи оптимизации:\n```\n{file_content}\n```"
    
    chat_contexts[chat_id].append({"role": "user", "content": user_message})
    
    try:
        response = client.chat.completions.create(
            model="deepseek/deepseek-r1:free",
            messages=chat_contexts[chat_id],
        )
        
        ai_response = response.choices[0].message.content
        chat_contexts[chat_id].append({"role": "assistant", "content": ai_response})
        
        markup = create_reset_button(chat_id)
        bot.send_message(chat_id, ai_response, parse_mode="Markdown", reply_markup=create_main_menu())
    except Exception as e:
        bot.send_message(chat_id, f"❌ Ошибка: {str(e)}", reply_markup=create_main_menu())

def split_long_message(message, max_length=4096):
    message = str(message)
    if len(message) <= max_length:
        return [message]
    
    parts = []
    while message:
        if len(message) > max_length:
            split_pos = message.rfind('\n', 0, max_length)
            if split_pos == -1:
                split_pos = max_length
            part = message[:split_pos]
            message = message[split_pos:].lstrip()
        else:
            part = message
            message = ''
        parts.append(part)
    return parts

@bot.message_handler(content_types=['text'])
def handle_text(message):
    chat_id = message.chat.id
    user_input = message.text.strip()
    
    if not user_input:
        bot.reply_to(message, "Пожалуйста, введите текст сообщения.")
        return
        
    if chat_id in waiting_for_file:
        bot.send_message(chat_id, "Я ожидаю файл с кодом. Пожалуйста, отправьте файл или нажмите /cancel.", reply_markup=create_main_menu())
        return
        
    gpt_typing[chat_id] = 0
    th = Thread(target=typing, args=(chat_id,))
    th.start()
    
    if chat_id not in chat_contexts:
        chat_contexts[chat_id] = [
            {
                "role": "system", 
                "content": """Ты — ассистент для разработчиков и IT-специалистов.                 
                Отвечай подробно и понятно, с примерами когда это уместно."""
            }
        ]
    
    chat_contexts[chat_id].append({"role": "user", "content": user_input})

    try:
        response = client.chat.completions.create(
            model="deepseek/deepseek-r1:free", 
            messages=chat_contexts[chat_id],
        )
        
        ai_response = response.choices[0].message.content
        chat_contexts[chat_id].append({"role": "assistant", "content": ai_response})
        
        message_parts = split_long_message(ai_response, 4096)
        
        markup = create_reset_button(chat_id)
        for part in message_parts:
            try:
                if part == message_parts[0]:
                    bot.send_message(chat_id, part, parse_mode='Markdown', reply_markup=create_main_menu())
                else:
                    bot.send_message(chat_id, part, parse_mode='Markdown')
            except Exception as e:
                try:
                    if part == message_parts[0]:
                        bot.send_message(chat_id, part, reply_markup=create_main_menu())
                    else:
                        bot.send_message(chat_id, part)
                except Exception as e:
                    bot.send_message(chat_id, f"❌ Не удалось отправить часть сообщения: {str(e)}")
                    
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {str(e)}")
    finally:
        gpt_typing[chat_id] = 1

@bot.message_handler(content_types=['document'])
def handle_code_file(message):
    chat_id = message.chat.id
    action = waiting_for_file.get(chat_id)
    
    if not action:
        bot.send_message(chat_id, "Пожалуйста, выберите действие с помощью кнопок: 'Объяснить код' или 'Анализ кода'.", reply_markup=create_main_menu())
        return
    
    gpt_typing[chat_id] = 0
    th = Thread(target=typing, args=(chat_id, ))
    th.start()
    
    try:
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        file_path = f"temp_{message.document.file_name}"
        with open(file_path, 'wb') as f:
            f.write(downloaded_file)
        
        with open(file_path, 'r', encoding='utf-8') as f:
            code_content = f.read()
        
        os.remove(file_path)
        
        process_code_file(chat_id, code_content, action)
        
        if chat_id in waiting_for_file:
            del waiting_for_file[chat_id]
            
    except Exception as e:
        bot.send_message(chat_id, f"❌ Ошибка при обработке файла: {str(e)}", reply_markup=create_main_menu())
    finally:
        gpt_typing[chat_id] = 1
        if chat_id in waiting_for_file:
            del waiting_for_file[chat_id]

if __name__ == "__main__":
    print("🤖 Бот запущен...")
    bot.infinity_polling()
