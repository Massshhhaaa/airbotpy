#include <PubSubClient.h>
#include <ESP8266WiFi.h>

#define BUFFER_SIZE 100
#define RELAY_PIN1 D6 //розетка на двигатель(правая)
#define RELAY_PIN2 D7  // HIGH соотвествует выключенному положение реле
#define SENSOR_PIN1 D4

#define ENGINEHEATING "/engine_heating"
#define FLOORHEATING "/floor_heating"
#define MOTION_SENSOR "/motion_sensor"

#define DATA_MOTION_SENSOR "/motion_sensor/data"

#define MOTION_SENS 7 //число обнаруженных движения для функции отправки
#define MOTION_SENS_TIME 50

//const char *ssid =  "TP-Link_E82C"; 
//const char *pass =  "11774372"; 

const char *ssid =  "WiFi-DOM.RU-7630"; 
const char *pass =  "JVLuSoUA"; 

bool off_rstflag = true;
bool automate_disable_flag = false;

const char *mqtt_server = "farmer.cloudmqtt.com"; 
 const int mqtt_port = 12415; 
 const char *mqtt_user = "vcnpayei";
 const char *mqtt_pass = "Mc55q9zvQ7Ek"; 

uint32_t motionT = MOTION_SENS_TIME;  
uint32_t engineT;
uint32_t timeconst = 10800000; // врямя автоматического отключения 3 часа


 int t = millis();

 volatile int count = 0;
 volatile int ledState = LOW; //Define ledOut, default is off


WiFiClient wclient;
PubSubClient client(wclient, mqtt_server, mqtt_port);


 class Element {
  public: 
      String topic;
      String backTopic;
      int pin;
      bool state = false;
      
     Element(int initPin, String initTopic){
     topic = initTopic;
     pin = initPin;
     backTopic = topic + "/back";
    }

        
        void enable() {
                state = true;
                digitalWrite(pin, LOW);
                client.publish(backTopic, String("1"));
                Serial.println("pin:  enabled");

                if (topic == "/engine_heating"){automate_disable_flag = true; engineT = millis();}
              }

    
         void disable() {
             state = false;
              digitalWrite(pin, HIGH);
              client.publish(backTopic, String("0"));
              Serial.println("pin: disabled");
            }
              
            
      void main(String payload, String pubTopic){
           
          if (topic == pubTopic) {
          Serial.println("topic совпадает");
          
              if (payload == "1") {enable();}
              if (payload == "0") {disable();}

          Serial.print("STATE: ");Serial.println(state);
         }

      
  
  } 
          
};

class Sensor : public Element{
  public:
    Sensor(int initPin, String initTopic):Element(initPin, initTopic){};
        
      void process() {
        delay(1);
        if( count > MOTION_SENS && millis() - motionT < MOTION_SENS_TIME) {
            ledState = HIGH;
            digitalWrite(2, state);
            client.publish(DATA_MOTION_SENSOR, String("1"));
            Serial.println("Сообщение об обнаружении движения отправлено");
            count=0;        
       } else{ count=0; }

      }     
};

  Element engineHeating(RELAY_PIN1, ENGINEHEATING), floorHeating(RELAY_PIN2, FLOORHEATING);

  Sensor motionSensor(SENSOR_PIN1, ENGINEHEATING);
  
    
void callback(const MQTT::Publish & pub) {     // Функция получения данных от сервера
  Serial.print(pub.topic());                // выводим в сериал порт название топика
  Serial.print(" => ");
  Serial.println(pub.payload_string());     // выводим в сериал порт значение полученных данных
  
  String payload = pub.payload_string();
  String pubTopic = pub.topic();

      
  engineHeating.main(payload, pubTopic);
  floorHeating.main(payload, pubTopic);
  motionSensor.main(payload, pubTopic);

      
}


ICACHE_RAM_ATTR void blinks() {
  Serial.println("void blink() - движение опознано");
  count++;
  motionT = millis();
}




