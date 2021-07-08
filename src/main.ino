// Wire Master Writer
// by Nicholas Zambetti <http://www.zambetti.com>

// Demonstrates use of the Wire library
// Writes data to an I2C/TWI slave device
// Refer to the "Wire Slave Receiver" example for use with this

// Created 29 March 2006

// This example code is in the public domain.


#include <Wire.h>
#include <ESP8266WiFi.h>

#define PORT 8101

WiFiServer server(PORT);

void setup()
{
  Serial.begin(115200);

  WiFi.hostname("tooth1");
  WiFi.begin("robotoverlords", "TODO");

  Serial.print("Connecting");
  while (WiFi.status() != WL_CONNECTED)
  {
    delay(500);
    Serial.print(".");
  }
  Serial.println();

  Serial.print("Connected, IP address: ");
  Serial.println(WiFi.localIP());

  // TODO Wire.setClock(400000);

  Wire.begin(); // join i2c bus (address optional for master)

  Serial.print("Listening on port ");
  Serial.println(PORT);
  server.begin();

  Serial.println("Setup complete");
}


#define DEV1 64
#define DEV2 65
// 64

void writeBuf(uint8_t device, uint8_t* buf, uint16_t len) {
  Wire.beginTransmission(device);
  Wire.write(buf, len);
  Wire.endTransmission();
}

void writeFreq(uint8_t device, uint16_t fA, uint16_t fB, uint8_t vA, uint8_t vB) {
  uint8_t buf[6];
  buf[0] = fA & 0xff;
  buf[1] = (fA >> 8) & 0xff;
  buf[2] = fB & 0xff;
  buf[3] = (fB >> 8) & 0xff;
  buf[4] = vA;
  buf[5] = vB;
  writeBuf(device, buf, 6);
}

// Data is loaded onto the microcontroller in "frames" (chunks),
// effectively making this a ring buffer with NFRAME items of length
// FRAME_SAMPLES.
// Note the STM32F030F4 has only 4K SRAM so this buffer must stay small
#define NFRAME 4
#define FRAME_SAMPLES 200*2
uint8_t wav_buffer[NFRAME][FRAME_SAMPLES];
// TODO 2 channel buffer
volatile uint8_t frame_idx;  // Where to read sample data
volatile uint8_t frame_buf_idx; // Where to write the next incoming frame
volatile uint16_t sample_idx; // Which sample in frame_idx to read next
void writeFrame(uint8_t device, uint8_t* frameptr) {
  Wire.beginTransmission(device);
  Wire.write(frameptr, FRAME_SAMPLES);
  Wire.endTransmission();
}

void chord(uint16_t fA, uint16_t fB, uint16_t fC, uint8_t vol) {
  writeFreq(DEV1, fA, 0, vol, vol);
  writeFreq(DEV2, fB, fC, vol, vol);
}

void off() {
  writeFreq(DEV1, 0, 0, 0, 0);
  writeFreq(DEV2, 0, 0, 0, 0);
}

void loop()
{
  WiFiClient client = server.available();
  if (client)
  {
    Serial.println("Client connected");
    uint8_t buf[12];
    while (client.connected()) {
      if (client.available() >= 12) {
        client.read(buf, 12);
        for (int i = 0; i < 12; i++) {
          Serial.print(buf[i]);
          Serial.print(" ");
        }
        Serial.println();
        writeBuf(DEV1, buf, 6);
        writeBuf(DEV2, buf+6, 6);
      }
    }
    Serial.println("Client disconnected");
  }

  Serial.println("Playing idle sequence");

  chord(660, 784, 1047, 255);
  delay(100);
  off();
  delay(100);
  chord(660, 784, 1047, 255);
  delay(700);
  off();
  delay(5000);

  /*
  Wire.requestFrom(DEV, 2, false);
  delay(1);
  while(Wire.available()) {
    char c = Wire.read();
    Serial.print(c);
  }
  Serial.println("");
  delay(500);
  */

  
}

