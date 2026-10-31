[app]
title = Spider Android
package.name = spiderandroid
package.domain = org.sabrierkin

source.dir = .
source.include_exts = py,png,jpg,json

version = 1.4.0
requirements = python3,kivy==2.3.0,pyjnius

orientation = portrait
fullscreen = 1
android.archs = arm64-v8a
android.allow_backup = True
android.api = 33
android.minapi = 21
android.ndk = 26b
android.sdk_buildtools_source = cmdline-tools
android.accept_sdk_license = True
