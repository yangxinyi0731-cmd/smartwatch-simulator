// M5StickS3 六轴数据流：以目标 50 Hz 通过 USB 串口输出 CSV 行
// 输出格式： t_ms,ax,ay,az,gx,gy,gz   （加速度单位 g，角速度单位 deg/s，以实测确认为准）
#include <M5Unified.h>

static uint32_t next_sample_us = 0;
static uint32_t sample_count = 0;
static uint32_t last_display_ms = 0;

void setup() {
  M5.begin();
  M5.Display.setTextFont(&fonts::FreeMonoBold9pt7b);
  M5.Display.printf("IMU stream\n50 Hz\nwaiting: PC\n");
  Serial.begin(115200);
  next_sample_us = micros();
}

void loop() {
  M5.update();

  uint32_t now_us = micros();
  if ((int32_t)(now_us - next_sample_us) >= 0) {
    next_sample_us += 20000;
    if ((int32_t)(now_us - next_sample_us) > 0) {
      next_sample_us = now_us + 20000;
    }
    M5.Imu.update();
    auto d = M5.Imu.getImuData();
    Serial.printf("%lu,%.4f,%.4f,%.4f,%.4f,%.4f,%.4f\n",
                  (unsigned long)(now_us / 1000UL),
                  d.accel.x, d.accel.y, d.accel.z,
                  d.gyro.x, d.gyro.y, d.gyro.z);
    sample_count++;
  }

  uint32_t now_ms = millis();
  if (now_ms - last_display_ms >= 500) {
    last_display_ms = now_ms;
    M5.Display.setCursor(0, 40);
    M5.Display.printf("samples:\n%lu    ", (unsigned long)sample_count);
  }
}
