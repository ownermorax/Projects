import telebot
from telebot import types
from telebot.apihelper import ApiException
import json
import os

# Конфигурация бота
TOKEN = ''
CONFIG_FILE = 'channels_config.json'

# Инициализация бота
bot = telebot.TeleBot(TOKEN)

# Функции для работы с конфигурацией
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)

def get_user_channels(user_id):
    config = load_config()
    return config.get(str(user_id), [])

def add_user_channel(user_id, channel):
    config = load_config()
    if str(user_id) not in config:
        config[str(user_id)] = []
    if channel not in config[str(user_id)]:
        config[str(user_id)].append(channel)
    save_config(config)

def remove_user_channel(user_id, channel):
    config = load_config()
    if str(user_id) in config and channel in config[str(user_id)]:
        config[str(user_id)].remove(channel)
        save_config(config)

# Проверка прав бота
def check_bot_permissions(bot, chat_id):
    try:
        chat = bot.get_chat(chat_id)
        if chat.type == 'channel':
            member = bot.get_chat_member(chat_id, bot.get_me().id)
            return member.can_edit_messages
        return False
    except Exception:
        return False

# Словарь для хранения состояний
user_states = {}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    help_text = """
📢 Бот для управления каналами

🔹 Основные команды:
/addchannel - добавить канал
/mychannels - мои каналы
/newpost - создать пост с кнопками
/addbuttons - добавить кнопки к сообщению
/editbuttons - изменить кнопки
/addalertbutton - кнопка
/listalerts

⚠️ Для редактирования бот должен быть:
1. Администратором канала
2. Иметь право "Изменять сообщения"

Формат кнопок:
Текст - URL
Каждая кнопка с новой строки
Пример:
Купить - https://example.com
Подробнее - https://example.com/details
"""
    bot.reply_to(message, help_text)

@bot.message_handler(commands=['addchannel'])
def add_channel(message):
    msg = bot.send_message(message.chat.id, "📢 Введите @username или ID канала (например @my_channel или -1001234567890):\n\n"
                                          "Бот должен быть администратором этого канала!")
    bot.register_next_step_handler(msg, process_add_channel)

def process_add_channel(message):
    try:
        channel = message.text.strip()
        if not channel.startswith(('@', '-100')):
            raise ValueError("Некорректный формат канала")
            
        if not check_bot_permissions(bot, channel):
            bot.reply_to(message, f"❌ У бота нет прав на редактирование в {channel}.\n"
                                "Добавьте бота как администратора с правом 'Изменять сообщения'.")
            return
            
        add_user_channel(message.from_user.id, channel)
        bot.reply_to(message, f"✅ Канал {channel} добавлен!")
        
    except Exception as e:
        bot.reply_to(message, f"⚠️ Ошибка: {str(e)}")


@bot.message_handler(commands=['mychannels'])
def list_channels(message):
    channels = get_user_channels(message.from_user.id)
    if not channels:
        bot.reply_to(message, "❌ У вас нет добавленных каналов. Используйте /addchannel")
        return
    
    response = "📢 Ваши каналы:\n\n" + "\n".join(f"{i+1}. {channel}" for i, channel in enumerate(channels))
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Управление каналами", callback_data="manage_channels"))
    
    bot.reply_to(message, response, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    try:
        if call.data == 'manage_channels':
            show_channel_management(call)
        elif call.data == 'back_to_channels':
            list_channels(call.message)
        elif call.data.startswith('remove_'):
            remove_channel(call)
        elif call.data.startswith('newpost_'):
            start_new_post(call)
        elif call.data.startswith('addbuttons_'):
            start_add_buttons(call)
            
    except Exception as e:
        bot.answer_callback_query(call.id, f"Ошибка: {str(e)}", show_alert=True)

def show_channel_management(call):
    channels = get_user_channels(call.from_user.id)
    markup = types.InlineKeyboardMarkup()
    for channel in channels:
        markup.add(types.InlineKeyboardButton(f"❌ Удалить {channel}", callback_data=f"remove_{channel}"))
    markup.add(types.InlineKeyboardButton("◀️ Назад", callback_data="back_to_channels"))
    
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="🗑 Выберите канал для удаления:",
        reply_markup=markup
    )

def remove_channel(call):
    channel = call.data.split('_')[1]
    remove_user_channel(call.from_user.id, channel)
    bot.answer_callback_query(call.id, f"Канал {channel} удален")
    list_channels(call.message)

