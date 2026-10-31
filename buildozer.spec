[app]

# (str) Uygulama başlığı
title = Spider Android

# (str) Paket ismi (Boşluksuz ve küçük harflerle)
package.name = spiderandroid

# (str) Paket domain adresi (Kurumsal kimlik için)
package.domain = org.sabrierkin

# (str) Ana giriş kodunun bulunduğu dizin
source.dir = .

# (list) APK içerisine dahil edilecek uzantılar
# NOT: .json, .png uzantıları ve anims klasörünüz APK içine mutlaka eklenmelidir!
source.include_exts = py,png,jpg,json,kv,atlas

# (list) APK içerisine dahil edilecek özel klasör isimleri
source.include_patterns = anims/*

# (str) Uygulama versiyonu
version = 1.4.0

# (list) Uygulama gereksinimleri (Kivy ve Android kütüphaneleri)
# Pyjnius ve Android paketleri kodunuzdaki Java sınıflarını (autoclass) çağırır.
requirements = python3,kivy==2.3.0,pyjnius,android

# (str) Desteklenen ekran yönü (Kodunuz iki yönü de destekliyor)
orientation = portrait

# (bool) Uygulama tam ekran mı başlayacak
fullscreen = 1

# (list) Android İzinleri (Gerekirse wakelock eklenebilir)
# android.permissions = WAKE_LOCK

# -----------------------------------------------------------------------------
# Android Yapılandırmaları
# -----------------------------------------------------------------------------

# (int) Android API Hedefi (33 veya 34 güncel cihazlar için idealdir)
android.api = 33

# (int) Minimum Android API Desteği
android.minapi = 21

# (bool) Android kilitlenme koruması için eski grafik motoru uyumluluğu
android.ndk_api = 21

# Build-tools sürümünü açıkça belirtiyoruz:
android.build_tools_version = 33.0.2

# (str) Android NDK sürümü (Kivy 2.3.0 ile kararlı çalışan sürüm)
android.ndk = 25b

# (list) Mimari desteği (Modern telefonlar için arm64-v8a şarttır)
android.archs = arm64-v8a

# (bool) Kalıcı ekran ışığı veya UI thread işlemlerini koşturmak için izin ver
android.meta_data = android.view.View=true

[buildozer]
# (int) Log seviyesi (Hataları görebilmek için 2 kalmalıdır)
log_level = 2

# (int) Buildozer hata durumunda işlemi durdursun mu
warn_on_root = 0
