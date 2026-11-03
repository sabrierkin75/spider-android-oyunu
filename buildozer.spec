[app]
title = Spider Android
package.name = spiderandroid
package.domain = org.sabrierkin

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json
# Proje dizininde setup.py algılanması için şu satırın önündeki '#' işaretini kaldırın veya ekleyin:
android.ignore_setup_py = True
# (Büyük/küçük harf duyarlılığı veya alt klasör kaçırma riskini bitirir)
#source.include_patterns = anims/*, anims/**/*, *.json, anims/*.png, anims/**/*.png
icon.filename = %(source.dir)s/spider.png
version = 1.4.0
requirements = python3,kivy==2.3.0,pyjnius

orientation = portrait, landscape
fullscreen = 1
android.archs = arm64-v8a
android.allow_backup = True
android.api = 33
android.minapi = 21
# Sanal makinedeki NDK 27 sürümünün kararlı çalışması için API hedefini yükseltin
android.ndk_api = 21
# Gradle'ın modern AndroidX kütüphanelerini yükleyebilmesi için bu değeri kesinlikle 1 yapın
android.enable_androidx = 1
android.sdk_buildtools_source = cmdline-tools
android.accept_sdk_license = True
p4a.branch = release-2024.01.21
