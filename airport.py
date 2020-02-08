import telebot
from telebot import types
import paho.mqtt.client as mqtt
from threading import Thread
import time
import os
TOKEN = "1020204517:AAFYVzNcIg4DfT7aUGJjOx91ae8XVGXNHhg"
bot = telebot.TeleBot(TOKEN)

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
    markup.add(btn1) #задаем кнопки, чере запятую
    markup.add(btn2)
    return markup

@bot.message_handler(content_types=["text"]) #принимает любой текст фигню какую-то
def send_anytext(message):     #обратная связь, после получения команды с кнопки
    chat_id = message.chat.id
    user_id = message.from_user.id
    if user_id == 441494356 or user_id == 630799281:
        if message.text == 'Engine':
            client.publish("/airport", payload="on_engine", qos=0, retain=False)
            run = True
            while run:
                if mqtt_callback == b'engine_is_on' or mqtt_callback == b'engine_is_off':
                    run = False
                    if mqtt_callback == b'engine_is_on':
                        text = 'ВКЛЮЧЕН'
                        bot.send_message(chat_id, text, parse_mode='HTML', reply_markup=keyboard())
                        client.publish("/airport_callback", payload="0", qos=0, retain=False)
                    else:
                        text = 'выключен'
                        bot.send_message(chat_id, text, parse_mode='HTML', reply_markup=keyboard())
                        client.publish("/airport_callback", payload="0", qos=0, retain=False)

        if message.text == 'Floor':
            client.publish("/airport", payload="on_floor", qos=0, retain=False)
            run1 = True
            while run1:
                if mqtt_callback == b'floor_is_on' or mqtt_callback == b'floor_is_off':
                    run1 = False
                    if mqtt_callback == b'floor_is_on':
                        text = 'включен'
                        bot.send_message(chat_id, text, parse_mode='HTML', reply_markup=keyboard())
                        client.publish("/airport_callback", payload="0", qos=0, retain=False)
                    else:
                        text = 'выключен'
                        bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=keyboard())
                        client.publish("/airport_callback", payload="0", qos=0, retain=False)
        #    text = 'Подогрвев пола ВКЛЮЧЕН'
         #   bot.send_message(chat_id, text, parse_mode='HTML', reply_markup=keyboard())

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

def check_upd(client, message):
    run1 = True 
    while run1:
        if mqtt_callback == b'engine_is_off_auto':
            print("функция побежала")
            client.publish("/airport_callback", payload="0", qos=0, retain=False)
            text = 'Выключен подогрев двигателя по истечению времени'
            #chat_id = '441494356'
            bot.send_message(message.chat.id, text)
        run1 = True



client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.username_pw_set("vcnpayei","Mc55q9zvQ7Ek")
client.connect("farmer.cloudmqtt.com", 12415, 60)

#Thread(target=bot.polling, args=(True,)).start()
Thread(target=client.loop_forever, args=()).start()
Thread(target=check_upd, args=(client, message,)).start()
#bot.polling(none_stop=True)  # bot.infinity_polling(True). если бот будет падать, то поставить это

while True:
    try:
        bot.polling(none_stop=True)
    except Exception as E:
        time.sleep(1)
