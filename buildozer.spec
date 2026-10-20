[app]
title = Spider Android
package.name = spiderandroid
package.domain = org.sabrierkin
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json
source.include_patterns = anims/*, *.png
version = 1.4.0

# Gerekli kütüphaneler (hostpython3 eklenerek derleme kararlı hale getirildi)
requirements = python3,kivy,pyjnius,android,hostpython3

# --- ANDROID 14 (API 34) KARARLI AYARLARI ---
android.api = 34
android.minapi = 21
android.ndk = 26b
android.ndk_api = 21

# Derlenecek işlemci mimarileri (Yeni nesil cihazlar için)
android.archs = arm64-v8a, armeabi-v7a

orientation = portrait
android.fullscreen = 1

[buildozer]
log_level = 2
warn_on_root = 1
