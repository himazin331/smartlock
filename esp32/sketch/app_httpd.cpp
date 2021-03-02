// Copyright 2015-2016 Espressif Systems (Shanghai) PTE LTD
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

#include "esp_http_server.h"    // httpサーバ関連のヘッダーファイル
#include "esp_timer.h"
#include "esp_camera.h"         // カメラ関連のヘッダーファイル
#include "img_converters.h"
#include "camera_index.h"       // カメラのヘッダーファイル
#include "Arduino.h"

#define AS312_PIN 33    // 人感センサー ピン

// 映像取得 レスポンスヘッダ情報
#define PART_BOUNDARY "123456789000000000000987654321"
static const char *_STREAM_CONTENT_TYPE = "multipart/x-mixed-replace;boundary=" PART_BOUNDARY;
static const char *_STREAM_BOUNDARY = "\r\n--" PART_BOUNDARY "\r\n";
static const char *_STREAM_PART = "Content-Type: image/jpeg\r\nContent-Length: %u\r\n\r\n";

// httpdハンドラ
httpd_handle_t stream_httpd = NULL;
httpd_handle_t camera_httpd = NULL;

// 画像取得
static esp_err_t index_handler(httpd_req_t *req)
{
    camera_fb_t *fb = NULL; // フレーム
    esp_err_t res = ESP_OK; // 成功(ESP_OK)/失敗(ESP_FAIL)フラグ

    fb = esp_camera_fb_get(); // 画像取得

    // 取得失敗 -> Error 500
    if (!fb) {
        httpd_resp_send_500(req);
        return ESP_FAIL;
    }

    // レスポンスヘッダ
    httpd_resp_set_type(req, "image/jpeg");
    httpd_resp_set_hdr(req, "Content-Disposition", "inline; filename=capture.jpg");
    // レスポンスデータ(画像)
    res = httpd_resp_send(req, (const char *)fb->buf, fb->len);

    // リソース解放
    esp_camera_fb_return(fb);

    return res;
}

// 映像取得
static esp_err_t stream_handler(httpd_req_t *req)
{
    camera_fb_t *fb = NULL; // フレーム
    esp_err_t res = ESP_OK; // 成功(ESP_OK)/失敗(ESP_FAIL)フラグ

    // バッファ
    size_t _jpg_buf_len = 0;
    uint8_t *_jpg_buf = NULL;
    char *part_buf[64];

    static int64_t last_frame = 0; // 前回のフレーム送信終了時刻
    if (!last_frame) {
        last_frame = esp_timer_get_time(); // 処理時間 計測開始
    }

    // レスポンスヘッダ
    res = httpd_resp_set_type(req, _STREAM_CONTENT_TYPE);
    // セット失敗 -> 中断
    if (res != ESP_OK) {
        return res;
    }

    // 撮影
    while (true) {
        fb = esp_camera_fb_get(); // フレーム取得
        // 取得失敗 -> 中断
        if (!fb) {
            Serial.printf("Camera capture failed");
            res = ESP_FAIL;
        } else {
            _jpg_buf_len = fb->len;
            _jpg_buf = fb->buf;
        }

        // レスポンスデータ
        if (res == ESP_OK) {
            size_t hlen = snprintf((char *)part_buf, 64, _STREAM_PART, _jpg_buf_len);
            res = httpd_resp_send_chunk(req, (const char *)part_buf, hlen);
        }
        if (res == ESP_OK) {
            res = httpd_resp_send_chunk(req, (const char *)_jpg_buf, _jpg_buf_len);
        }
        if (res == ESP_OK) {
            res = httpd_resp_send_chunk(req, _STREAM_BOUNDARY, strlen(_STREAM_BOUNDARY));
        }

        // フレーム初期化
        if (fb) {
            esp_camera_fb_return(fb);
            fb = NULL;
            _jpg_buf = NULL;
        } else if (_jpg_buf) {
            free(_jpg_buf);
            _jpg_buf = NULL;
        }

        // 送信失敗 -> 中断
        if (res != ESP_OK) {
            break;
        }

        // 現在のフレーム送信終了時刻
        int64_t fr_end = esp_timer_get_time();

        // 処理時間計算
        int64_t frame_time = fr_end - last_frame; // 処理時間
        last_frame = fr_end; // 前回のフレーム送信終了時刻更新
        frame_time /= 1000; // 秒 -> マイクロ秒変換

        // シリアル通信
        Serial.printf("MJPG: %uB %ums (%.1ffps)\n", (uint32_t)(_jpg_buf_len),
                        (uint32_t)frame_time, 1000.0 / (uint32_t)frame_time);
    }

    // リソース解放
    esp_camera_fb_return(fb);
    free(_jpg_buf);

    last_frame = 0; // 前回のフレーム送信終了時刻初期化
    return res;
}

// カメラ映像設定
void camera_setting()
{
    sensor_t *s = esp_camera_sensor_get();

    s->set_framesize(s, (framesize_t)6);  // Resolution
    s->set_quality(s, 10);        // Quality
    s->set_brightness(s, 0);      // Brightness
    s->set_contrast(s, 0);        // Contrast
    s->set_saturation(s, 0);      // Saturation
    s->set_special_effect(s, 0);  // Special effect
    s->set_whitebal(s, 1);        // AWB
    s->set_awb_gain(s, 1);        // AWB Gain
    s->set_wb_mode(s, 0);         // WB mode
    s->set_exposure_ctrl(s, 1);   // AEC Sensor
    s->set_aec2(s, 0);            // AEC DSP
    s->set_ae_level(s, 0);        // AE Level
    s->set_aec_value(s, 1);       // Exposure
    s->set_gain_ctrl(s, 1);       // AGC
    s->set_agc_gain(s, 0);        // Gain
    s->set_gainceiling(s, (gainceiling_t)0); // Gain ceiling
    s->set_bpc(s, 0);             // BPC
    s->set_wpc(s, 1);             // WPC
    s->set_raw_gma(s, 1);         // Raw GMA
    s->set_lenc(s, 1);            // Lens Correction
    s->set_hmirror(s, 1);         // H-Mirror
    s->set_dcw(s, 1);             // DCW (Downsize EN)
    s->set_colorbar(s, 0);        // Color Bar
}

void startCameraServer()
{
    httpd_config_t config = HTTPD_DEFAULT_CONFIG();

    // カメラ映像設定
    camera_setting();
    // 人感センサー セットアップ
    pinMode(AS312_PIN, INPUT);

    // 画像取得 ハンドラ紐付け
    httpd_uri_t index_uri = {
        .uri       = "/",
        .method    = HTTP_GET,
        .handler   = index_handler,
        .user_ctx  = NULL
    };
    Serial.printf("Starting web server on port: '%d'\n", config.server_port);
    if (httpd_start(&camera_httpd, &config) == ESP_OK) {
        httpd_register_uri_handler(camera_httpd, &index_uri);
    }

    // 映像取得 ハンドラ紐付け
    httpd_uri_t stream_uri = {
        .uri       = "/stream",
        .method    = HTTP_GET,
        .handler   = stream_handler,
        .user_ctx  = NULL
    };
    config.server_port += 1;
    config.ctrl_port += 1;
    Serial.printf("Starting stream server on port: '%d'\n", config.server_port);
    if (httpd_start(&stream_httpd, &config) == ESP_OK) {
        httpd_register_uri_handler(stream_httpd, &stream_uri);
    }
}
