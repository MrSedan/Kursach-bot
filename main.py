import telebot
from telebot import types
from dotenv import dotenv_values
from datetime import datetime
import json, os, sqlite3
from telebot.handler_backends import ContinueHandling

config = dotenv_values('.env')
token = config['TOKEN']

bot = telebot.TeleBot(token)
data = dict()


def get_concerts():
    """Получение списка концертов"""
    db = sqlite3.connect("database.db")
    cursor = db.cursor()
    cursor.execute("SELECT name, date, time, id FROM Concerts")
    concerts = cursor.fetchall()
    cursor.close()
    db.close()
    return concerts


def buy_ticket(user_id, place, line, concert_id):
    """Произвести \"Покупку\" билета"""
    db = sqlite3.connect("database.db")
    cursor = db.cursor()
    user_id = str(user_id)
    cursor.execute(
        f"INSERT INTO Tickets(user,place,line, concert_id) VALUES ({user_id}, {place}, {line}, {concert_id})")
    db.commit()
    cursor.close()
    db.close()


def get_tickets_for_concert(concert_id):
    """Получение списка купленных билетов для концерта"""
    db = sqlite3.connect('database.db')
    cursor = db.cursor()
    cursor.execute(f'SELECT "place", "line" FROM Tickets WHERE concert_id={concert_id}')
    tickets = cursor.fetchall()
    cursor.close()
    db.close()
    return tickets


def gen_markup_after_buy():
    markup = types.InlineKeyboardMarkup()
    but = types.InlineKeyboardButton('Вернутся к концертам', callback_data='back_to_choose_concert')
    markup.add(but)
    return markup


def data_save():
    """Сохранение временной информации на носителе"""
    with open('info.json', 'w') as f:
        json.dump(data, f)


def gen_markup_for_buy(msg):
    """Генерация списка кнопок пролистывания концертов"""
    markup = types.InlineKeyboardMarkup()
    markup.row_width = 1
    msg_id = msg.message_id
    chat_id = msg.chat.id
    # ⬅️➡️
    if not chat_id in data['index']:
        data['index'][chat_id] = 0
        data_save()
    a = []
    if data['index'][chat_id] > 0:
        left_but = types.InlineKeyboardButton('⬅️', callback_data='prev')
        a.append(left_but)
    if data['index'][chat_id] < len(get_concerts()) - 1:
        right_but = types.InlineKeyboardButton('➡️', callback_data='next')
        a.append(right_but)
    markup.row(*a)
    buy_but = types.InlineKeyboardButton('Выбрать билет', callback_data=f'choose_ticket {msg_id}')
    markup.add(buy_but)
    back_but = types.InlineKeyboardButton('Назад', callback_data=f'main_menu {msg_id}')
    markup.add(back_but)
    return markup


def gen_markup_for_choosen_ticket(place, line):
    markup = types.InlineKeyboardMarkup()
    buy_but = types.InlineKeyboardButton('Купить билет', callback_data=f'buy_choosen_ticket {place} {line}')
    markup.add(buy_but)
    but = types.InlineKeyboardButton('Назад', callback_data='choose_ticket')
    markup.add(but)
    return markup


def gen_markup_for_choose(msg):
    """Генерация списка кнопок для выбора билета"""
    # ✅❌
    markup = types.InlineKeyboardMarkup()
    concerts = get_concerts()
    tickets = get_tickets_for_concert(concerts[data['index'][msg.chat.id]][3])
    for i in range(10):
        a = []
        for j in range(8):
            but = types.InlineKeyboardButton(f'✅ {j + 1}', callback_data=f'buy_ticket {j + 1} {i + 1}') if (j + 1,
                                                                                                            i + 1) not in tickets \
                else types.InlineKeyboardButton(f'❌ {j + 1}', callback_data=f'choosen')
            a.append(but)
        markup.row(*a)
    send_map = types.InlineKeyboardButton('Показать карту зала', callback_data='show_map')
    markup.add(send_map)
    back_but = types.InlineKeyboardButton('Назад', callback_data='back_to_choose_concert')
    markup.add(back_but)
    return markup


@bot.message_handler(func=lambda message: True)
def check_concerts(message):
    chat_id = message.chat.id
    if not chat_id in data['index']:
        data['index'][chat_id] = 0
        data_save()
    return ContinueHandling()


