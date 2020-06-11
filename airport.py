import telebot
from telebot import types
from datetime import datetime
import paho.mqtt.client as mqtt
from threading import Thread
import time
import os

bot = telebot.TeleBot(os.environ['TOKEN'])
mqtt_callback = 10

@bot.message_handler(commands=['start', 'go'])
def send_welcome(message):
    user_id = message.from_user.id
    if user_id == 441494356 or user_id == 630799281:
        bot.send_message(
            message.chat.id,
            '''Добро пожаловать, Милорд.
            ''',
            reply_markup=keyboard())


def filework(place, text): # place = 0-2 in list, text must be include "something\n"
    f = open('text.txt', 'r+')
    content = f.readlines()
    content[place] = text
    f.close()
    f = open('text.txt', 'w')
    f.close()
    f = open('text.txt', 'r+')
    for item in content:
        f.write("%s" % item)
    f.close()

def keyboard():
    f = open('text.txt', 'r')
    s = f.readlines()
    f.close()
    sec = s[0]
    eng = s[1]
    flr = s[2]
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    btn2 = types.KeyboardButton(eng) #объявляем кнопку
    btn3 = types.KeyboardButton(flr)
    btn1 = types.KeyboardButton(sec)
    markup.add(btn1)
    markup.add(btn2, btn3) #задаем кнопки, чере запятую
    return markup

@bot.message_handler(content_types=["text"]) #принимает любой текст фигню какую-то
def send_anytext(message):     #обратная связь, после получения команды с кнопки
    chat_id = message.chat.id
    user_id = message.from_user.id
    global chat_idG
    chat_idG = message.chat.id
    timeout = 3

    if user_id == 441494356 or user_id == 630799281:

        if message.text == 'heat on engine' or message.text == 'heat off engine':
            client.publish("/airport", payload="on_engine", qos=0, retain=False)
            t1 = datetime.now()
            while True:
                if mqtt_callback == b'engine_is_on':
                    filework(1, 'heat off engine\n')
                    bot.send_message(chat_id, text = 'ВКЛЮЧЕН', parse_mode='HTML', reply_markup=keyboard())
                    client.publish("/airport_callback", payload="0", qos=0, retain=False)
                    chat_idG = chat_id
                    break
                elif mqtt_callback == b'engine_is_off':
                    filework(1, 'heat on engine\n')
                    bot.send_message(chat_id, text = 'выключен', parse_mode='HTML', reply_markup=keyboard())
                    client.publish("/airport_callback", payload="0", qos=0, retain=False)
                    break
                elif (datetime.now()-t1).seconds > timeout:
                    bot.send_message(chat_id, text = 'Нет соединения', parse_mode='HTML', reply_markup=keyboard())
                    break

        if message.text == 'heat on floor' or message.text == 'heat off floor':
            client.publish("/airport", payload="on_floor", qos=0, retain=False)
            t1 = datetime.now()
            while True:
                if mqtt_callback == b'floor_is_on':
                    filework(2, 'heat off floor\n')
                    bot.send_message(chat_id, text = 'включен', parse_mode='HTML', reply_markup=keyboard())
                    client.publish("/airport_callback", payload="0", qos=0, retain=False)
                    break
                elif mqtt_callback == b'floor_is_off':
                    filework(2, 'heat on floor\n')
                    bot.send_message(chat_id, text = 'выключен', parse_mode="HTML", reply_markup=keyboard())
                    client.publish("/airport_callback", payload="0", qos=0, retain=False)
                    break
                elif (datetime.now()-t1).seconds > timeout:
                    bot.send_message(chat_id, text = 'Нет соединения', parse_mode='HTML', reply_markup=keyboard())
                    break

        if message.text == 'activate security':
            client.publish("/airport_callback", payload="0", qos=0, retain=False)
            filework(0, 'deactivate\n')
            bot.send_message(chat_id, text='oк', parse_mode='HTML', reply_markup=keyboard())

        if message.text == 'deactivate':
            filework(0, 'activate security\n')
            bot.send_message(chat_id, text='oк', parse_mode='HTML', reply_markup=keyboard())


def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("/airport_callback", "/airport_sensor")
# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg,): #(client, userdata, msg)
    print(msg.topic+" "+str(msg.payload))
    global mqtt_callback
    mqtt_callback = msg.payload
   # callback_msg = (msg.payload)

def check_upd(client):
    time_sensitive = 1 # время задержки между отправкой оповещений движении
    start_flg = True
    t3 = datetime.now()

    while True:
        if mqtt_callback == b'engine_is_off_auto':
            filework(1, 'heat on engine\n')
            print("вошел в функцию автоматического отключения двигателя")
            client.publish("/airport_callback", payload="0", qos=0, retain=False)
            global chat_idG
            bot.send_message(chat_idG, text = 'Автоматически выключен подогрев двигателя', parse_mode='HTML', reply_markup=keyboard())
            #дублирование для меня
            if chat_idG != 441494356:
                bot.send_message(441494356, text = 'Автоматически выключен подогрев двигателя', parse_mode='HTML', reply_markup=keyboard())


        f = open('text.txt', 'r')
        sec = f.read()
        f.close()
        if sec == 'deactivate':
            time.sleep(1)
            if (datetime.now() - t3).seconds > time_sensitive or start_flg:
                if mqtt_callback == b'motion':
                    client.publish("/airport_sensor", payload="0", qos=0, retain=False)
                    bot.send_message(chat_id = 441494356, text =  'Обнаружен котiк')
                    t3 = datetime.now() # время последнего обнаружения
                    start_flg = False


client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.username_pw_set("vcnpayei", os.environ['MQTT_PASS'])
client.connect("farmer.cloudmqtt.com", 12415, 60)
Thread(target=client.loop_forever, args=()).start()
Thread(target=check_upd, args=(client,)).start()
#bot.polling(none_stop=True)  # bot.infinity_polling(True). если бот будет падать, то поставить это

while True:
    try:
        bot.polling(none_stop=True)
    except Exception as E:
        time.sleep(1)
