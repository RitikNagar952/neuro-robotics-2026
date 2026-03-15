#include <Arduino.h>

#define SAMPLE_RATE       512
#define BAUD_RATE         115200

#define INPUT_PIN_H       A0
#define INPUT_PIN_V       A1
#define INPUT_PIN_ARM_R   A2
#define INPUT_PIN_ARM_L   A3

// ---- EOG smoothing ----
const int WINDOW_SIZE = 12;
float bufferH[WINDOW_SIZE], bufferV[WINDOW_SIZE];
int bufIdx = 0;

// ---- EMG smoothing ----
const int EMG_WINDOW = 8;
float emgBufR[EMG_WINDOW], emgBufL[EMG_WINDOW];
int emgIdx = 0;

// ---------------- NOTCH FILTER ----------------
float Notch_Filter(float input, float &z1_1, float &z1_2, float &z2_1, float &z2_2) {

float x1 = input - -1.58696045*z1_1 - 0.96505858*z1_2;
float out1 = 0.96588529*x1 + -1.57986211*z1_1 + 0.96588529*z1_2;

z1_2 = z1_1;
z1_1 = x1;

float x2 = out1 - -1.62761184*z2_1 - 0.96671306*z2_2;
float out2 = 1.00000000*x2 + -1.63566226*z2_1 + 1.00000000*z2_2;

z2_2 = z2_1;
z2_1 = x2;

return out2;
}

// filter states
static float zh1_1, zh1_2, zh2_1, zh2_2;
static float zv1_1, zv1_2, zv2_1, zv2_2;

// calibration offsets
float offsetH = 512.0;
float offsetV = 512.0;

void setup() {
Serial.begin(BAUD_RATE);
}

void loop() {

// ----- calibration command -----
if (Serial.available()) {
char cmd = Serial.read();

if (cmd == 'c') {  
  offsetH = Notch_Filter(analogRead(INPUT_PIN_H), zh1_1, zh1_2, zh2_1, zh2_2);  
  offsetV = Notch_Filter(analogRead(INPUT_PIN_V), zv1_1, zv1_2, zv2_1, zv2_2);  
}

}

static unsigned long lastMicros = micros();

if (micros() - lastMicros >= (1000000L / SAMPLE_RATE)) {

lastMicros = micros();  

// ---------- EOG ----------  
float cleanH = Notch_Filter(analogRead(INPUT_PIN_H), zh1_1, zh1_2, zh2_1, zh2_2);  
float cleanV = Notch_Filter(analogRead(INPUT_PIN_V), zv1_1, zv1_2, zv2_1, zv2_2);  

bufferH[bufIdx] = cleanH - offsetH;  
bufferV[bufIdx] = cleanV - offsetV;  

// ---------- EMG ----------  
float emgR = analogRead(INPUT_PIN_ARM_R);  
float emgL = analogRead(INPUT_PIN_ARM_L);  

// rectify EMG  
emgR = abs(emgR - 512);  
emgL = abs(emgL - 512);  

emgBufR[emgIdx] = emgR;  
emgBufL[emgIdx] = emgL;  

bufIdx = (bufIdx + 1) % WINDOW_SIZE;  
emgIdx = (emgIdx + 1) % EMG_WINDOW;  

// ----- averages -----  
float avgH = 0, avgV = 0;  
float avgEmgR = 0, avgEmgL = 0;  

for(int i=0;i<WINDOW_SIZE;i++){  
  avgH += bufferH[i];  
  avgV += bufferV[i];  
}  

for(int i=0;i<EMG_WINDOW;i++){  
  avgEmgR += emgBufR[i];  
  avgEmgL += emgBufL[i];  
}  

avgH /= WINDOW_SIZE;  
avgV /= WINDOW_SIZE;  
avgEmgR /= EMG_WINDOW;  
avgEmgL /= EMG_WINDOW;  

// ---------- SERIAL OUTPUT ----------  
Serial.print(avgH);  
Serial.print(",");  

Serial.print(avgV);  
Serial.print(",");  

Serial.print(avgEmgR);  
Serial.print(",");
Serial.println(avgEmgL);

}
}
