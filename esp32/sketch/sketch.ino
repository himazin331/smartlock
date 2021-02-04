#include <WiFi.h> // WiFi関連のヘッダーファイル
#include <WiFiUdp.h>  // UDP関連のヘッダーファイル
#include <Wire.h> // I2C関連のヘッダーファイル
#include <string.h>
#include "esp_camera.h" // カメラ関連のヘッダーファイル

#include "select_pins.h" // センサーやカメラなどのピン情報

// アクセスポイントモード
// #define SOFTAP_MODE
#if defined(SOFTAP_MODE)
#endif

// 自動スリープ時使用 (今回は不要)
#define uS_TO_S_FACTOR 1000000 // μS -> S変換
#define TIME_TO_SLEEP  5 // 自動スリープになる時間(秒)

// 無線LAN情報
#define WIFI_SSID   "*************"
#define WIFI_PASSWD "*************"
String macAddress = ""; // MACアドレス
String ipAddress = "";  // IPアドレス

// Raspberry Pi情報
static WiFiUDP udp;
static const char *raspip = "192.168.1.8";
static const int raspport = 6100;

char udp_data[128]; // UDP受信データ

extern void startCameraServer();

// ボタン アクティブ
#include <OneButton.h>
OneButton button(BUTTON_1, true);

// ディスプレイ アクティブ
#include "SSD1306.h"
#include "OLEDDisplayUi.h"
#define SSD1306_ADDRESS 0x3c
SSD1306 oled(SSD1306_ADDRESS, I2C_SDA, I2C_SCL, (OLEDDISPLAY_GEOMETRY)SSD130_MODLE_TYPE);
OLEDDisplayUi ui(&oled);

bool deviceProbe(uint8_t addr)
{
  Wire.beginTransmission(addr);
  return Wire.endTransmission() == 0;
}

// ディスプレイ セットアップ
bool setupDisplay()
{
  // セットアップ失敗 -> 中断
  if (!deviceProbe(SSD1306_ADDRESS))return false;
  
  oled.init();
  oled.setTextAlignment(TEXT_ALIGN_CENTER); // 中央揃え
  oled.setFont(ArialMT_Plain_16);           // フォント

  // 起動画面 表示
  oled.drawString(oled.getWidth() / 2, oled.getHeight() / 2 - 16, "SmartLock");
  oled.drawString(oled.getWidth() / 2, oled.getHeight() / 2, "System");
  oled.display();

  return true;
}

// ディスプレイ出力
void smartlock()
{
  // PIR反応 -> 認証開始
  while (digitalRead(AS312_PIN))
  {
    // ボタン反応 有効
    button.tick();

    // PIR反応フラグをRaspに送信
    udp.beginPacket(raspip, raspport);
    udp.write('1');
    udp.endPacket();
    delay(500);
    
    oled.clear();

    oled.setTextAlignment(TEXT_ALIGN_CENTER); // 中央揃え
    oled.setFont(ArialMT_Plain_16); // フォント

    Serial.println("Authentication...");
    oled.drawString(oled.getWidth() / 2, oled.getHeight() / 2 - 16, "Authentication");
    oled.display();
  }

  oled.clear(); // 画面初期化

  oled.setTextAlignment(TEXT_ALIGN_CENTER); // 中央揃え
  oled.setFont(ArialMT_Plain_16); // フォント

  oled.drawString(oled.getWidth() / 2, oled.getHeight() / 2 - 16, "SmartLock");
  oled.drawString(oled.getWidth() / 2, oled.getHeight() / 2, "System");
  oled.display();
}

// 外部電源供給 セットアップ
bool setupPower()
{
  #define IP5306_ADDR 0X75
  #define IP5306_REG_SYS_CTL0 0x00
  
  // セットアップ失敗 -> 中断
  if (!deviceProbe(IP5306_ADDR))return false;
  
  // セットアップ
  bool en = true;
  Wire.beginTransmission(IP5306_ADDR);
  Wire.write(IP5306_REG_SYS_CTL0);
  if (en)
    Wire.write(0x37);
  else
    Wire.write(0x35);
  return Wire.endTransmission() == 0;

  return true;
}

// 人感センサー セットアップ
bool setupSensor()
{
  pinMode(AS312_PIN, INPUT);
  return true;
}

