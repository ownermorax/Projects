import telebot
from telebot import types
import os

BOT_TOKEN = ''
STUDENT_COUNT = 25
bot = telebot.TeleBot(BOT_TOKEN)
mark1 = {}
mark2 = {}
students = {}
flag = {}
global maxstudents
maxstudents = 2
admins = {}

def check(uid, ref):
    with open(f"{ref}.txt", "r") as file:
        contents = file.readlines()
        for q in contents:
            if(int(uid) == int(q)):
                file.close()
                return True
        file.close()
        return False

@bot.message_handler(commands=['start'])
def start(message):
    global maxstudents
    chat_id = message.chat.id
    try:
        ref = int(message.text.split()[1])
        if(int(students.get(ref)) < maxstudents):
            if(int(ref) != int(chat_id)):
                try:
                    if(check(chat_id, ref) == True):
                        bot.send_message(chat_id,"Вы уже ставили оценку.")
                    else:
                        xf = bot.send_message(chat_id,"Введите оценку в формате число1/число2.")
                        bot.register_next_step_handler(xf, calc, ref)                    
                except:
                    xf = bot.send_message(chat_id,"Введите оценку в формате число1/число2.")
                    bot.register_next_step_handler(xf, calc, ref)
                
            else:
                bot.send_message(chat_id,"Вы не можете ставить себе оценку.")
        else:
              bot.send_message(chat_id,"Было достигнуто максимального количества оценок")
    except IndexError:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.row("Создать опрос")
        bot.reply_to(message, "Привет! Я бот для расчета суммы двух чисел и деления на количество учеников.",reply_markup=markup)
        flag[chat_id] = 0
        
def calc(message,ref):
    chat_id = message.chat.id
    ref= int(ref)
    parts = message.text.split('/')
    try:
        num1 = int(parts[0])
        num2 = int(parts[1])
        if(1 <= num1 <= 5 and 1 <= num2 <= 5):
            bot.send_message(chat_id,"Оценка принята.")
            with open(f"{ref}.txt", "a") as file:
                file.writelines(f"{chat_id}" + '\n')
                file.close()
            mark1[ref] = mark1.get(ref) + num1
            mark2[ref]= mark2.get(ref) + num2
            students[ref]= students.get(ref) + 1
        else:
            bot.send_message(chat_id,"Пожалуйста, введите числа от 1 до 5.")
    except:
        bot.send_message(chat_id,"Неверный формат чисел. Пожалуйста, введите целые числа.")

@bot.message_handler(
    func=lambda message: message.text == 'Создать опрос')
def opros(message):
    chat_id = message.chat.id
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("Завершить опрос")
    with open(f"{chat_id}.txt", "w+") as file:
        file.close()
    mark1[chat_id] = 0
    mark2[chat_id] = 0
    students[chat_id] = 0
    bot.send_message(chat_id, f"🔗 Ваша ссылка для опроса:\n\nhttps://t.me/*юз бота*?start={chat_id}", reply_markup=markup)

@bot.message_handler(
    func=lambda message: message.text == 'Завершить опрос')
def stopopros(message):
    chat_id = message.chat.id
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("Создать опрос")
    if students[chat_id] == 0:
        students[chat_id] = 1
    bot.send_message(chat_id, f"Опрос завершён\nВаша оценка: {mark1[chat_id]/students[chat_id]}/{mark2[chat_id]/students[chat_id]}\nКоличество проголосовавших: {students[chat_id]}", reply_markup=markup)
    os.remove( f"{chat_id}.txt")

@bot.message_handler(commands=['setlimit'])
def setlimit(message):
    chat_id = message.chat.id
    if(chat_id in admins):
        xf = bot.send_message(chat_id,"Введите новый лимит.")
        bot.register_next_step_handler(xf, setlim)
    else:
        bot.send_message(chat_id,"У вас нет прав администратора")

def setlim(message):
    global maxstudents
    chat_id = message.chat.id
    try:
        limit = int(message.text)
        maxstudents = limit
        bot.send_message(chat_id,f"Установлен новый лимит - {maxstudents}")
    except:
        bot.send_message(chat_id,"Неверный формат числа. Пожалуйста, введите целое число.")

        
if __name__ == '__main__':
    print('Бот запущен успешно\nby morax')
    bot.infinity_polling()
