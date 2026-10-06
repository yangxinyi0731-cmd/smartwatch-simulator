// M5StickS3 六轴数据流 v2：50 Hz 串口输出 + 屏幕显示判断 + 振动提示 + Wi-Fi 免插线
// 输出格式： t_ms,ax,ay,az,gx,gy,gz   （加速度单位 g，角速度单位 deg/s，以实测确认为准）
// 电脑指令（USB 串口或 Wi-Fi TCP 均可）：#TEXT:<警告文字> / #TEXT: / #STATUS:<状态文字> / #VIB:0|1 / #CLEAR
#include <M5Unified.h>
#include <WiFi.h>

static const char *WIFI_AP_SSID = "HealthWatch";
static const char *WIFI_AP_PASSWORD = "healthwatch";
static const uint16_t WIFI_TCP_PORT = 5005;
static const int VIBRATION_PIN = 9;
static const uint32_t VIBRATION_MAX_MS = 2000;
static const uint32_t ALERT_STALE_MS = 8000;

static uint32_t next_sample_us = 0;
static uint32_t sample_count = 0;
static uint32_t last_display_ms = 0;
static uint32_t vibration_until_ms = 0;
static uint32_t last_alert_ms = 0;

static bool wifi_enabled = false;
static bool alert_active = false;
static bool display_dirty = true;
static bool station_pending = false;
static bool station_connected = false;
static bool station_enabled = false;
static uint32_t station_started_ms = 0;
static String status_text = "等待电脑";
static String alert_text = "";
static String usb_buffer;
static String tcp_buffer;
static String tcp_batch;
static uint32_t tcp_flush_ms = 0;
static WiFiServer tcp_server(WIFI_TCP_PORT);
static WiFiClient tcp_client;

static void setWifi(bool enabled);

static void sendLine(const String &line) {
  Serial.println(line);
  if (tcp_client && tcp_client.connected()) {
    tcp_client.println(line);
  }
}

static void handleCommand(String command) {
  command.trim();
  if (command.length() == 0) {
    return;
  }
  if (command.startsWith("#TEXT:")) {
    String text = command.substring(6);
    text.trim();
    if (text.length() == 0) {
      alert_active = false;
      alert_text = "";
    } else {
      alert_active = true;
      alert_text = text;
      last_alert_ms = millis();
    }
    display_dirty = true;
  } else if (command == "#CLEAR") {
    alert_active = false;
    alert_text = "";
    status_text = "等待电脑";
    display_dirty = true;
  } else if (command.startsWith("#STATUS:")) {
    String text = command.substring(8);
    text.trim();
    status_text = text.length() ? text : "等待电脑";
    display_dirty = true;
  } else if (command.startsWith("#WIFI:")) {
    String value = command.substring(6);
    value.trim();
    setWifi(value == "1");
  } else if (command == "#NET") {
    sendLine("#NET:mode=" + String((int)WiFi.getMode()) +
             " status=" + String((int)WiFi.status()) +
             " station=" + String(station_enabled ? 1 : 0) +
             " connected=" + String(station_connected ? 1 : 0) +
             " ap=" + String(wifi_enabled ? 1 : 0) +
             " ip=" + WiFi.localIP().toString());
  } else if (command == "#SCAN") {
    WiFi.mode(wifi_enabled ? WIFI_AP_STA : WIFI_STA);
    int found = WiFi.scanNetworks(false, false);
    sendLine("#SCAN:count=" + String(found));
    for (int index = 0; index < found && index < 12; index++) {
      sendLine("#SCAN:" + String(index + 1) + " " + WiFi.SSID(index) +
               " ch" + String(WiFi.channel(index)) + " " +
               String(WiFi.RSSI(index)) + "dBm");
    }
    WiFi.scanDelete();
    if (wifi_enabled) {
      WiFi.mode(WIFI_AP);
    } else if (!station_connected) {
      WiFi.mode(WIFI_OFF);
    }
  } else if (command.startsWith("#STA:")) {
    String payload = command.substring(5);
    int separator = payload.indexOf('|');
    if (separator <= 0) {
      sendLine("#STA:FAIL format");
    } else {
      String ssid = payload.substring(0, separator);
      String password = payload.substring(separator + 1);
      WiFi.mode(wifi_enabled ? WIFI_AP_STA : WIFI_STA);
      WiFi.begin(ssid.c_str(), password.c_str());
      WiFi.setSleep(false);
      tcp_server.begin();
      station_pending = true;
      station_connected = false;
      station_enabled = true;
      station_started_ms = millis();
      sendLine("#STA:connecting ssid=" + ssid);
      display_dirty = true;
    }
  } else if (command.startsWith("#VIB:")) {
    String value = command.substring(5);
    value.trim();
    if (value == "1") {
      digitalWrite(VIBRATION_PIN, HIGH);
      vibration_until_ms = millis() + VIBRATION_MAX_MS;
    } else {
      digitalWrite(VIBRATION_PIN, LOW);
      vibration_until_ms = 0;
    }
  }
  sendLine("#ACK:" + command);
}

static void readCommands(Stream &stream, String &buffer) {
  while (stream.available()) {
    char value = (char)stream.read();
    if (value == '\n' || value == '\r') {
      if (buffer.length()) {
        handleCommand(buffer);
        buffer = "";
      }
    } else if (buffer.length() < 160) {
      buffer += value;
    } else {
      buffer = "";
    }
  }
}

