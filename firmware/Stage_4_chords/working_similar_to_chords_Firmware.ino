#include <Arduino.h>

#define SAMPLE_RATE       512          
#define BAUD_RATE         115200
#define INPUT_PIN_H       A0    
#define INPUT_PIN_V       A1    

const int WINDOW_SIZE = 12; 
float bufferH[WINDOW_SIZE], bufferV[WINDOW_SIZE];
int bufIdx = 0;

// Filters
float Notch_Filter(float input, float &z1_1, float &z1_2, float &z2_1, float &z2_2) {
  float x1 = input - -1.58696045*z1_1 - 0.96505858*z1_2;
  float out1 = 0.96588529*x1 + -1.57986211*z1_1 + 0.96588529*z1_2;
  z1_2 = z1_1; z1_1 = x1;
  float x2 = out1 - -1.62761184*z2_1 - 0.96671306*z2_2;
  float out2 = 1.00000000*x2 + -1.63566226*z2_1 + 1.00000000*z2_2;
  z2_2 = z2_1; z2_1 = x2;
  return out2;
}

static float zh1_1, zh1_2, zh2_1, zh2_2;
static float zv1_1, zv1_2, zv2_1, zv2_2;

// STAGE 3: Use fixed offsets instead of moving ones
float offsetH = 512.0, offsetV = 512.0;

void setup() {
  Serial.begin(BAUD_RATE);
}

void loop() {
  // Listen for calibration command
  if (Serial.available() > 0) {
    char cmd = Serial.read();
    if (cmd == 'c') {
      // Set current raw values as the new center (Zero)
      offsetH = Notch_Filter(analogRead(INPUT_PIN_H), zh1_1, zh1_2, zh2_1, zh2_2);
      offsetV = Notch_Filter(analogRead(INPUT_PIN_V), zv1_1, zv1_2, zv2_1, zv2_2);
    }
  }

  static unsigned long lastMicros = micros();
  if (micros() - lastMicros >= (1000000L / SAMPLE_RATE)) {
    lastMicros = micros();

    float cleanH = Notch_Filter(analogRead(INPUT_PIN_H), zh1_1, zh1_2, zh2_1, zh2_2);
    float cleanV = Notch_Filter(analogRead(INPUT_PIN_V), zv1_1, zv1_2, zv2_1, zv2_2);

    // Smoothing
    bufferH[bufIdx] = cleanH - offsetH;
    bufferV[bufIdx] = cleanV - offsetV;
    bufIdx = (bufIdx + 1) % WINDOW_SIZE;

    float avgH = 0, avgV = 0;
    for(int i=0; i<WINDOW_SIZE; i++) { avgH += bufferH[i]; avgV += bufferV[i]; }
    
    Serial.print(avgH / (float)WINDOW_SIZE);
    Serial.print(",");
    Serial.println(avgV / (float)WINDOW_SIZE);
  }
}