void setup() {
  blinks();
  
  Serial.begin(115200);
  pinMode(RELAY_PIN1, OUTPUT);
  pinMode(RELAY_PIN2, OUTPUT);

  pinMode (LED_BUILTIN, OUTPUT);
  pinMode (SENSOR_PIN1, INPUT_PULLUP);
  
//  –Задаем  функцию blink , которая будет вызвана по внешнему прерыванию.
  attachInterrupt ( digitalPinToInterrupt (SENSOR_PIN1), blinks, CHANGE);

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

        client.subscribe(ENGINEHEATING);
        client.subscribe(FLOORHEATING);  
        client.subscribe(MOTION_SENSOR);    
        
      }
    }
  
    if (client.connected()) {
    
      client.loop();
      //автоматическое флажковое отключение при рестарте
      if (off_rstflag == true) {

        Serial.println("Рестарт..Выключение реле..");
        engineHeating.disable();
        floorHeating.disable();
        off_rstflag = false;
      }
      
        //отключение при достижении лимита времени подогрева двигателя
       if (digitalRead(RELAY_PIN1) == LOW && millis() - engineT >= timeconst && automate_disable_flag == true){
          engineHeating.disable();
          automate_disable_flag = false;
       }
           

           
    }
    motionSensor.process();
    
   
  }
  delay(1);
}



//http://arduino.ru/forum/obshchii/datchik-hb100-kak-opredelit-nalichie-dvizheniya
//-----Значение readMean и readMedian нужно подбирать в зависимости от зашумленности...

//
//const int ledPin =  7;      
//int ledState = LOW; 
//long previousMillis = 0;
//long interval = 1000;
//
//int sensorPin = A0; // номер аналогового входа
//
//// функция считывает аналоговый вход заданное количество раз
//// и возвращает отфильтрованное значение
//int readMean(int pin, int samples){
//  // переменная для хранения суммы считанных значений
//  int sum = 0;
//  // чтение и складывание значений
//  for (int i = 0; i < samples; i++){
//    sum = sum + analogRead(pin);
//  }
//  // делим сумму значений на количество измерений
//  sum = sum/samples;
//  // возвращаем среднее значение
//  return sum;
//}
//
//// функция считывает аналоговый вход заданное количество раз
//// и возвращает медианное отфильтрованное значение
//int readMedian (int pin, int samples){
//  // массив для хранения данных
//  int raw[samples];
//  // считываем вход и помещаем величину в ячейки массива
//  for (int i = 0; i < samples; i++){
//    raw[i] = analogRead(pin);
//  }
//  // сортируем массив по возрастанию значений в ячейках
//  int temp = 0; // временная переменная
//
//  for (int i = 0; i < samples; i++){
//    for (int j = 0; j < samples - 1; j++){
//      if (raw[j] > raw[j + 1]){
//        temp = raw[j];
//        raw[j] = raw[j + 1];
//        raw[j + 1] = temp;
//      }
//    }
//  }
//  // возвращаем значение средней ячейки массива
//  return raw[samples/2];
//}
//void setup(){
//  Serial.begin(9600);
//  pinMode(7, OUTPUT); 
//}
//void loop(){
//  // выводим значение на аналоговом входе в монитор порта
//  Serial.print(analogRead(sensorPin));
//  Serial.print(" ");
//  // выводим среднеизмеренное значение
//  Serial.print(readMean(sensorPin, 15));
//  Serial.print(" ");
//  // выводим медианное отфильтрованное значение
//  Serial.println(readMedian(sensorPin, 15));
//  delay(100);
//  if ((readMean(sensorPin, 15) < 140 || readMean(sensorPin, 15)>850 ) && (readMedian(sensorPin, 15)< 140 || readMedian(sensorPin, 15)> 850) ){
//    ledState=HIGH;      
//    digitalWrite(ledPin, ledState);
//  }
//   unsigned long currentMillis = millis();  
//         if(currentMillis - previousMillis > interval) {
//       previousMillis = currentMillis; 
//    if (ledState == HIGH)
//      ledState = LOW;
//    digitalWrite(ledPin, ledState);
//         }
//  }
//
//
//
//
//
//







