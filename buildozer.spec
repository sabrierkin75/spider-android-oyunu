
[app]
title = Spider Android
package.name = spiderandroid
package.domain = org.sabrierkin

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

# İzinler (Gerekliyse ekleyin, kodunuzda özel bir izin görünmüyor)
# android.permissions = INTERNET

[buildozer]
log_level = 2
warn_on_root = 1
