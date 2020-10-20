def operation(type_operation, message):
    global chat_idG
    chat_idG = message.chat.id
    timeout = 5
    t1 = datetime.now()

    client.publish("/airport", payload=type_operation, qos=0, retain=False)
    while True:
        if mqtt_callback == b'engine_is_on':
            filework(1, 'heat off engine\n')
            cb_msg = "ВКЛЮЧЕН"
            chat_idG = message.chat_id
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


def security_operations(chat_id, payload, btn_status):
    client.publish("/airport_callback", payload="0", qos=0, retain=False)
    client.publish("/airport", payload=payload, qos=0, retain=False)
    filework(0, btn_status)
    bot.send_message(chat_id, text='oк', parse_mode='HTML', reply_markup=keyboard())