def start_new_post(call):
    channel = call.data.split('_')[1]
    user_states[call.from_user.id] = {
        'channel': channel,
        'step': 'waiting_post_text'
    }
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=f"📝 Введите текст поста для публикации в {channel}:"
    )

def start_add_buttons(call):
    channel = call.data.split('_')[1]
    if not check_bot_permissions(bot, channel):
        bot.answer_callback_query(
            call.id,
            f"У бота нет прав на редактирование в {channel}",
            show_alert=True
        )
        return
        
    user_states[call.from_user.id] = {
        'channel': channel,
        'step': 'waiting_message_id_for_buttons'
    }
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=f"🔢 Введите ID сообщения в {channel} для добавления кнопок:\n\n"
             "ℹ️ ID можно получить, переслав сообщение боту @getidsbot"
    )

# Создание нового поста
@bot.message_handler(func=lambda message: user_states.get(message.from_user.id, {}).get('step') == 'waiting_post_text')
def process_post_text(message):
    try:
        user_id = message.from_user.id
        channel = user_states[user_id]['channel']
        user_states[user_id] = {
            'channel': channel,
            'post_text': message.text,
            'step': 'waiting_buttons'
        }
        
        bot.send_message(message.chat.id, "✅ Текст сохранен. Теперь введите кнопки в формате:\n"
                                       "Текст - URL\n"
                                       "Каждая кнопка с новой строки\n\n"
                                       "Пример:\n"
                                       "Купить - https://example.com\n"
                                       "Подробнее - https://example.com/details")
    
    except Exception as e:
        bot.reply_to(message, f"⚠️ Ошибка: {str(e)}")
        if user_id in user_states:
            del user_states[user_id]


@bot.message_handler(func=lambda message: user_states.get(message.from_user.id, {}).get('step') == 'waiting_buttons')
def process_post_buttons(message):
    try:
        user_id = message.from_user.id
        channel = user_states[user_id]['channel']
        post_text = user_states[user_id]['post_text']
        
        markup = create_markup_from_text(message.text)
        
        
        bot.send_message(
            chat_id=channel,
            text=post_text,
            reply_markup=markup
        )
        
        bot.send_message(message.chat.id, f"✅ Пост опубликован в {channel}!")
        del user_states[user_id]
        
    except Exception as e:
        bot.reply_to(message, f"⚠️ Ошибка: {str(e)}")
        if user_id in user_states:
            del user_states[user_id]

# Добавление кнопок к существующему сообщению
@bot.message_handler(func=lambda message: user_states.get(message.from_user.id, {}).get('step') == 'waiting_message_id_for_buttons')
def process_message_id_for_buttons(message):
    try:
        user_id = message.from_user.id
        channel = user_states[user_id]['channel']
        msg_id = int(message.text.strip())
        
        user_states[user_id] = {
            'channel': channel,
            'message_id': msg_id,
            'step': 'waiting_buttons_to_add'
        }
        
        bot.send_message(message.chat.id, "🛠 Введите кнопки в формате:\n"
                                       "Текст - URL\n"
                                       "Каждая кнопка с новой строки")
    
    except ValueError:
        bot.reply_to(message, "❌ Неверный формат ID. Укажите числовой ID сообщения.")
    except Exception as e:
        bot.reply_to(message, f"⚠️ Ошибка: {str(e)}")
        if user_id in user_states:
            del user_states[user_id]


