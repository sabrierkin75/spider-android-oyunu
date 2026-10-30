[app]
# (str) Title of your application
title = Spider_Android

# (str) Package name
package.name = spiderandroid

# (str) Package domain (needed for android packaging)
package.domain = org.sabrierkin

# (str) Source code where the main.py lives
source.dir = .

# (list) Source files to include (extensions to include)
# NOT: png, json, eye.png, close.png gibi tüm kritik assetler buradaki uzantılar sayesinde APK'ya dahil edilir.
source.include_exts = py,png,jpg,json,kv,atlas

# (list) List of inclusions using pattern matching
source.include_patterns = assets/*, anims/*, *.png, *.json

# (str) Application versioning (method 1)
version = 1.4.0

# (list) Application requirements
# pyjnius kütüphanesi Android arka ışık ve SystemUI kontrolleri için zorunludur.
requirements = python3==3.10.22,kivy==2.3.0,pyjnius,pillow

# (str) Supported orientations (landscape, portrait or all)
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 1

# (list) Permissions
android.permissions = WAKE_LOCK

# (int) Target Android API, should be as high as possible.
android.api = 33

# (int) Minimum API your APK will support.
android.minapi = 21

# (int) Android SDK version to use
# android.sdk = 33

# (str) Android NDK version to use
# android.ndk = 25b

# (bool) If True, then skip trying to update the Android sdk dependency
android.skip_update = False

# (bool) If True, then automatically accept SDK license agreements
android.accept_sdk_license = True

# (str) The Android architectural undesirable to target (armeabi-v7a, arm64-v8a, x86, x86_64)
android.archs = arm64-v8a

[buildozer]
# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1