@bot.callback_query_handler(func=lambda call: True)
def check_concerts(call: types.CallbackQuery):
    chat_id = call.message.chat.id
    if not chat_id in data['index']:
        data['index'][chat_id] = 0
        data_save()
    return ContinueHandling()


# Обработка стартовой команды
@bot.message_handler(commands=['start'])
def start_message(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buy_tick_but = types.KeyboardButton('Показать концерты')
    markup.add(buy_tick_but)
    bot.send_message(message.chat.id, 'Добро пожаловать в билетную кассу театра имени А.Боба!')
    bot.send_message(message.chat.id, 'Выберете действие, что вы хотите совершить.', reply_markup=markup)


# Обработка сообщений
@bot.message_handler(func=lambda message: True)
def reply_markup_reaction(message):
    if message.text == 'Показать концерты':
        msg = bot.send_message(message.chat.id, 'Выводится список ближайших концертов...',
                               reply_markup=types.ReplyKeyboardRemove())
        concerts = get_concerts()
        concert = concerts[data['index'][message.chat.id]]
        concert_name = concert[0]
        concert_time = concert[2]
        concert_date = concert[1]
        text = f"""{concert_name}\nВремя: {concert_time}\nДата: {concert_date}"""
        bot.send_message(message.chat.id, text, reply_markup=gen_markup_for_buy(msg))


# Обработка нажатий на кнопки под сообщениями
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call: types.CallbackQuery):
    global data
    if call.data.startswith('main_menu'):
        start_message(call.message)
        bot.delete_message(call.message.chat.id, call.message.id)
        bot.delete_message(call.message.chat.id, call.message.id - 1)
        return
    if call.data.startswith('choose_ticket'):
        bot.edit_message_text('Тест', call.message.chat.id, call.message.message_id,
                              reply_markup=gen_markup_for_choose(call.message))
        return
    if call.data.startswith('back_to_choose_concert'):
        concerts = get_concerts()
        concert = concerts[data['index'][call.message.chat.id]]
        concert_name = concert[0]
        concert_time = concert[2]
        concert_date = concert[1]
        text = f"""{concert_name}\nВремя: {concert_time}\nДата: {concert_date}"""
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id + 1)
        except:
            pass
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id,
                              reply_markup=gen_markup_for_buy(call.message))
        return
    if call.data.startswith('show_map'):
        with open('places.png', 'rb') as f:
            map = f.read()
        bot.send_photo(call.message.chat.id, map)
        return
    if call.data.startswith('buy_ticket'):
        place = call.data.split()[1]
        line = call.data.split()[2]
        bot.edit_message_text(f'Выбрано место: {place}\nРяд {line}', call.message.chat.id,
                              call.message.message_id, reply_markup=gen_markup_for_choosen_ticket(place, line))
        return
    if call.data.startswith('buy_choosen_ticket'):
        place = call.data.split()[1]
        line = call.data.split()[2]
        concert_id = get_concerts()[data['index'][call.message.chat.id]][3]
        buy_ticket(call.message.from_user.id, place, line, concert_id)
        bot.edit_message_text(f'Билет на место: {place}\nРяд: {line}\nУспешно приобретен!', call.message.chat.id,
                              call.message.message_id, reply_markup=gen_markup_after_buy())
        return

    concerts = get_concerts()
    chat_id = call.message.chat.id
    if not chat_id in data['index']:
        data['index'][chat_id] = 0
        data_save()
    if data['index'][chat_id] > 0 and call.data == 'prev':
        data['index'][chat_id] -= 1
        data_save()
    if data['index'][chat_id] < len(concerts) - 1 and call.data == 'next':
        data['index'][chat_id] += 1
        data_save()
    concert = concerts[data['index'][chat_id]]
    concert_name = concert[0]
    concert_time = concert[2]
    concert_date = concert[1]
    text = f"""{concert_name}\nВремя: {concert_time}\nДата: {concert_date}"""
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id,
                          reply_markup=gen_markup_for_buy(call.message))


if __name__ == '__main__':
    if not os.path.isfile('info.json'):
        with open('info.json', 'w+') as f:
            json.dump({'index': dict()}, f)

    with open('info.json') as f:
        data = json.load(f)
    bot.polling(none_stop=True, skip_pending=True)
