
#include <MQTT.h>
#include <PubSubClient.h>
#include <ESP8266WiFi.h>
#include "Wire.h"

#define BUFFER_SIZE 100
#define RELAY_PIN1 12 //розетка на двигатель(правая)
#define RELAY_PIN2 13  // HIGH соотвествует выключенному положение реле
#define SENSOR_PIN1 15
#define SENSOR_PIN2 14


//const char *ssid =  "TP-Link_E82C";  // Имя вайфай точки доступа
//const char *pass =  "11774372"; // Пароль от точки доступа

const char *ssid =  "Mahsa Naumova";  // Имя вайфай точки доступа
const char *pass =  "masha1500"; // Пароль от точки доступа

bool off_rstflag = true;
bool automate_disable_flag = false;

const char *mqtt_server = "farmer.cloudmqtt.com"; // Имя сервера MQTT
const int mqtt_port = 12415; // Порт для подключения к серверу MQTT
const char *mqtt_user = "vcnpayei"; // Логин от сервер
const char *mqtt_pass = "Mc55q9zvQ7Ek"; // Пароль от сервера

uint32_t timestart;
uint32_t timeconst = 10800000; // врямя автоматического отключения 3 часа



WiFiClient wclient;
PubSubClient client(wclient, mqtt_server, mqtt_port);

void callback(const MQTT::Publish & pub) {     // Функция получения данных от сервера
  Serial.print(pub.topic());                // выводим в сериал порт название топика
  Serial.print(" => ");
  Serial.println(pub.payload_string());     // выводим в сериал порт значение полученных данных

  String payload = pub.payload_string();
  if (String(pub.topic()) == "/airport") {  //  проверяем из нужного ли нам топика пришли данные
    // rly01 = payload.toInt();         //  преобразуем полученные данные в тип integer
    // digitalWrite(RELAY_PIN1, rly01);      //  включаем или выключаем светодиод в зависимоти от полученных значений данных
    if (payload == "on_engine") {
      if (digitalRead(RELAY_PIN1) == HIGH) {
        digitalWrite(RELAY_PIN1, LOW);
        client.publish("/airport_callback", String("engine_is_on"));
      } else {
        digitalWrite(RELAY_PIN1, HIGH);
        client.publish("/airport_callback", String("engine_is_off"));
      }
      Serial.print(digitalRead(RELAY_PIN1));
      timestart = millis();                //запускаем таймер если включили
      automate_disable_flag = true;
    }
    if (payload == "on_floor") {
      if (digitalRead(RELAY_PIN2) == HIGH) {
        digitalWrite(RELAY_PIN2, LOW);
        client.publish("/airport_callback", String("floor_is_on"));
      } else {
        digitalWrite(RELAY_PIN2, HIGH);
        client.publish("/airport_callback", String("floor_is_off"));
      }Serial.print(digitalRead(RELAY_PIN2));
    }
  }
}

void setup() {
  Serial.begin(115200);
  pinMode(RELAY_PIN1, OUTPUT);
  pinMode(RELAY_PIN2, OUTPUT);
  pinMode(SENSOR_PIN1, INPUT);

}

void loop() {
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
        digitalWrite(RELAY_PIN1, HIGH);
        digitalWrite(RELAY_PIN2, HIGH);  //автоматическое выключение реле при потере связи с интернетом//  не работает
        Serial.println("Could not connect to MQTT server");
      }
    }
//автоматическое флажковое отключение при рестарте
    if (client.connected()) {
      if (off_rstflag == true) {
        digitalWrite(RELAY_PIN1, HIGH);
        digitalWrite(RELAY_PIN2, HIGH);
        off_rstflag = false;
      } delay(100);
      client.loop();
//отключение при достижении лимита времени подогрева двигателя
if (digitalRead(RELAY_PIN1) == LOW){
      if (millis() - timestart >= timeconst) {
        if (automate_disable_flag == true) {
          digitalWrite(RELAY_PIN1, HIGH);
          client.publish("/airport_callback", String("engine_is_off_auto"));
          automate_disable_flag = false;
        }
      } delay(100);
     }
    }
  }
if (digitalRead(SENSOR_PIN1) == LOW) or (digitalRead(SENSOR_PIN2) == LOW){
    Serial.println("котик обнаружен");
    client.publish("/airport_sensor", String("motion_detected"));
    }
}