@bot.message_handler(func=lambda message: user_states.get(message.from_user.id, {}).get('step') == 'waiting_buttons_to_add')
def process_add_buttons_to_message(message):
    try:
        user_id = message.from_user.id
        if user_id not in user_states:
            bot.reply_to(message, "⏳ Сессия истекла. Начните заново.")
            return
            
        channel = user_states[user_id]['channel']
        msg_id = user_states[user_id]['message_id']
        
        try:
            chat_member = bot.get_chat_member(channel, bot.get_me().id)
            if not chat_member.can_edit_messages:
                bot.reply_to(message, f"❌ У бота нет прав на редактирование в {channel}")
                del user_states[user_id]
                return
        except Exception as e:
            bot.reply_to(message, f"❌ Ошибка проверки прав: {str(e)}")
            del user_states[user_id]
            return
        
        buttons_text = message.text
        
        markup = types.InlineKeyboardMarkup()
        
        for line in buttons_text.split('\n'):
            if '-' in line:
                try:
                    text, url = [part.strip() for part in line.split('-', 1)]
                    if not url.startswith(('http://', 'https://')):
                        url = 'https://' + url
                    markup.add(types.InlineKeyboardButton(text=text, url=url))
                except ValueError:
                    continue
        
        try:
            bot.edit_message_reply_markup(
                chat_id=channel,
                message_id=msg_id,
                reply_markup=markup
            )
            bot.send_message(message.chat.id, f"✅ Кнопки успешно обновлены в {channel}!")
            
        except ApiException as e:
            error_msg = f"⚠️ Ошибка при редактировании:\n"
            if "message not found" in str(e):
                error_msg += "Сообщение не найдено. Проверьте ID."
            elif "not enough rights" in str(e):
                error_msg += "Недостаточно прав для редактирования."
            else:
                error_msg += str(e)
            bot.reply_to(message, error_msg)
        
        del user_states[user_id]
        
    except Exception as e:
        bot.reply_to(message, f"⚠️ Ошибка: {str(e)}")
        if user_id in user_states:
            del user_states[user_id]

# Вспомогательные функции
def create_markup_from_text(buttons_text):
    markup = types.InlineKeyboardMarkup()
    for line in buttons_text.split('\n'):
        if '-' in line:
            try:
                text, url = [part.strip() for part in line.split('-', 1)]
                if not url.startswith(('http://', 'https://')):
                    url = 'https://' + url
                markup.add(types.InlineKeyboardButton(text=text, url=url))
            except ValueError:
                continue
    return markup

def get_message_text(bot, chat_id, message_id):
    try:
        message = bot.get_chat_message(chat_id, message_id)
        return message.text
    except Exception:
        return ""

def handle_edit_errors(message, error):
    error_msg = "⚠️ Ошибка при редактировании:\n"
    if "message not found" in str(error):
        error_msg += "Сообщение не найдено. Проверьте ID."
    elif "not enough rights" in str(error):
        error_msg += "Недостаточно прав для редактирования."
    elif "message is not modified" in str(error):
        error_msg += "Сообщение не было изменено."
    else:
        error_msg += str(error)
    bot.reply_to(message, error_msg)

@bot.message_handler(commands=['addbuttons', 'editbuttons'])
def handle_buttons_commands(message):
    channels = get_user_channels(message.from_user.id)
    if not channels:
        bot.reply_to(message, "❌ У вас нет добавленных каналов. Используйте /addchannel")
        return
    
    markup = types.InlineKeyboardMarkup()
    for channel in channels:
        btn_text = "Выбрать" if len(channels) < 5 else channel
        markup.add(types.InlineKeyboardButton(
            btn_text,
            callback_data=f"{message.text[1:]}_{channel}"
        ))
    
    bot.send_message(
        message.chat.id,
        "📢 Выберите канал:",
        reply_markup=markup
    )
# Глобальный словарь для хранения уведомлений
alert_buttons = {}

