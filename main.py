import telebot
from telebot import types
from dotenv import dotenv_values
import json, os

config = dotenv_values('.env')
token = config['TOKEN']

bot = telebot.TeleBot(token)

# Генерация списка кнопок пролистывания концертов
def gen_markup_for_buy(msg_id):
    markup = types.InlineKeyboardMarkup()
    markup.row_width = 1
    # ⬅️➡️
    left_but = types.InlineKeyboardButton('⬅️', callback_data='prev')
    right_but = types.InlineKeyboardButton('➡️', callback_data='next')
    back_but = types.InlineKeyboardButton('Назад', callback_data=f'/start {msg_id}')
    markup.row(left_but, right_but)
    markup.add(back_but)
    return markup

# Обработка стартовой команды
@bot.message_handler(commands=['start'])
def start_message(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buy_tick_but = types.KeyboardButton('Купить билеты!')
    markup.add(buy_tick_but)
    bot.send_message(message.chat.id, 'Добро пожаловать в билетную кассу театра имени А.Боба!')
    bot.send_message(message.chat.id, 'Выберете действие, что вы хотите совершить.', reply_markup=markup)

# Обработка сообщений
@bot.message_handler(func=lambda message: True)
def reply_markup_reaction(message):
    if message.text == 'Купить билеты!':

        msg = bot.send_message(message.chat.id, 'Выводится список ближайших концертов...',
                         reply_markup=types.ReplyKeyboardRemove())
        bot.send_message(message.chat.id, 'Фиг те, а не билеты!', reply_markup=gen_markup_for_buy(msg.message_id))

i = 1

# Обработка нажатий на кнопки под сообщениями
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    global i
    if call.data.startswith('/start'):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        buy_tick_but = types.KeyboardButton('Купить билеты!')
        markup.add(buy_tick_but)
        msg_id = call.data.split()[1]
        bot.edit_message_text('Добро пожаловать в билетную кассу театра имени А.Боба!',
                              call.message.chat.id,
                              call.message.message_id,
                              reply_markup=None)
        bot.send_message(call.message.chat.id, 'Выберете действие, что вы хотите совершить.',  reply_markup=markup)
        # bot.delete_message(call.message.chat.id, int(msg_id))
    elif call.data == 'prev':
        chat_id =str(call.message.chat.id)
        with open('info.json') as f: data = json.load(f)
        if not chat_id in data['index']: data['index'][call.message.chat.id] = 0
        data['index'][call.message.chat.id]-=1
        i = data['index'][call.message.chat.id]
        with open('info.json','w') as f: json.dump(data,f)
        bot.edit_message_text(f'Message: {i}', call.message.chat.id, call.message.message_id, reply_markup=gen_markup_for_buy(call.message.message_id))
    elif call.data == 'next':
        chat_id = str(call.message.chat.id)
        with open('info.json') as f:
            data = json.load(f)
        if not chat_id in data['index']: data['index'][call.message.chat.id] = 0
        data['index'][call.message.chat.id] += 1
        i = data['index'][call.message.chat.id]
        with open('info.json', 'w') as f:
            json.dump(data, f)
        bot.edit_message_text(f'Message: {i}', call.message.chat.id, call.message.message_id, reply_markup=gen_markup_for_buy(call.message.message_id))

bot.polling(none_stop=True)

if __name__=='__main__':
    if not os.path.isfile('info.json'):
        with open('info.json','w+') as f: json.dump({'index':dict()}, f)
    bot.infinity_polling()