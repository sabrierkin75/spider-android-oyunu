[app]

# (string) Uygulamanızın ekranda görünecek adı
title = Spider Android

# (string) Paket adı (com.ssae.spiderandroid yapısının son kelimesi)
package.name = spiderandroid

# (string) Şirket/Geliştirici alan adı (com.ssae.spiderandroid yapısının ilk iki kelimesi)
package.domain = com.ssae

# (string) Kodların ve görsellerin bulunduğu ana dizin (.)
source.dir = .

# (list) Uygulamaya dahil edilecek dosya uzantıları
source.include_exts = py,png,jpg,kv,atlas,json

# (list) Dahil edilecek özel klasörler (Görsellerinizin olduğu anims klasörü)
source.include_patterns = anims/*, anims/*/*, eye.png, close.png, awake.png, sleep.png

# uygulama simgesi
icon.filename = spider.png

# (string) Uygulamanın versiyonu
version = 1.4.0

# (list) Uygulamanın çalışması için gereken Python kütüphaneleri
# GitHub'daki HTML/Şablon çökmesini engellemek için jinja2 eklenmiştir.
requirements = python3, kivy==2.3.0, jinja2, requests

# (str) Uygulamanın başlangıç ekranı yönü (Uygulamanız dikey tasarlanmıştır)
orientation = portrait

# (bool) Uygulamanın tam ekran (Fullscreen) başlamasını zorlar
fullscreen = 1

# =============================================================================
# Android Ayarları
# =============================================================================

# (int) Hedef Android API Seviyesi (Modern Android standartları için API 35 / Android 15)
android.api = 33

# (int) Minimum Android API Seviyesi (Uygulamanın çalışabileceği en eski sürüm: Android 7.0)
android.minapi = 24

# (int) Android SDK Versiyonu
#android.sdk = 34

# (str) Android NDK Versiyonu (Kivy için en kararlı sürüm)
#android.ndk = 25b

# android ndk api
#android.ndk_api = 24

# (bool) Google Play korumaları ve modern Gradle için gerekli olan izin
android.accept_sdk_license = True

# (list) Uygulamanın talep ettiği Android izinleri
# Ekranı açık tutma (WAKE_LOCK) işlevi için gerekli izin eklenmiştir.
android.permissions = WAKE_LOCK

# (list) Desteklenen işlemci mimarileri
# Sadece arm64-v8a seçmek modern cihazların %99'unu kapsar ve paketlemeyi çok hızlandırır.
android.archs = arm64-v8a

# (bool) Uygulamanın telefona kurulduğunda dış hafızaya taşınabilmesine izin verir
android.allow_backup = True

# (string) Android için kullanılacak olan Gradle versiyonu
#android.gradle_dependencies = 'com.android.tools.build:gradle:8.3.2'

# =============================================================================
# Buildozer Gelişmiş Ayarlar
# =============================================================================

[buildozer]

# (int) Log detay seviyesi (2 = Her şeyi terminale yazdırır, hataları görmenizi sağlar)
log_level = 2

# (int) Hatalı derleme durumunda ccache kullanımını aktif tutar
ccache = 1
