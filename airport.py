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
    btn3 = types.KeyboardButton('engine') #объявляем кнопку
    btn4 = types.KeyboardButton('floor')
    btn1 = types.KeyboardButton('activate security')
    btn2 = types.KeyboardButton('deactivate')
    markup.add(btn1, btn2)
    markup.add(btn3)
    markup.add(btn4) #задаем кнопки, чере запятую
    return markup

@bot.message_handler(content_types=["text"]) #принимает любой текст фигню какую-то
def send_anytext(message):     #обратная связь, после получения команды с кнопки
    chat_id = message.chat.id
    user_id = message.from_user.id
    global chat_idG
    chat_idG = message.chat.id
    timeout = 4

    if user_id == 441494356 or user_id == 630799281:

        if message.text == 'engine':
            client.publish("/airport", payload="on_engine", qos=0, retain=False)
            t1 = datetime.now()
            while True:
                if mqtt_callback == b'engine_is_on':
                        bot.send_message(chat_id, text = 'ВКЛЮЧЕН', parse_mode='HTML', reply_markup=keyboard())
                        client.publish("/airport_callback", payload="0", qos=0, retain=False)
                        chat_idG = chat_id
                        break
                elif mqtt_callback == b'engine_is_off':
                        bot.send_message(chat_id, text = 'выключен', parse_mode='HTML', reply_markup=keyboard())
                        client.publish("/airport_callback", payload="0", qos=0, retain=False)
                        break
                elif (datetime.now()-t1).seconds > timeout:
                    bot.send_message(chat_id, text = 'Cоединение не установлено', parse_mode='HTML', reply_markup=keyboard())
                    break

        if message.text == 'floor':
            client.publish("/airport", payload="on_floor", qos=0, retain=False)
            t1 = datetime.now()
            while True:
                if mqtt_callback == b'floor_is_on':
                        bot.send_message(chat_id, text = 'включен', parse_mode='HTML', reply_markup=keyboard())
                        client.publish("/airport_callback", payload="0", qos=0, retain=False)
                        break
                elif mqtt_callback == b'floor_is_off':
                        bot.send_message(chat_id, text = 'выключен', parse_mode="HTML", reply_markup=keyboard())
                        client.publish("/airport_callback", payload="0", qos=0, retain=False)
                        break
                elif (datetime.now()-t1).seconds > timeout:
                    bot.send_message(chat_id, text = 'Cоединение не установлено', parse_mode='HTML', reply_markup=keyboard())
                    break

        if message.text == 'activate security':
            client.publish("/airport_callback", payload="0", qos=0, retain=False)
            f = open('text.txt', 'w')
            f.write("sec = True")
            f.close()
            bot.send_message(chat_id, text='Система активирована', parse_mode='HTML', reply_markup=keyboard())

        if message.text == 'deactivate':
            f = open('text.txt', 'w')
            f.write("sec = False")
            f.close()
            bot.send_message(chat_id, text='Деактивировано', parse_mode='HTML', reply_markup=keyboard())


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
    time_sensitive = 30 # время задержки между отправкой оповещений движении
    start_flg = True
    t3 = datetime.now()

    while True:
        if mqtt_callback == b'engine_is_off_auto':
            print("вошел в функцию автоматического отключения")
            client.publish("/airport_callback", payload="0", qos=0, retain=False)
            global chat_idG
            bot.send_message(chat_idG, text = 'Автоматически выключен подогрев двигателя')
            #дублирование для меня
            if chat_idG != 441494356:
                bot.send_message(441494356, text = 'Автоматически выключен подогрев двигателя')

        f = open('text.txt', 'r')
        sec = f.read()
        f.close()
        if sec == 'sec == True':
            time.sleep(2)
            if (datetime.now() - t3).seconds > time_sensitive or start_flg:
                if mqtt_callback == b'motion_detected':
                    client.publish("/airport_callback", payload="0", qos=0, retain=False)
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