// カメラ セットアップ
bool setupCamera()
{
  camera_config_t config;

  #if defined(Y2_GPIO_NUM)
    config.ledc_channel = LEDC_CHANNEL_0;
    config.ledc_timer = LEDC_TIMER_0;
    config.pin_d0 = Y2_GPIO_NUM;
    config.pin_d1 = Y3_GPIO_NUM;
    config.pin_d2 = Y4_GPIO_NUM;
    config.pin_d3 = Y5_GPIO_NUM;
    config.pin_d4 = Y6_GPIO_NUM;
    config.pin_d5 = Y7_GPIO_NUM;
    config.pin_d6 = Y8_GPIO_NUM;
    config.pin_d7 = Y9_GPIO_NUM;
    config.pin_xclk = XCLK_GPIO_NUM;
    config.pin_pclk = PCLK_GPIO_NUM;
    config.pin_vsync = VSYNC_GPIO_NUM;
    config.pin_href = HREF_GPIO_NUM;
    config.pin_sscb_sda = SIOD_GPIO_NUM;
    config.pin_sscb_scl = SIOC_GPIO_NUM;
    config.pin_pwdn = PWDN_GPIO_NUM;
    config.pin_reset = RESET_GPIO_NUM;
    config.xclk_freq_hz = 20000000;
    config.pixel_format = PIXFORMAT_JPEG;
    //init with high specs to pre-allocate larger buffers
    if (psramFound()) {
      config.frame_size = FRAMESIZE_UXGA;
      config.jpeg_quality = 10;
      config.fb_count = 2;
    } else {
      config.frame_size = FRAMESIZE_SVGA;
      config.jpeg_quality = 12;
      config.fb_count = 1;
    }
  #endif

  // セットアップ失敗 -> 中断
  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Camera init failed with error 0x%x\n", err);
    return false;
  }

  sensor_t *s = esp_camera_sensor_get();
  // 反転
  s->set_hmirror(s, 1);
  s->set_vflip(s, 1);

  return true;
}

// ボタン セットアップ
void setupButton()
{
  // 2回プッシュ -> スリープモード
  button.attachDoubleClick([]() {    
    ui.disableAutoTransition(); // スライドアニメーション無効

    oled.setTextAlignment(TEXT_ALIGN_CENTER); // 中央揃え
    oled.setFont(ArialMT_Plain_10); // フォント
    oled.clear(); // 画面初期化

    // スリープモード移行表示
    Serial.println("Sleep mode");
    oled.drawString(oled.getWidth() / 2 - 5, oled.getHeight() / 2 - 20, "Transition to sleep mode...");
    oled.drawString(oled.getWidth() / 2, oled.getHeight() / 2, "Press the button");
    oled.drawString(oled.getWidth() / 2, oled.getHeight() / 2 + 10, "to wake up.");
    oled.display();
    delay(3000);

    // ディスプレイ出力OFF
    oled.clear();
    oled.displayOff();

    // スリープモード移行
    esp_sleep_enable_ext1_wakeup(((uint64_t)(((uint64_t)1) << BUTTON_1)), ESP_EXT1_WAKEUP_ALL_LOW); // 復帰条件
    esp_deep_sleep_start();
  });
}

// ネットワーク セットアップ
void setupNetwork()
{
  macAddress = "LilyGo-CAM-";

  // アクセスポイントモード
  #ifdef SOFTAP_MODE
    WiFi.mode(WIFI_AP);
    macAddress += WiFi.softAPmacAddress().substring(0, 5);
    WiFi.softAP(macAddress.c_str());
    ipAddress = WiFi.softAPIP().toString();
  #else // ステーションモード
    WiFi.begin(WIFI_SSID, WIFI_PASSWD);
    while (WiFi.status() != WL_CONNECTED) {
      delay(500);
      Serial.print(".");
    }
    Serial.println("");
    Serial.println("WiFi connected");
    ipAddress = WiFi.localIP().toString();
    macAddress += WiFi.macAddress().substring(0, 5);
  #endif
}

// UDP セットアップ
void setupUDP()
{
  udp.begin(6000);
}

// セットアップ
void setup()
{
  // シリアル通信開始 (115200bps)
  Serial.begin(115200);
  Wire.begin(I2C_SDA, I2C_SCL);

  bool status;
  // ディスプレイ セットアップ
  status = setupDisplay();
  Serial.print("setupDisplay status: "); Serial.println(status);

  // 外部電源供給 セットアップ
  status = setupPower();
  Serial.print("setupPower status: "); Serial.println(status);

  // 人感センサー セットアップ
  status = setupSensor();
  Serial.print("setupSensor status: "); Serial.println(status);

  // カメラ セットアップ
  status = setupCamera();
  Serial.print("setupCamera status: "); Serial.println(status);

  // セットアップ失敗 -> 再試行
  if (!status) {
    delay(10000);
    esp_restart();
  }

  // ボタン セットアップ
  setupButton();
  // ネットワーク セットアップ
  setupNetwork();
  // UDP セットアップ
  setupUDP();
  // Start
  startCameraServer();

  // IPアドレス情報 シリアルモニター出力
  Serial.print("IP Address: "); Serial.println(ipAddress);
}

// ディスプレイ出力
void loop()
{
  // 施錠フラグ Trueならば
  if (udp.parsePacket()) {
    udp.read(udp_data, 128);
    if (strcmp(udp_data, "lock") == 0)
    {
      smartlock();
    }
  }
}