[app]
title = M.C. - Music Catcher
package.name = musiccatcher
package.domain = org.ytgrab
version = 1.0.0

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json

# KivyMD 2.0 pulls in materialyoucolor / asynckivy / materialshapes
requirements = python3,
    kivy==2.3.0,
    https://github.com/kivymd/KivyMD/archive/master.zip,
    materialyoucolor,
    asyncgui,
    asynckivy,
    materialshapes,
    exceptiongroup,
    yt-dlp,
    pillow,
    certifi,
    pyjnius,
    android,
    ffpyplayer

android.permissions = INTERNET, WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE
android.api = 34
android.minapi = 26
android.archs = arm64-v8a
android.accept_sdk_license = True
p4a.bootstrap = sdl2

orientation = portrait
fullscreen = 0
log_level = 2

[buildozer]
log_level = 2
warn_on_root = 1
