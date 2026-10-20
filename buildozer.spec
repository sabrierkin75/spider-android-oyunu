[app]
title = Spider Android
package.name = spiderandroid
package.domain = org.sabrierkin
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json
source.include_patterns = anims/*, *.png
version = 1.4.0

# --- KRİTİK DEĞİŞİKLİK ---
# hostpython3'ü tamamen kaldırıyoruz. Böylece sistem sıfırdan Python derleme döngüsüne girip kilitlenmeyecek.
requirements = python3==3.11.9,kivy,pyjnius,android

# --- ANDROID 14 (API 34) GÜVENLİ AYARLARI ---
android.api = 34
android.minapi = 21
android.ndk = 26b
android.ndk_api = 21

# İşlemci mimarileri
android.archs = arm64-v8a, armeabi-v7a

orientation = portrait
android.fullscreen = 1

[buildozer]
log_level = 2
warn_on_root = 1
