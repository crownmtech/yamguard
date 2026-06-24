[app]

# Application title
title = YamGuard

# Package name
package.name = yamguard

# Package domain (needed for android/ios packaging)
package.domain = com.yamguard.app

# Source code directory
source.dir = .

# Application version
version = 1.0.0

# Requirements for the application
requirements = python3,kivy==2.2.1,kivymd==1.1.1,opencv-python==4.8.1.78,numpy==1.24.3,Pillow==10.0.1,matplotlib==3.7.2,reportlab==4.0.4,bcrypt==4.0.1,plyer==2.1.0,requests==2.31.0,scikit-learn==1.3.0,android-permissions==0.0.3

# Garden requirements
garden_requirements = 

# Presplash of the application
presplash.filename = %(source.dir)s/assets/images/presplash.png

# Icon of the application
icon.filename = %(source.dir)s/assets/icons/app_icon.png

# Supported orientation (portrait, landscape, all)
orientation = portrait

# Android API to use
android.api = 33

# Android minimum API to use
android.minapi = 29

# Android SDK version to use
android.sdk = 33

# Android NDK version to use
android.ndk = 25b

# Android private storage controls
android.private_storage = True

# Android NDK directory (if empty, uses buildozer's default)
android.ndk_path = 

# Android SDK directory (if empty, uses buildozer's default)
android.sdk_path = 

# ANT directory (if empty, uses buildozer's default)
android.ant_path = 

# Android entry point
android.entrypoint = org.kivy.android.PythonActivity

# Android app theme
android.apptheme = @android:style/Theme.NoTitleBar

# Android permissions
android.permissions = CAMERA,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,INTERNET,ACCESS_NETWORK_STATE,FLASHLIGHT,FOREGROUND_SERVICE

# Android features
android.features = android.hardware.camera,android.hardware.camera.autofocus,android.hardware.camera.flash

# Android API to use for compiling
android.compile_api = 33

# Android build tools version
android.build_tools = 33.0.0

# Android gradle dependencies
android.gradle_dependencies = 

# Android add Java classes
android.add_src = 

# Android AAR archives
android.add_aars = 

# Android jars
android.add_jars = 

# Android platform libraries
android.add_libs_arm64_v8a = 
android.add_libs_armeabi_v7a = 
android.add_libs_x86 = 
android.add_libs_x86_64 = 

# Android presplash color
android.presplash_color = #16A34A

# Android splash screen
android.splashscreen = 

# Android window background
android.window_background = 

# Android services
# android.services = 

# Android broadcast receivers
# android.broadcast_receivers = 

# Android add activities
android.add_activities = 

# Fullscreen mode
fullscreen = 0

# Android logcat filters
android.logcat_filters = *:S python:D

# Android app library repository
android.repo_url = https://maven.google.com

# Android architectures
android.archs = arm64-v8a, armeabi-v7a

# Android whitelist file
android.whitelist = 

# Android blacklist file
android.blacklist = 

# Android no-byte-compile Python files
android.no-byte-compile-python = False

# Android copy libs
android.copy_libs = 1

# P4A setup
p4a.source_dir = 
p4a.local_recipes = 

# Bootstrap type
p4a.bootstrap = sdl2

# Window backend
kivy.include_packages = 
kivy.exclude_packages = 
kivy.update_config = 

# Buildozer mode
buildozer.warn_on_root = 1

# iOS specific
ios.kivy_version = 2.2.1
ios.codesign.allowed = False
ios.codesign.debug = 
ios.codesign.release = 

# OS X specific
osx.python_version = 3
osx.kivy_version = 1.9.1

# Application build profiles
[buildozer]
log_level = 2
warn_on_root = 1
