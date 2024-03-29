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
#define SERIAL_RX_BUFFER_SIZE 256
#define IDLE_SEQ_DELAY 10000

WiFiServer server(PORT);

#define DEV1 63
#define DEV2 64

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
#define FRAME_SAMPLES 64*2
uint8_t wav_buffer[FRAME_SAMPLES];
// TODO 2 channel buffer
void writeFrame(uint8_t device, uint8_t* frameptr) {
  Wire.beginTransmission(device);
  Wire.write(frameptr, FRAME_SAMPLES);
  Wire.endTransmission();
}

void demoWav() {
  Serial.println("Starting wav mode");
  writeFreq(DEV1, 0, 0, 255, 255); // Start wav mode
  writeFreq(DEV2, 0, 0, 255, 255); // Start wav mode
  // Keep the buffer filled
  for (uint16_t i = 0; i < FRAME_SAMPLES; i+= 2) { // Skip every other byte; only fill channel 1
      wav_buffer[i] = i & 0xff; // Simple sawtooth, 8 bits @ 44.1kHz ~= 172 Hz tone
  }
  while (1) {
    writeFrame(DEV1, wav_buffer);
    writeFrame(DEV2, wav_buffer);
    delay(10);
  }
}


void chord(uint16_t fA, uint16_t fB, uint16_t fC, uint16_t fD) {
  uint8_t vA = (fA == 0) ? 0 : 255;
  uint8_t vB = (fB == 0) ? 0 : 255;
  uint8_t vC = (fC == 0) ? 0 : 255;
  uint8_t vD = (fD == 0) ? 0 : 255;
  writeFreq(DEV1, fA, fB, vA, vB);
  writeFreq(DEV2, fC, fD, vC, vD);
}

void off() {
  writeFreq(DEV1, 0, 0, 0, 0);
  writeFreq(DEV2, 0, 0, 0, 0);
}

void startupSeq() {

  chord(330, 0, 0, 0);
  delay(100);
  chord(0, 392, 0, 0);
  delay(100);
  chord(0, 0, 524, 0);
  delay(100);
  chord(0, 0, 0, 660);
  delay(100);
  off();
}

void idleSeq() {
  chord(330, 392, 524, 660);
  delay(50);
  off();
  delay(50);
  chord(330, 392, 524, 660);
  delay(700);
  off();
}

void setup()
{
  Serial.begin(1000000);

  Wire.setClock(400000); // FAST I2C Mode
  Wire.begin(); // join i2c bus (address optional for master)
  startupSeq();
  delay(50);
  idleSeq();
  // demoWav();


  Serial.print("Beginning async WIFI connection");
  WiFi.hostname("tooth1");
  WiFi.begin("robotoverlords", "TODO");

  Serial.print("Listening on port ");
  Serial.println(PORT);
  server.begin();

  Serial.println("Setup complete");
}


uint8_t ser_i = 0;
uint8_t serbuf[12];
uint64_t nextIdleSeq = 0;
bool wifi_connected = false;
void loop()
{

  if (!wifi_connected) {
    if (WiFi.status() == WL_CONNECTED) {
      Serial.print("Connected, IP address: ");
      Serial.println(WiFi.localIP());
      wifi_connected = true;
    }
  } else {
    WiFiClient client = server.available();
    if (client) {
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
  }

  uint64_t now = millis();
  while (Serial.available()) {
    nextIdleSeq = now + IDLE_SEQ_DELAY;
    serbuf[ser_i++] = Serial.read();
    if (ser_i >= 12) {
      writeBuf(DEV1, serbuf, 6);
      writeBuf(DEV2, serbuf+6, 6);
      ser_i = 0;
    }

  }

  if (now > nextIdleSeq) {
    Serial.println("Playing idle sequence");
    nextIdleSeq = now + IDLE_SEQ_DELAY;
    // idleSeq();
  }

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

