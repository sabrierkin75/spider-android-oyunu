[app]
title = Spider Android
package.name = com.spiderandroid
package.domain = org.sabrierkin

# --- BU SATIR EKSİK OLDUĞU İÇİN HATA ALIYORDUNUZ ---
# Nokta (.), ana dizindeki tüm dosyaları (main.py dahil) kaynak olarak kabul eder.
source.dir = .

# Kaynak kodların uzantıları
source.include_exts = py,png,jpg,kv,atlas,json

# Proje dizinindeki alt klasörler (anims klasörünü dahil etmek için)
source.include_patterns = anims/*, *.png

version = 1.4.0
requirements = python3,kivy,pyjnius,android

# --- ANDROID 14 (API 34) İÇİN KRİTİK AYARLAR ---
android.api = 34
android.minapi = 21
android.ndk = 26b
android.ndk_api = 21

# Ekran yönü ve tam ekran ayarları
orientation = portrait
android.fullscreen = 1

[buildozer]
log_level = 2
warn_on_root = 1
