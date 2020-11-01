#include <MsTimer2.h>
#include <MQTT.h>
#include <PubSubClient.h>
#include <ESP8266WiFi.h>
#include "Wire.h"

#define BUFFER_SIZE 100
#define RELAY_PIN1 12 //розетка на двигатель(правая)
#define RELAY_PIN2 13  // HIGH соотвествует выключенному положение реле
#define SENSOR_PIN1 5

// топик /airport используется для отправки с бота на контроллер запросов
// /airport_callback используется для отправки с контроллера на сервер ответов
// /airport_sensor для результатов датчика движения
//

const char *ssid =  "TP-Link_E82C";  // Имя вайфай точки доступа
const char *pass =  "11774372"; // Пароль от точки доступа

//const char *ssid =  "Mahsa Naumova";  // Имя вайфай точки доступа
//const char *pass =  "masha1500"; // Пароль от точки доступа

bool off_rstflag = true;
bool automate_disable_flag = false;
bool security_condition = false; //true is on

const char *mqtt_server = "farmer.cloudmqtt.com"; // Имя сервера MQTT
const int mqtt_port = 12415; // Порт для подключения к серверу MQTT
const char *mqtt_user = "vcnpayei"; // Логин от сервер
const char *mqtt_pass = "Mc55q9zvQ7Ek"; // Пароль от сервера
const int delayfor = 15;

uint32_t timestart;
uint32_t timeconst = 10800000; // врямя автоматического отключения 3 часа в мс

int number = 0;

WiFiClient wclient;
PubSubClient client(wclient, mqtt_server, mqtt_port);

void callback(const MQTT::Publish & pub) {     // Функция получения данных от сервера
  Serial.print(pub.topic());                // выводим в сериал порт название топика
  Serial.print(" => ");
  Serial.println(pub.payload_string());     // выводим в сериал порт значение полученных данных

  String payload = pub.payload_string();
  if (String(pub.topic()) == "/airport") {  //  проверяем из нужного ли нам топика пришли данные

    if (payload == "on_engine") {
      if (digitalRead(RELAY_PIN1) == HIGH) {
        digitalWrite(RELAY_PIN1, LOW);
        client.publish("/airport_callback", String("engine_is_on"));
      } else {
        digitalWrite(RELAY_PIN1, HIGH);
        client.publish("/airport_callback", String("engine_is_off"));
      }
      timestart = millis();
      automate_disable_flag = true;
    }

    if (payload == "on_floor") {
      if (digitalRead(RELAY_PIN2) == HIGH) {
        digitalWrite(RELAY_PIN2, LOW);
        client.publish("/airport_callback", String("floor_is_on"));
      } else {
        digitalWrite(RELAY_PIN2, HIGH);
        client.publish("/airport_callback", String("floor_is_off"));
      }
    }

    if (payload == "security_activated") {
      security_condition = true;
      client.publish("/airport_callback", String("now_security_activate"));
    }

    if (payload == "security_deactivated") {
      security_condition = false;
      client.publish("/airport_callback", String("now_security_deactive"));
    }

  }
}

void setup() {
  Serial.begin(115200);
  pinMode(RELAY_PIN1, OUTPUT);
  pinMode(RELAY_PIN2, OUTPUT);

  attachInterrupt(SENSOR_PIN1, stateChange, FALLING); // Set the interrupt function, interrupt pin is digital pin D2, interrupt service function is stateChange (), when the D2 power change from high to low , the trigger interrupt.
  MsTimer2::set(500, Handle); // Set the timer interrupt function, running once Handle() function per 1000ms
  MsTimer2::start();//Start timer interrupt function


}

void loop() {

  AutoDisableRestasrt();
  // подключаемся к wi-fi
  if (WiFi.status() != WL_CONNECTED) {
    Serial.print("Connecting to ");
    Serial.print(ssid);
    Serial.println("...");
    WiFi.begin(ssid, pass);

    if (WiFi.waitForConnectResult() != WL_CONNECTED)
      return;
    Serial.println("WiFi connected");
  }

  // подключаемся к MQTT серверу
  if (WiFi.status() == WL_CONNECTED) {
    if (!client.connected()) {
      Serial.println("Connecting to MQTT server");
      if (client.connect(MQTT::Connect("arduinoClient2")
                         .set_auth(mqtt_user, mqtt_pass))) {
        Serial.println("Connected to MQTT server");
        client.set_callback(callback);
        client.subscribe("/airport");      // подписывааемся по топик с данными
      } else {
        Serial.println("Could not connect to MQTT server");
      }
    }

    if (client.connected()) {

      client.loop();
      AutoDisableTimeLimit();

    }
  }

}


void stateChange() {
  number++;  //Interrupted once, the number + 1
}

void Handle() { //Timer service function
  if ((number > 1) && (security_condition == true )) { //If in the set of the interrupt time the number more than 1 times, then means have detect moving objects,This value can be adjusted according to the actual situation, which is equivalent to adjust the threshold of detection speed of moving objects.
    client.publish("/airport_sensor", String("motion_detected"));
    number = 0; //Cleare the number, so that it does not affect the next trigger
  }
  else
    number = 0;
}

void AutoDisableTimeLimit () {  //отключение при достижении лимита времени подогрева двигателя
  if ((digitalRead(RELAY_PIN1) == LOW) && (millis() - timestart >= timeconst) && (automate_disable_flag == true)) {
    digitalWrite(RELAY_PIN1, HIGH);
    client.publish("/airport_callback", String("engine_is_off_auto"));
    automate_disable_flag = false;
  } delay(delayfor);
}


void AutoDisableRestasrt () { //автоматическое флажковое отключение при рестарте
  if (off_rstflag == true) {
    digitalWrite(RELAY_PIN1, HIGH);
    digitalWrite(RELAY_PIN2, HIGH);
    off_rstflag = false;
  } delay(delayfor);
}
