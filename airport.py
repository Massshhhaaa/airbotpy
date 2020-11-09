# topic /airort_callback used to recive messages from controller at the airport
# topic /airport_sensor used only for motions sensors which send "motion detected" there is movement
#
import telebot
from telebot import types
from datetime import datetime, timedelta
import paho.mqtt.client as mqtt
from threading import Thread
import time
import os
# from operations import operation, security_operations
bot = telebot.TeleBot(os.environ['TOKEN'])

#whitelist configuration
whitelist = list(map(int, os.environ['WHITE_LIST'].split()))


mqtt_callback = 10
mqtt_callback_sensor = 10


@bot.message_handler(commands=['start', 'go'], func=lambda message: message.chat.id in whitelist)
def send_welcome(message):
    bot.send_message(
        message.chat.id,
        ''' Мне нужно отправить команду, чтобы я могу выполнить действие.
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

def operation(type_operation, message):
    global chat_idG
    chat_idG = message.chat.id
    timeout = 5
    t1 = datetime.now()

    client.publish("/airport", payload=type_operation, qos=0, retain=False)
    while True:
        if mqtt_callback == b'engine_is_on':
            d = datetime.now() + timedelta(hours=3)
            filework(1, 'heat off engine\n')
            cb_msg = "Подогрев двигателя включен "+str(d.strftime("%d %b %H:%M"))+ "\nЗапланированное выключение через 3 часа"
            chat_idG = message.chat.id
            break

        elif mqtt_callback == b'engine_is_off':
            filework(1, 'heat on engine\n')
            cb_msg = 'выключен'
            break

        elif mqtt_callback == b'floor_is_on':
            filework(2, 'heat off floor\n')
            cb_msg = 'включен'
            break

        elif mqtt_callback == b'floor_is_off':
            filework(2, 'heat on floor\n')
            cb_msg = 'выключен'
            break

        elif (datetime.now()-t1).seconds > timeout:
            cb_msg = 'Нет соединения'
            break
    client.publish("/airport_callback", payload="0", qos=0, retain=False)
    bot.send_message(message.chat.id, text = cb_msg, parse_mode="HTML", reply_markup=keyboard())


def security_operations(message, payload, btn_status):

    client.publish("/airport_callback", payload="я ничтожество", qos=0, retain=False)
    client.publish("/airport", payload=payload, qos=0, retain=False)
    filework(0, btn_status)
    bot.send_message(message.chat.id, text='oк', parse_mode='HTML', reply_markup=keyboard())


@bot.message_handler(content_types=["text"], func=lambda message: message.chat.id in whitelist) #принимает любой текст фигню какую-то
def send_anytext(message):                                                                       #обратная связь, после получения команды с кнопки
    if message.text == 'heat on engine' or message.text == 'heat off engine':
        operation("on_engine", message)

    if message.text == 'heat on floor' or message.text == 'heat off floor':
        operation("on_floor", message)

    if message.text == 'activate security':
        security_operations(message, payload="security_activated", btn_status="deactivate\n")

    if message.text == 'deactivate':
        security_operations(message, payload="security_deactivated", btn_status="activate security\n")


def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("/airport_callback")
    client.subscribe("/airport_sensor")
# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg,):
    print(msg.topic+" "+str(msg.payload))
    global mqtt_callback
    global mqtt_callback_sensor
    mqtt_callback = msg.payload
    if msg.topic == "/airport_sensor":
        mqtt_callback_sensor = msg.payload


def check_upd(client):
    time_sensitive = 0 # время задержки между отправкой оповещений движении


    start_flg = True
    t3 = datetime.now()

    while True:
        if mqtt_callback == b'engine_is_off_auto':
            filework(1, 'heat on engine\n')
            print("вошел в функцию автоматического отключения двигателя")
            client.publish("/airport_callback", payload="0", qos=0, retain=False)
            for id in whitelist:
                bot.send_message(id, text = 'Автоматически выключен подогрев двигателя', parse_mode='HTML', reply_markup=keyboard())


        f = open('text.txt', 'r')
        sec = f.readline().rstrip()
        f.close()
        if sec == 'deactivate':
            time.sleep(1)
            if (datetime.now() - t3).seconds > time_sensitive or start_flg:
                if mqtt_callback_sensor == b'motion_detected':
                    client.publish("/airport_sensor", payload="0", qos=0, retain=False)
                    bot.send_message(chat_id = 441494356, text = 'Обнаружено движение', parse_mode='HTML')
                    t3 = datetime.now() # время последнего обнаружения
                    start_flg = False


client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.username_pw_set("vcnpayei", os.environ['MQTT_PASS'])
client.connect("farmer.cloudmqtt.com", 12415, 60)
Thread(target=client.loop_forever, args=()).start()
Thread(target=check_upd, args=(client,)).start()
 # bot.infinity_polling(True). если бот будет падать, то поставить это

while True:
    try:
        bot.polling(none_stop=True)
    except Exception as E:
        time.sleep(1)
