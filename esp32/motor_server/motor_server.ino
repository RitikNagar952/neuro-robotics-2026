/*
 * motor_server.ino  —  ESP32 WiFi HTTP Motor Command Server
 *
 * Neuro-Robotics Hackathon 2026 | IIT Jodhpur  🏆
 *
 * Dual-mode server:
 *   1. Browser UI  → serves a web page with keyboard + touch buttons
 *   2. Python API  → responds to GET /m1/clk, /m2/anticlk, /m5/stop etc.
 *
 * Motor Pin Mapping (L298N dual H-bridge):
 *   Motor 1 (Base rotation)  → GPIO 26, 27
 *   Motor 2 (Shoulder)       → GPIO 25, 33
 *   Motor 3 (Elbow)          → GPIO 16, 17
 *   Motor 4 (Wrist)          → GPIO 18, 19
 *   Motor 5 (Gripper)        → GPIO 22, 23
 *
 * HTTP Endpoints:
 *   GET /            → Serve web control UI
 *   GET /mX/clk      → Motor X clockwise      (X = 1..5)
 *   GET /mX/anticlk  → Motor X counter-CW
 *   GET /mX/stop     → Motor X stop
 *
 * Setup: Set WIFI_SSID and WIFI_PASSWORD below, upload, then
 *        copy the printed IP address into python/config.py → ESP32_IP
 */

#include <WiFi.h>

// ── WiFi Credentials ──────────────────────────────────
const char* ssid     = "tws";
const char* password = "11111111";

// ── Motor Pin Definitions ─────────────────────────────
const int m1_a = 26; const int m1_b = 27;   // Motor 1 — Base rotation
const int m2_a = 25; const int m2_b = 33;   // Motor 2 — Shoulder
const int m3_a = 16; const int m3_b = 17;   // Motor 3 — Elbow
const int m4_a = 18; const int m4_b = 19;   // Motor 4 — Wrist
const int m5_a = 22; const int m5_b = 23;   // Motor 5 — Gripper

WiFiServer server(80);

// ── Web UI (served at GET /) ───────────────────────────
String htmlPage = R"rawliteral(
<!DOCTYPE html>
<html>
<head>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>5-Motor Control</title>
  <style>
    body { text-align: center; font-family: Arial, sans-serif; background-color: #222; color: white; margin-top: 20px;}
    .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; max-width: 400px; margin: auto; }
    .btn { padding: 15px; font-size: 16px; border-radius: 5px; border: none; background-color: #007bff; color: white; cursor: pointer; user-select: none;}
    .btn:active { background-color: #0056b3; }
    h3 { margin-bottom: 5px; grid-column: span 2; }
  </style>
</head>
<body>
  <h2>5-Motor Command Center</h2>
  <p id="status" style="color:#0f0; font-size:14px;">🔴 Toggle Mode OFF — hold keys to run</p>
  <p>Press SPACE to toggle mode. Keys: 1-0 for motors.</p>

  <div class="grid">
    <h3>Motor 1 — Base</h3>
    <button class="btn" data-cmd="m1/clk">1 (CW)</button>
    <button class="btn" data-cmd="m1/anticlk">2 (CCW)</button>
    <h3>Motor 2 — Shoulder</h3>
    <button class="btn" data-cmd="m2/clk">3 (CW)</button>
    <button class="btn" data-cmd="m2/anticlk">4 (CCW)</button>
    <h3>Motor 3 — Elbow</h3>
    <button class="btn" data-cmd="m3/clk">5 (CW)</button>
    <button class="btn" data-cmd="m3/anticlk">6 (CCW)</button>
    <h3>Motor 4 — Wrist</h3>
    <button class="btn" data-cmd="m4/clk">7 (CW)</button>
    <button class="btn" data-cmd="m4/anticlk">8 (CCW)</button>
    <h3>Motor 5 — Gripper</h3>
    <button class="btn" data-cmd="m5/clk">9 (CW)</button>
    <button class="btn" data-cmd="m5/anticlk">0 (CCW)</button>
  </div>

  <script>
    const statusEl = document.getElementById('status');
    const stopCmd = {
      'm1/clk': 'm1/stop', 'm1/anticlk': 'm1/stop',
      'm2/clk': 'm2/stop', 'm2/anticlk': 'm2/stop',
      'm3/clk': 'm3/stop', 'm3/anticlk': 'm3/stop',
      'm4/clk': 'm4/stop', 'm4/anticlk': 'm4/stop',
      'm5/clk': 'm5/stop', 'm5/anticlk': 'm5/stop',
    };
    const keyMap = {
      '1':'m1/clk',  '2':'m1/anticlk',
      '3':'m2/clk',  '4':'m2/anticlk',
      '5':'m3/clk',  '6':'m3/anticlk',
      '7':'m4/clk',  '8':'m4/anticlk',
      '9':'m5/clk',  '0':'m5/anticlk',
    };
    let toggleMode = false;
    let activeCmd = null;
    function sendCommand(cmd) { fetch('/' + cmd).catch(()=>{}); }
    function stopAll() {
      ['m1','m2','m3','m4','m5'].forEach(m => sendCommand(m + '/stop'));
      activeCmd = null;
    }
    document.addEventListener('keydown', (e) => {
      if (e.repeat) return;
      if (e.key === ' ') {
        toggleMode = !toggleMode;
        if (!toggleMode) { stopAll(); statusEl.textContent = '🔴 Toggle Mode OFF — hold keys to run'; }
        else { statusEl.textContent = '🟢 Toggle Mode ON — press a key to start'; }
        return;
      }
      if (!keyMap[e.key]) return;
      const cmd = keyMap[e.key];
      if (toggleMode) {
        if (activeCmd === cmd) { sendCommand(stopCmd[cmd]); activeCmd = null; statusEl.textContent = '🟢 Toggle Mode ON — press a key to start'; }
        else { if (activeCmd) sendCommand(stopCmd[activeCmd]); sendCommand(cmd); activeCmd = cmd; statusEl.textContent = '🟢 Running: ' + cmd; }
      } else { sendCommand(cmd); }
    });
    document.addEventListener('keyup', (e) => {
      if (toggleMode) return;
      if (keyMap[e.key]) sendCommand(stopCmd[keyMap[e.key]]);
    });
    document.querySelectorAll('.btn').forEach(btn => {
      const cmd = btn.dataset.cmd;
      const start = (e) => { e.preventDefault(); sendCommand(cmd); };
      const stop  = (e) => { e.preventDefault(); sendCommand(stopCmd[cmd]); };
      btn.addEventListener('mousedown', start); btn.addEventListener('mouseup', stop);
      btn.addEventListener('mouseleave', stop);
      btn.addEventListener('touchstart', start, {passive:false});
      btn.addEventListener('touchend', stop, {passive:false});
      btn.addEventListener('touchcancel', stop, {passive:false});
    });
  </script>
</body>
</html>
)rawliteral";

// ── Motor Control ─────────────────────────────────────
void setMotor(int pinA, int pinB, int state) {
  if      (state ==  1) { digitalWrite(pinA, HIGH); digitalWrite(pinB, LOW);  }
  else if (state == -1) { digitalWrite(pinA, LOW);  digitalWrite(pinB, HIGH); }
  else                  { digitalWrite(pinA, LOW);  digitalWrite(pinB, LOW);  }
}

void sendOK(WiFiClient client) {
  client.println("HTTP/1.1 200 OK");
  client.println("Content-Type: text/plain");
  client.println("Connection: close");
  client.println();
  client.println("OK");
}

void setup() {
  Serial.begin(115200);

  int pins[] = {m1_a, m1_b, m2_a, m2_b, m3_a, m3_b, m4_a, m4_b, m5_a, m5_b};
  for (int i = 0; i < 10; i++) { pinMode(pins[i], OUTPUT); digitalWrite(pins[i], LOW); }

  Serial.print("Connecting to WiFi...");
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) { delay(500); Serial.print("."); }

  Serial.println("\nWiFi connected!");
  Serial.print("ESP32 IP address: ");
  Serial.println(WiFi.localIP());
  Serial.println(">>> Copy this IP into python/config.py → ESP32_IP <<<");

  server.begin();
}

