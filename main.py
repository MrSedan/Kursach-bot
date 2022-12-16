import telebot
from telebot import types
from dotenv import dotenv_values
from datetime import datetime
import json, os, sqlite3
from telebot.handler_backends import ContinueHandling
from telebot.apihelper import ApiTelegramException

dotenv = dotenv_values()
token = dotenv['TOKEN']

bot = telebot.TeleBot(token)
data = dict()


def log(text: str):
    """Запись лога в файл"""
    text = str(text)
    with open('log.txt', 'a+', encoding='utf-8') as f:
        f.write(f"{datetime.now()} {text}\n")


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
    log(f"Произведена покупка билета на место {place}, ряд {line}, ид концерта {concert_id}")
    db.commit()
    cursor.close()
    db.close()


def get_my_tickets(user_id):
    """Получение списка билетов, приобретенных текущим пользователем"""
    db = sqlite3.connect("database.db")
    cursor = db.cursor()
    user_id = str(user_id)
    cursor.execute(
        f"""SELECT Concerts.name as concert_name, Concerts.date, Concerts.time, Tickets.place, Tickets.line FROM Concerts
        JOIN Tickets ON Tickets.concert_id = Concerts.id
        WHERE Tickets.user = {user_id};"""
    )
    my_tickets = cursor.fetchall()
    cursor.close()
    db.close()
    return my_tickets


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
    """Генерация кнопок после покупки билета"""
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
    chat_id = str(msg.chat.id)
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
    buy_but = types.InlineKeyboardButton('Выбрать место', callback_data=f'choose_ticket {msg_id}')
    markup.add(buy_but)
    back_but = types.InlineKeyboardButton('Назад', callback_data=f'main_menu {msg_id}')
    markup.add(back_but)
    return markup


def gen_markup_for_choosen_ticket(place, line):
    """Генерация списка кнопок для подтверждения покупки"""
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
    chat_id = str(msg.chat.id)
    tickets = get_tickets_for_concert(concerts[data['index'][chat_id]][3])
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
def check_concerts(message: types.Message):
    """Удаление предыдущих сообщений после текстовой команды"""
    chat_id = str(message.chat.id)
    if not chat_id in data['index']:
        data['index'][chat_id] = 0
    if not chat_id in data['delete']:
        data['delete'][chat_id] = 0
    for i in range(data['delete'][chat_id]):
        try:
            bot.delete_message(chat_id, message.message_id - i - 1)
        except ApiTelegramException:
            pass
    data['delete'][chat_id] = 0
    data_save()
    return ContinueHandling()


@bot.callback_query_handler(func=lambda call: True)
def check_concerts(call: types.CallbackQuery):
    """Удаление предыдущих сообщений после нажатия на кнопку"""
    chat_id = str(call.message.chat.id)
    if not chat_id in data['index']:
        data['index'][chat_id] = 0
    if not chat_id in data['delete']:
        data['delete'][chat_id] = 0
    for i in range(data['delete'][chat_id]):
        try:
            bot.delete_message(chat_id, call.message.message_id - i - 1)
        except ApiTelegramException:
            pass
    data['delete'][chat_id] = 0
    data_save()
    return ContinueHandling()


