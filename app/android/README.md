# KrishiRakshak Native Android App (Phase 2 Preview)

This directory contains the native Android Studio project for the KrishiRakshak farmer application.

## Overview
* Native Android wrapper around the offline KrishiRakshak farmer interface.
* Configured to connect directly to the Raspberry Pi 5 Wi-Fi hotspot (`http://10.42.0.1:8080`) or local mock server.
* Native `WebChromeClient` integration handles camera capture (`capture="environment"`) and gallery photo selection with runtime Android permissions.

## Building the APK
1. Open this folder (`app/android`) in Android Studio (Hedgehog / Iguana or later).
2. Sync Gradle files.
3. Build the APK:
   * **In Android Studio:** Select `Build` > `Build Bundle(s) / APK(s)` > `Build APK(s)`.
   * **Via Gradle CLI:**
     ```bash
     ./gradlew assembleDebug
     ```
4. Install the generated APK on your Android device:
   ```bash
   adb install app/build/outputs/apk/debug/app-debug.apk
   ```

## Hotspot Connection
1. Power on the Raspberry Pi 5 running `krishirakshak --serve 8080`.
2. Turn off mobile data on the phone.
3. Connect the phone's Wi-Fi to the Pi hotspot (e.g. `KrishiRakshak-Pi`).
4. Launch the app.
