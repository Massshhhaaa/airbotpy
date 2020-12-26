
import telebot
from telebot import types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

from datetime import datetime, timedelta

import paho.mqtt.client as mqtt
from threading import Thread

import time
import os

# from operations import operation, security_operations
bot = telebot.TeleBot(os.environ['TOKEN'])

#whitelist configuration
whitelist = list(map(int, os.environ['WHITE_LIST'].split()))



off = u'\U000025EF'
on = u'\U00002B24'
toright = u'\U00002192'
toleft = u'\U00002190'
upd = u'\U000021BB'

status = {
    'Signaling': off,
    'HeatFloor': off,
    'HeatEngine': off,
}

class Command:
    def __init__(self, name, topic):
        self.name = name
        self.topic = topic 
        self.status = False
        self.backTopic = topic + '/back'


    def send(self, call): 
        payload = '99'
        if self.status == True: 
            payload = '0'
        else: 
            payload = '1'

        client.publish(self.topic, payload=payload, qos=1, retain=False)
        self.call = call 

    def react(self): #каллбэк получен значит можно обновлять клавиатуру телеги
        self.status = not self.status
        
        if self.status:
            status[self.name] = on
            bot.answer_callback_query(self.call.id, "Включен")
        else: 
            status[self.name] = off
            bot.answer_callback_query(self.call.id, "Выключен")

        bot.answer_callback_query(self.call.id, "включен")
        bot.edit_message_text(main_markup_info(), self.call.message.chat.id, self.call.message.message_id,
                              reply_markup=main_markup())


def main_markup():
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("Сигнализация  "+ status.get('Signaling'), callback_data="Signaling"),
        InlineKeyboardButton("Подогрев пола  "+  status.get('HeatFloor'), callback_data="HeatFloor"),
        InlineKeyboardButton("Подогрев двигателя  "+ status.get('HeatEngine'), callback_data="HeatEngine"),
    )
    markup.row(
        InlineKeyboardButton("Сводка", callback_data="Report"),
        InlineKeyboardButton("Обновить " + upd, callback_data="Update"),
    )
    return markup

def main_markup_info():
    d = datetime.now() + timedelta(hours=0)
    text = """
Информация по состоянию представлена на """ + str(d.strftime("%d %b %H:%M") + """ мск""")
    return text


@bot.message_handler(commands=['start', 'help'],  func=lambda message: message.chat.id in whitelist)
@bot.message_handler(content_types=["text"],  func=lambda message: message.chat.id in whitelist)
def send_welcome(message):
    bot.send_message(message.chat.id, text=main_markup_info(), reply_markup=(main_markup()))



@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):

    # MAIN CALLBACKS
    if call.data == "Signaling":
        motionSensor.send(call)

    # MANAGEMENT CALLBACKS
    elif call.data == "HeatFloor":
        heatFloor.send(call)

    elif call.data == "HeatEngine":
        heatEngine.send(call)


    elif call.data == "Update":
        bot.edit_message_text(main_markup_info(), call.message.chat.id, call.message.message_id, reply_markup=main_markup())

    elif call.data == "Report":
        text = """
Сводка:
----------------------------
подогрев пола          
подогрев двигателя     
----------------------------

Последняя активность внутри ангара была 24 Декабря в 11:20
"""
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id,
                              reply_markup=main_markup())

heatEngine = Command("HeatEngine", "loseev5@gmail.com/engine_heating") 
heatFloor = Command('HeatFloor', '/floor_heating')
motionSensor = Command('Signaling', '/motion_sensor')



def motionNotification():
    time_sensitive = 0 # время задержки между отправкой оповещений движении


    start_flg = True
    t3 = datetime.now()

    # if (datetime.now() - t3).seconds > time_sensitive or start_flg:
    bot.send_message(chat_id = 441494356, text = 'Обнаружено движение', parse_mode='HTML')
    t3 = datetime.now() # время последнего обнаружения
    start_flg = False


# MQTT SETUP
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    client.subscribe( heatEngine.backTopic)
    client.subscribe( heatFloor.backTopic)
    client.subscribe( motionSensor.backTopic)
    client.subscribe('/motion_sensor/data')

def on_message(client, userdata, msg,):
    print(msg.topic+" "+str(msg.payload))

    if msg.topic == heatEngine.backTopic:
        heatEngine.react()

    elif msg.topic == heatFloor.backTopic:
        heatFloor.react()

    elif msg.topic == motionSensor.backTopic:
        motionSensor.react()

    elif msg.topic == '/motion_sensor/data':
        motionNotification()


client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
# client.username_pw_set("vcnpayei", os.environ['MQTT_PASS'])
# client.connect("farmer.cloudmqtt.com", 12415, 60)
client.username_pw_set("loseev5@gmail.com", "D@zxTFkNT6XAHmv")
client.connect("maqiatto.com", 1883, 60)
Thread(target=client.loop_forever, args=()).start()



while True:
    try:
        bot.polling(none_stop=True)
    except Exception as E:
        time.sleep(1)