@bot.message_handler(commands=['start'])
def start_message(message):
    """Обрботка стартовой команды"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buy_tick_but = types.KeyboardButton('Показать концерты')
    my_tickets = types.KeyboardButton('Мои билеты')
    markup.add(buy_tick_but)
    markup.add(my_tickets)
    chat_id = str(message.chat.id)
    bot.send_message(message.chat.id, 'Добро пожаловать в билетную кассу театра имени А.Боба!')
    bot.send_message(message.chat.id, 'Выберите действие, что вы хотите совершить.', reply_markup=markup)
    i = 0
    while i>=0:
        try:
            bot.delete_message(message.chat.id, message.message_id - i)
            i += 1
        except ApiTelegramException:
            i = -1
    data['delete'][chat_id] = 3
    data_save()


@bot.message_handler(func=lambda message: message.text == 'Показать концерты')
def reply_markup_reaction_show_concerts(message):
    """Выдать список концертов"""
    global data
    chat_id = str(message.chat.id)
    msg = bot.send_message(message.chat.id, 'Выводится список ближайших концертов...',
                           reply_markup=types.ReplyKeyboardRemove())
    concerts = get_concerts()
    concert = concerts[data['index'][chat_id]]
    concert_name = concert[0]
    concert_time = concert[2]
    concert_date = concert[1]
    text = f"""{concert_name}\nВремя: {concert_time}\nДата: {concert_date}"""
    bot.send_message(message.chat.id, text, reply_markup=gen_markup_for_buy(msg))
    data['delete'][chat_id] += 2
    data_save()


@bot.message_handler(func=lambda message: message.text == 'Мои билеты')
def show_my_tickets(message: types.Message):
    """Выдача купленных билетов"""
    bot.send_message(message.chat.id, 'Выводятся ваши билеты...',
                     reply_markup=types.ReplyKeyboardRemove())
    my_tickets = get_my_tickets(message.from_user.id)
    markup = types.InlineKeyboardMarkup()
    back_but = types.InlineKeyboardButton('Назад', callback_data='main_menu')
    markup.add(back_but)
    chat_id = str(message.chat.id)
    t = 0
    if my_tickets:
        for i in range(len(my_tickets)):
            name = my_tickets[i][0]
            date = my_tickets[i][1]
            time = my_tickets[i][2]
            place = my_tickets[i][3]
            line = my_tickets[i][4]
            if i + 1 == len(my_tickets):
                bot.send_message(message.chat.id,
                                 f'Билет на: {name}\nДата: {date}\nВремя: {time}\nРяд: {line}\nМесто: {place}',
                                 reply_markup=markup)
            else:
                bot.send_message(message.chat.id,
                                 f'Билет на: {name}\nДата: {date}\nВремя: {time}\nРяд: {line}\nМесто: {place}')
        data['delete'][chat_id] = len(my_tickets) + 1
    else:
        bot.send_message(message.chat.id, f'Ни одного билета не приобретено!',
                         reply_markup=markup)
        data['delete'][chat_id] = 2
    data_save()


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call: types.CallbackQuery):
    """Обработка нажатий на кнопки под сообщениями"""
    global data
    chat_id = str(call.message.chat.id)
    if call.data.startswith('main_menu'):
        start_message(call.message)
        try:
            for i in range(2):
                bot.delete_message(call.message.chat.id, call.message.id - i)
        except ApiTelegramException:
            pass
        return
    if call.data.startswith('choose_ticket'):
        concerts = get_concerts()
        concert = concerts[concerts[data['index'][chat_id]][3] - 1]
        name = concert[0]
        bot.edit_message_text(f'Выводятся места на концерт: {name}', call.message.chat.id, call.message.message_id,
                              reply_markup=gen_markup_for_choose(call.message))
        return
    if call.data.startswith('back_to_choose_concert'):
        concerts = get_concerts()
        concert = concerts[data['index'][chat_id]]
        concert_name = concert[0]
        concert_time = concert[2]
        concert_date = concert[1]
        text = f"""{concert_name}\nВремя: {concert_time}\nДата: {concert_date}"""
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id + 1)
        except ApiTelegramException:
            pass
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id,
                              reply_markup=gen_markup_for_buy(call.message))
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id + 1)
        except ApiTelegramException:
            pass
        return
    if call.data.startswith('show_map'):
        with open('places.png', 'rb') as f:
            map = f.read()
        bot.send_photo(call.message.chat.id, map)
        return
    if call.data.startswith('buy_ticket'):
        place = call.data.split()[1]
        line = call.data.split()[2]
        bot.edit_message_text(f'Выбрано место: {place}\nРяд: {line}', call.message.chat.id,
                              call.message.message_id, reply_markup=gen_markup_for_choosen_ticket(place, line))
        return
    if call.data.startswith('buy_choosen_ticket'):
        place = call.data.split()[1]
        line = call.data.split()[2]
        concert_id = get_concerts()[data['index'][chat_id]][3]
        tickets = get_tickets_for_concert(concert_id)
        if (int(place), int(line)) not in tickets:
            buy_ticket(call.message.chat.id, place, line, concert_id)
            concerts = get_concerts()
            concert = concerts[concerts[data['index'][chat_id]][3] - 1]
            name = concert[0]
            bot.edit_message_text(f'Билет на место: {place}\nРяд: {line}\nКонцерт: {name}\nУспешно приобретен!',
                                  call.message.chat.id,
                                  call.message.message_id, reply_markup=gen_markup_after_buy())
        else:
            bot.edit_message_text(f'К сожалению, данный билет уже был приобретен!', call.message.chat.id,
                                  call.message.message_id, reply_markup=gen_markup_cant_buy())
        return

    concerts = get_concerts()
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
    if not os.path.isfile('log.txt'):
        with open('log.txt', 'w+', encoding='utf-8'): pass
    if not os.path.isfile('info.json'):
        with open('info.json', 'w+') as f:
            json.dump({'index': dict(), 'delete': dict()}, f)
    if not os.path.isfile('database.db'):
        with open('log.txt', 'w+'): pass
        with open('database.db', 'w+') as f: pass
        db = sqlite3.connect('database.db')
        cursor = db.cursor()
        with open('initial.sql', 'r', encoding='utf-8') as f:
            cursor.executescript(f.read())
        db.commit()
        cursor.close()
        db.close()
    with open('info.json') as f:
        data = json.load(f)
    bot.infinity_polling(skip_pending=True)
