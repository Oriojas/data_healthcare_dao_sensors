#include "env.h"
#include <Wire.h>
#include <WiFiClient.h>
#include <ESP8266WiFi.h>
#include <ESP8266WebServer.h>
#include <ESP8266HTTPClient.h>
#include "MAX30100_PulseOximeter.h"


#define REPORTING_PERIOD_MS     4000


float BPM, SpO2;

String serverName = "http://ec2-100-24-74-70.compute-1.amazonaws.com:8088/send_data/";

PulseOximeter pox;

uint32_t tsLastReport = 0;

void(* resetFunc) (void) = 0;

ESP8266WebServer server(80);

WiFiClient wifiClient;

void setup() {
  Serial.begin(115200);
  pinMode(16, OUTPUT);
  delay(100);

  Serial.println("Connecting to ");
  Serial.println(ssid);

  //connect to your local wi-fi network
  WiFi.begin(ssid, password);
  
  //check wi-fi is connected to wi-fi network
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.print(".");
  }
  Serial.println("");
  Serial.println("WiFi connected..!");
  Serial.print("Got IP: ");  Serial.println(WiFi.localIP());
  
  server.on("/", handle_OnConnect);
  server.onNotFound(handle_NotFound);

  server.begin();
  Serial.println("HTTP server started");
  
  Serial.print("Initializing pulse oximeter..");

  if (!pox.begin()) {
    Serial.println("FAILED");
    for (;;);
  } else {
    Serial.println("SUCCESS");
    
  }
}
void loop() { 

  pox.update();
  
  if (millis() - tsLastReport > REPORTING_PERIOD_MS) {

    BPM = pox.getHeartRate();
    SpO2 = pox.getSpO2();

    Serial.print("BPM: ");
    Serial.println(BPM);

    Serial.print("SpO2: ");
    Serial.print(int(SpO2));
    Serial.println("%");
    
    if (SpO2 > 0 & SpO2 < 100) {

      HTTPClient http;
      
      String serverPath = serverName + "?user=" + user + "&bpm=" + BPM + "&spo2=" + int(SpO2); 
           
      http.begin(wifiClient, serverPath);                         
      int httpCode = http.GET();      

      Serial.print("Response: ");
      Serial.println(httpCode);
      Serial.println(user);

      if (httpCode < 0) {

          resetFunc();
        
        }        
          
      http.end();
      
      tsLastReport = millis();
       
    } else {

        tsLastReport = millis();
      
      }

    Serial.println("*********************************");
    Serial.println();
    
  }


}

void handle_OnConnect() {

  server.send(200, "text/plain", "OK");
}

void handle_NotFound() {
  server.send(404, "text/plain", "Not found");
}
