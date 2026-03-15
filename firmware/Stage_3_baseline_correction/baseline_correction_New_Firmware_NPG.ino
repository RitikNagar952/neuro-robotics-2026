#include <Arduino.h>

// ----------------- USER CONFIGURATION -----------------
#define SAMPLE_RATE       512          
#define BAUD_RATE         115200
#define INPUT_PIN_H       A0    // Horizontal (Left/Right)
#define INPUT_PIN_V       A1    // Vertical (Up/Down)

// --- Filter Functions ---
float highpass_H(float input) {
  static float z1, z2;
  float x = input - -1.91327599*z1 - 0.91688335*z2;
  float out = 0.95753983*x + -1.91507967*z1 + 0.95753983*z2;
  z2 = z1; z1 = x;
  return out;
}

float highpass_V(float input) {
  static float z1, z2;
  float x = input - -1.91327599*z1 - 0.91688335*z2;
  float out = 0.95753983*x + -1.91507967*z1 + 0.95753983*z2;
  z2 = z1; z1 = x;
  return out;
}

float Notch_H(float input) {
  static float z1_1, z1_2, z2_1, z2_2;
  float x1 = input - -1.58696045*z1_1 - 0.96505858*z1_2;
  float out1 = 0.96588529*x1 + -1.57986211*z1_1 + 0.96588529*z1_2;
  z1_2 = z1_1; z1_1 = x1;
  float x2 = out1 - -1.62761184*z2_1 - 0.96671306*z2_2;
  float out2 = 1.00000000*x2 + -1.63566226*z2_1 + 1.00000000*z2_2;
  z2_2 = z2_1; z2_1 = x2;
  return out2;
}

float Notch_V(float input) {
  static float z1_1, z1_2, z2_1, z2_2;
  float x1 = input - -1.58696045*z1_1 - 0.96505858*z1_2;
  float out1 = 0.96588529*x1 + -1.57986211*z1_1 + 0.96588529*z1_2;
  z1_2 = z1_1; z1_1 = x1;
  float x2 = out1 - -1.62761184*z2_1 - 0.96671306*z2_2;
  float out2 = 1.00000000*x2 + -1.63566226*z2_1 + 1.00000000*z2_2;
  z2_2 = z2_1; z2_1 = x2;
  return out2;
}

void setup() {
  Serial.begin(BAUD_RATE);
  pinMode(INPUT_PIN_H, INPUT);
  pinMode(INPUT_PIN_V, INPUT);
}

void loop() {
  static unsigned long lastMicros = micros();
  unsigned long now = micros();
  unsigned long dt = now - lastMicros;
  lastMicros = now;

  static long timer = 0;
  timer -= dt;

  // --- Baseline Correction Variables ---
  // These track the "average" DC offset of your body/hardware
  static float dcH = 2048.0; 
  static float dcV = 2048.0;
  const float alpha = 0.01; // Learning rate for the baseline (0.01 is stable)

  if(timer <= 0) {
    timer += 1000000L / SAMPLE_RATE;

    int rawH = analogRead(INPUT_PIN_H);
    int rawV = analogRead(INPUT_PIN_V);

    // 1. Update the DC baseline (Moving Average)
    dcH = (dcH * (1.0 - alpha)) + (float(rawH) * alpha);
    dcV = (dcV * (1.0 - alpha)) + (float(rawV) * alpha);

    // 2. Subtract the baseline to center the signal around 0.0
    float centeredH = (float)rawH - dcH;
    float centeredV = (float)rawV - dcV;

    // 3. Apply filters to the centered data
    float filtH = highpass_H(Notch_H(centeredH));
    float filtV = highpass_V(Notch_V(centeredV));

    // Format: "HorizontalValue,VerticalValue"
    Serial.print(filtH);
    Serial.print(",");
    Serial.println(filtV);
  }
}