void loop() {
  WiFiClient client = server.available();
  if (!client) return;

  String request = "";
  String currentLine = "";
  bool requestReceived = false;

  while (client.connected()) {
    if (client.available()) {
      char c = client.read();
      if (c == '\n') {
        if (!requestReceived && currentLine.startsWith("GET ")) {
          request = currentLine;
          requestReceived = true;
        }
        if (currentLine.length() == 0) {
          // Serve web UI
          if (request.indexOf("GET / ") >= 0 || request.indexOf("GET /index") >= 0) {
            client.println("HTTP/1.1 200 OK");
            client.println("Content-Type: text/html");
            client.println("Connection: close");
            client.println();
            client.print(htmlPage);
          } else {
            // Motor commands (from browser buttons OR Python requests)
            if (request.indexOf("/m1/clk")     >= 0) setMotor(m1_a, m1_b,  1);
            if (request.indexOf("/m1/anticlk") >= 0) setMotor(m1_a, m1_b, -1);
            if (request.indexOf("/m1/stop")    >= 0) setMotor(m1_a, m1_b,  0);
            if (request.indexOf("/m2/clk")     >= 0) setMotor(m2_a, m2_b,  1);
            if (request.indexOf("/m2/anticlk") >= 0) setMotor(m2_a, m2_b, -1);
            if (request.indexOf("/m2/stop")    >= 0) setMotor(m2_a, m2_b,  0);
            if (request.indexOf("/m3/clk")     >= 0) setMotor(m3_a, m3_b,  1);
            if (request.indexOf("/m3/anticlk") >= 0) setMotor(m3_a, m3_b, -1);
            if (request.indexOf("/m3/stop")    >= 0) setMotor(m3_a, m3_b,  0);
            if (request.indexOf("/m4/clk")     >= 0) setMotor(m4_a, m4_b,  1);
            if (request.indexOf("/m4/anticlk") >= 0) setMotor(m4_a, m4_b, -1);
            if (request.indexOf("/m4/stop")    >= 0) setMotor(m4_a, m4_b,  0);
            if (request.indexOf("/m5/clk")     >= 0) setMotor(m5_a, m5_b,  1);
            if (request.indexOf("/m5/anticlk") >= 0) setMotor(m5_a, m5_b, -1);
            if (request.indexOf("/m5/stop")    >= 0) setMotor(m5_a, m5_b,  0);
            sendOK(client);
          }
          break;
        }
        currentLine = "";
      } else if (c != '\r') {
        currentLine += c;
      }
    }
  }
  client.stop();
}
