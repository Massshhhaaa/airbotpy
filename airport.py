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

def keyboard():
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    btn1 = types.KeyboardButton('Engine') #объявляем кнопку
    btn2 = types.KeyboardButton('Floor')
    markup.add(btn1, btn2) #задаем кнопки, чере запятую
   #markup.add(btn2)
    return markup

@bot.message_handler(content_types=["text"]) #принимает любой текст фигню какую-то
def send_anytext(message):     #обратная связь, после получения команды с кнопки
    chat_id = message.chat.id
    user_id = message.from_user.id
    global chat_idG
    chat_idG = message.chat.id
    error_time = 5

    if user_id == 441494356 or user_id == 630799281:

        if message.text == 'Engine':
            client.publish("/airport", payload="on_engine", qos=0, retain=False)
            t1 = datetime.now()
            while True:
                if mqtt_callback == b'engine_is_on' or mqtt_callback == b'engine_is_off':
                    if mqtt_callback == b'engine_is_on':
                        text = 'ВКЛЮЧЕН'
                        bot.send_message(chat_id, text, parse_mode='HTML', reply_markup=keyboard())
                        client.publish("/airport_callback", payload="0", qos=0, retain=False)
                        break
                    else:
                        text = 'выключен'
                        bot.send_message(chat_id, text, parse_mode='HTML', reply_markup=keyboard())
                        client.publish("/airport_callback", payload="0", qos=0, retain=False)
                        break
                if (datetime.now()-t1).seconds > error_time:
                    bot.send_message(chat_id, text = 'соединение не установлено', parse_mode='HTML', reply_markup=keyboard())
                    break


        if message.text == 'Floor':
            client.publish("/airport", payload="on_floor", qos=0, retain=False)
            t1 = datetime.now()
            while True:
                if mqtt_callback == b'floor_is_on' or mqtt_callback == b'floor_is_off':
                    if mqtt_callback == b'floor_is_on':
                        text = 'включен'
                        bot.send_message(chat_id, text, parse_mode='HTML', reply_markup=keyboard())
                        client.publish("/airport_callback", payload="0", qos=0, retain=False)
                        break
                    else:
                        text = 'выключен'
                        bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=keyboard())
                        client.publish("/airport_callback", payload="0", qos=0, retain=False)
                        break
                if (datetime.now()-t1).seconds > error_time:
                    bot.send_message(chat_id, text = 'соединение не установлено', parse_mode='HTML', reply_markup=keyboard())
                    break


def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("/airport_callback")
# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg,): #(client, userdata, msg)
    print(msg.topic+" "+str(msg.payload))
    global mqtt_callback
    mqtt_callback = msg.payload
   # callback_msg = (msg.payload)

def check_upd(client):
    while True:
        if mqtt_callback == b'engine_is_off_auto':
            print("вошел в функцию автоматического отключения")
            client.publish("/airport_callback", payload="0", qos=0, retain=False)
            text = 'Автоматически выключен подогрев двигателя'
            global chat_idG
            bot.send_message(441494356, text)
            #дублирование для меня
            if chat_idG != 441494356:
                bot.send_message(441494356, text)



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
