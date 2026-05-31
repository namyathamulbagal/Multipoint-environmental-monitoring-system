#include <WiFi.h>
#include <HTTPClient.h>
#include <Wire.h>
#include <SensirionI2cSht4x.h>

/* ================= WIFI SETTINGS ================= */
const char* ssid = "your wifi id";
const char* password = "your password";

/* ================= SERVER SETTINGS-changes for each device================= */
const char* serverName = "http://:5000/data";

SensirionI2cSht4x sht4x;

/* ================= ESP32 IDENTIFIER ================= */
const char* ESP_ID = "post_proximal"; // Changes for each ESP32
/* ================= LOGGING SETTINGS ================= */
unsigned long lastSendTime = 0;
const unsigned long sendInterval = 6000;  // 6 seconds

/* ================= WIFI CONNECT ================= */
void connectToWiFi() {
  Serial.print("Connecting to WiFi");
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\nWiFi Connected!");
  Serial.print("ESP32 IP Address: ");
  Serial.println(WiFi.localIP());
}

/* ================= SETUP ================= */
void setup() {
  Serial.begin(115200);
  delay(1000);

  Wire.begin();   // ESP32 default I2C pins: SDA=21, SCL=22

  // Initialize SHT4x sensor
  sht4x.begin(Wire, 0x44);
  Serial.println("SHT4x Initialized!");

  connectToWiFi();
}

void loop() {
  // Reconnect WiFi if disconnected
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi lost. Reconnecting...");
    connectToWiFi();
  }

  // Send data at intervals
  if (millis() - lastSendTime >= sendInterval) {
    lastSendTime = millis();

    float temperature = 0.0;
    float humidity = 0.0;
    uint16_t error;
    char errorMessage[256];

    error = sht4x.measureHighPrecision(temperature, humidity);
    if (error) {
      Serial.print("Sensor Error: ");
      errorToString(error, errorMessage, 256);
      Serial.println(errorMessage);
      return;
    }

    Serial.print("ESP: ");
    Serial.print(ESP_ID);
    Serial.print(" | Temp: ");
    Serial.print(temperature);
    Serial.print(" °C | RH: ");
    Serial.println(humidity);

    // Send data to Flask server
    if (WiFi.status() == WL_CONNECTED) {
      HTTPClient http;
      http.begin(serverName);
      http.addHeader("Content-Type", "application/json");

      String jsonData = "{";
      jsonData += "\"esp_id\":\"" + String(ESP_ID) + "\",";
      jsonData += "\"time\":" + String(millis()) + ",";
      jsonData += "\"temperature\":" + String(temperature, 2) + ",";
      jsonData += "\"humidity\":" + String(humidity, 2);
      jsonData += "}";

      int httpResponseCode = http.POST(jsonData);

      Serial.print("HTTP Response: ");
      Serial.println(httpResponseCode);

      http.end();
    }
  }
}