@bot.message_handler(commands=['addalertbutton'])
def add_alert_button(message):
    """Добавление/редактирование кнопки с уведомлением"""
    try:
        channels = get_user_channels(message.from_user.id)
        if not channels:
            bot.reply_to(message, "❌ У вас нет добавленных каналов. Используйте /addchannel")
            return
        
        bot.send_message(
            message.chat.id,
            "✏️ Введите данные в формате:\n\n"
            "<code>Канал | ID сообщения | Текст кнопки | Текст уведомления</code>\n\n"
            "Пример добавления новой кнопки:\n"
            "<code>@my_channel | 123 | Важное | Это тестовое уведомление!</code>\n\n"
            "Пример редактирования существующей кнопки (укажите тот же текст кнопки):\n"
            "<code>@my_channel | 123 | Важное | Новый текст уведомления</code>\n\n"
            "Ваши каналы:\n" + "\n".join(channels),
            parse_mode="HTML"
        )
        
        user_states[message.from_user.id] = {'step': 'waiting_alert_data'}
        
    except Exception as e:
        bot.reply_to(message, f"⚠️ Ошибка: {str(e)}")

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id, {}).get('step') == 'waiting_alert_data')
def process_alert_button(message):
    """Обработка данных для кнопки с уведомлением"""
    try:
        parts = [part.strip() for part in message.text.split('|')]
        if len(parts) != 4:
            raise ValueError("Нужно 4 части, разделенные |")
            
        channel, msg_id, button_text, alert_text = parts
        msg_id = int(msg_id)
        

        if channel not in get_user_channels(message.from_user.id):
            raise ValueError("У вас нет прав управлять этим каналом")
        try:
            forwarded = bot.forward_message(
                chat_id=message.chat.id,
                from_chat_id=channel,
                message_id=msg_id
            )
            
            if forwarded.reply_markup:
                markup = forwarded.reply_markup
                
                button_exists = False
                for row in markup.keyboard:
                    for btn in row:
                        if btn.text == button_text:
                            btn.callback_data = f"alert_{alert_text.replace('|', ' ')}"
                            button_exists = True
                            break
                    if button_exists:
                        break
                
                if not button_exists:
                    markup.add(types.InlineKeyboardButton(
                        text=button_text,
                        callback_data=f"alert_{alert_text.replace('|', ' ')}"
                    ))
            else:
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton(
                    text=button_text,
                    callback_data=f"alert_{alert_text.replace('|', ' ')}"
                ))
            
            alert_buttons[f"{channel}_{msg_id}_{button_text}"] = alert_text
            
            bot.edit_message_reply_markup(
                chat_id=channel,
                message_id=msg_id,
                reply_markup=markup
            )
            
            bot.reply_to(message, f"✅ Кнопка '{button_text}' добавлена/обновлена в {channel} к сообщению {msg_id}!")
            
        except ApiException as e:
            error_msg = "❌ Ошибка при работе с сообщением:\n"
            if "message not found" in str(e):
                error_msg += "Сообщение не найдено. Проверьте ID."
            elif "not enough rights" in str(e):
                error_msg += "Недостаточно прав для редактирования."
            else:
                error_msg += str(e)
            raise Exception(error_msg)
        
    except ValueError as e:
        bot.reply_to(message, f"❌ Ошибка в формате: {str(e)}\n\n"
                         "Правильный формат:\n"
                         "<code>Канал | ID сообщения | Текст кнопки | Текст уведомления</code>\n\n"
                         "Пример:\n"
                         "<code>@my_channel | 123 | Нажми меня | Привет!</code>",
                         parse_mode="HTML")
    except Exception as e:
        bot.reply_to(message, f"⚠️ Ошибка: {str(e)}")
    finally:
        if message.from_user.id in user_states:
            del user_states[message.from_user.id]

@bot.callback_query_handler(func=lambda call: call.data.startswith('alert_'))
def handle_alert_button(call):
    """Обработка нажатия на кнопку с уведомлением"""
    try:
        alert_text = call.data[6:].replace(' ', '|')
        
        bot.answer_callback_query(
            callback_query_id=call.id,
            text=alert_text,
            show_alert=True
        )
        
        bot.send_message(
            chat_id=call.message.chat.id,
            text=f"🔔 Уведомление: {alert_text}",
            reply_to_message_id=call.message.message_id
        )
        
    except Exception as e:
        try:
            bot.answer_callback_query(
                call.id,
                "Ошибка при показе уведомления",
                show_alert=True
            )
        except:
            pass

@bot.message_handler(commands=['listalerts'])
def list_alert_buttons(message):
    """Показать все кнопки с уведомлениями"""
    try:
        user_channels = get_user_channels(message.from_user.id)
        if not user_channels:
            bot.reply_to(message, "❌ У вас нет добавленных каналов")
            return
        
        user_alerts = []
        for key in alert_buttons:
            channel = key.split('_')[0]
            if channel in user_channels:
                user_alerts.append(key)
        
        if not user_alerts:
            bot.reply_to(message, "ℹ️ У вас нет созданных кнопок с уведомлениями")
            return
        
        response = "📋 Ваши кнопки с уведомлениями:\n\n"
        for alert_key in user_alerts:
            parts = alert_key.split('_')
            channel = parts[0]
            msg_id = parts[1]
            btn_text = '_'.join(parts[2:])
            response += f"🔹 {channel} (сообщение {msg_id}):\nКнопка: {btn_text}\nУведомление: {alert_buttons[alert_key]}\n\n"
        
        bot.reply_to(message, response)
        
    except Exception as e:
        bot.reply_to(message, f"⚠️ Ошибка: {str(e)}")
      
if __name__ == '__main__':
    print("Бот запущен и готов к работе...")
    bot.infinity_polling()
