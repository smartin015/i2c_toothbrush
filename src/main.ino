// Wire Master Writer
// by Nicholas Zambetti <http://www.zambetti.com>

// Demonstrates use of the Wire library
// Writes data to an I2C/TWI slave device
// Refer to the "Wire Slave Receiver" example for use with this

// Created 29 March 2006

// This example code is in the public domain.


#include <Wire.h>

void setup()
{
  Serial.begin(115200);
  Wire.begin(); // join i2c bus (address optional for master)
}


#define DEV1 64
#define DEV2 65
// 64

void writeFreq(uint8_t device, uint16_t fA, uint16_t fB, uint8_t vA, uint8_t vB) {
  Wire.beginTransmission(device);
  uint8_t buf[6];
  buf[0] = fA & 0xff;
  buf[1] = (fA >> 8) & 0xff;
  buf[2] = fB & 0xff;
  buf[3] = (fB >> 8) & 0xff;
  buf[4] = vA;
  buf[5] = vB;
  Wire.write(buf, sizeof(buf));
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
  Serial.println("Loop start");

  chord(660, 784, 1047, 255);
  delay(100);
  off();
  delay(100);
  chord(660, 784, 1047, 255);
  delay(700);
  off();
  delay(1500);

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

