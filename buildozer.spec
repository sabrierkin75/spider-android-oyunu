[app]
title = Spider Android
package.name = spiderandroid
package.domain = org.sabrierkin

source.dir = .
source.include_exts = py,png,jpg,json

# (str) Icon of the application
icon.filename = %(source.dir)s/spider.png
version = 1.4.0
requirements = python3,kivy==2.3.0

orientation = portrait
fullscreen = 1
android.archs = arm64-v8a
android.allow_backup = True
android.api = 35
android.minapi = 24
android.ndk = 25b
android.ndk_api = 24
android.sdk_buildtools_source = cmdline-tools
android.accept_sdk_license = True
p4a.branch = master
android.additional_cflags = -Wno-error=implicit-function-declaration -Wno-implicit-function-declaration