static void setWifi(bool enabled) {
  if (enabled == wifi_enabled) {
    return;
  }
  wifi_enabled = enabled;
  if (enabled) {
    WiFi.mode(WIFI_AP);
    bool started = WiFi.softAP(WIFI_AP_SSID, WIFI_AP_PASSWORD, 6);
    tcp_server.begin();
    tcp_client = WiFiClient();
    if (started) {
      sendLine("#WIFI:AP ssid=" + String(WIFI_AP_SSID) +
               " ip=" + WiFi.softAPIP().toString());
    } else {
      sendLine("#WIFI:FAIL");
    }
  } else {
    tcp_client.stop();
    tcp_server.stop();
    WiFi.mode(WIFI_OFF);
    sendLine("#WIFI:OFF");
  }
  display_dirty = true;
}

static void refreshDisplay() {
  M5.Display.fillScreen(TFT_BLACK);
  M5.Display.setTextColor(TFT_WHITE, TFT_BLACK);
  M5.Display.setTextDatum(top_left);
  M5.Display.setFont(&fonts::efontCN_16);
  M5.Display.setCursor(6, 6);
  M5.Display.printf("IMU 50Hz\n样本 %lu\n", (unsigned long)sample_count);
  if (wifi_enabled) {
    M5.Display.printf("WiFi: HealthWatch\n%s\n", WiFi.softAPIP().toString().c_str());
  } else if (station_connected) {
    M5.Display.printf("WiFi: %s\n%s\n", WiFi.SSID().c_str(),
                      WiFi.localIP().toString().c_str());
  } else if (station_pending) {
    M5.Display.printf("WiFi: 连接中…\n\n");
  } else {
    M5.Display.printf("WiFi: off\n\n");
  }
  M5.Display.drawFastHLine(0, 118, 135, TFT_DARKGREY);
  if (alert_active) {
    M5.Display.fillRect(0, 126, 135, 44, TFT_RED);
    M5.Display.setTextColor(TFT_WHITE, TFT_RED);
    M5.Display.setFont(&fonts::efontCN_24);
    M5.Display.setCursor(6, 136);
    M5.Display.printf("%s", alert_text.c_str());
  } else {
    M5.Display.setTextColor(TFT_GREEN, TFT_BLACK);
    M5.Display.setFont(&fonts::efontCN_16);
    M5.Display.setCursor(6, 140);
    M5.Display.printf("%s", status_text.c_str());
  }
  display_dirty = false;
}

void setup() {
  M5.begin();
  M5.Display.setRotation(0);
  M5.Display.setTextFont(&fonts::efontCN_16);
  Serial.begin(115200);
  Serial.setTxTimeoutMs(5);
  pinMode(VIBRATION_PIN, OUTPUT);
  digitalWrite(VIBRATION_PIN, LOW);
  WiFi.mode(WIFI_STA);
  WiFi.setSleep(false);
  if (WiFi.begin() == WL_NO_SSID_AVAIL) {
    WiFi.mode(WIFI_OFF);
  } else {
    station_pending = true;
    station_enabled = true;
    station_started_ms = millis();
    tcp_server.begin();
  }
  next_sample_us = micros();
  display_dirty = true;
}

void loop() {
  M5.update();

  if (M5.BtnA.wasPressed()) {
    setWifi(!wifi_enabled);
  }

  uint32_t now_us = micros();
  if ((int32_t)(now_us - next_sample_us) >= 0) {
    next_sample_us += 20000;
    if ((int32_t)(now_us - next_sample_us) > 0) {
      next_sample_us = now_us + 20000;
    }
    M5.Imu.update();
    auto d = M5.Imu.getImuData();
    char line[96];
    snprintf(line, sizeof(line), "%lu,%.4f,%.4f,%.4f,%.4f,%.4f,%.4f",
             (unsigned long)(now_us / 1000UL),
             d.accel.x, d.accel.y, d.accel.z,
             d.gyro.x, d.gyro.y, d.gyro.z);
    Serial.println(line);
    if (tcp_client && tcp_client.connected()) {
      tcp_batch += line;
      tcp_batch += '\n';
      if (tcp_batch.length() >= 512) {
        tcp_client.print(tcp_batch);
        tcp_batch = "";
        tcp_flush_ms = millis();
      }
    }
    sample_count++;
  }

  if (station_enabled) {
    wl_status_t station_status = WiFi.status();
    if (station_status == WL_CONNECTED) {
      if (!station_connected) {
        station_connected = true;
        station_pending = false;
        sendLine("#STA:OK ip=" + WiFi.localIP().toString());
        display_dirty = true;
      }
    } else {
      if (station_connected) {
        station_connected = false;
        display_dirty = true;
      }
      if (station_pending && millis() - station_started_ms > 20000) {
        station_pending = false;
        sendLine("#STA:FAIL timeout");
        display_dirty = true;
      }
    }
  }

  readCommands(Serial, usb_buffer);
  if (wifi_enabled || station_enabled) {
    if (!tcp_client || !tcp_client.connected()) {
      WiFiClient candidate = tcp_server.available();
      if (candidate) {
        tcp_client = candidate;
        tcp_client.setNoDelay(true);
        tcp_client.println("#READY:M5StickS3");
        sendLine("#TCP:client-connected");
      }
    }
    if (tcp_client && tcp_client.connected()) {
      readCommands(tcp_client, tcp_buffer);
      if (tcp_batch.length() && millis() - tcp_flush_ms >= 120) {
        tcp_client.print(tcp_batch);
        tcp_batch = "";
        tcp_flush_ms = millis();
      }
    }
  }

  uint32_t now_ms = millis();
  if (vibration_until_ms && now_ms > vibration_until_ms) {
    digitalWrite(VIBRATION_PIN, LOW);
    vibration_until_ms = 0;
  }
  if (alert_active && now_ms - last_alert_ms > ALERT_STALE_MS) {
    alert_active = false;
    alert_text = "";
    display_dirty = true;
  }
  if (display_dirty || now_ms - last_display_ms >= 1000) {
    last_display_ms = now_ms;
    refreshDisplay();
  }
}
