# KrishiRakshak Android app

The Android app is the farmer's way into KrishiRakshak (Phase 1). It contains the same farmer app pages as the
Raspberry Pi serves (copied from `app/web`) and shows them full screen in a WebView. Every photo and question goes to
the Pi over the Pi's own Wi-Fi hotspot, where all models run. Nothing is analysed on the phone and no internet is
used.

- API address: `http://10.42.0.1:8080` (the Pi hotspot). It can be changed in the app's About screen, for example to
  `http://<pc-address>:8080` for the mock server `tools/mock_api_server.py`.
- Camera and gallery photos through `WebChromeClient`, with Android runtime permissions.
- Read-aloud with the phone's own offline text-to-speech (`AndroidTTS` bridge in `MainActivity.kt`), because the
  Android WebView has no speech synthesis.

## Build the APK

Needs JDK 17 and the Android SDK 34 (or Android Studio).

```
bash app/android/sync_web.sh          # from the repository root: copy app/web into the APK assets
cd app/android
./gradlew assembleDebug
adb install app/build/outputs/apk/debug/app-debug.apk
```

Run `sync_web.sh` after every change in `app/web`. It copies the pages and sets the API address to the Pi hotspot
in the APK's copy of `js/config.js`. The judge screen `demo.html` is not copied (it is for a laptop).

## Use with the Pi

1. Start the Pi (the service starts at boot) and switch on its hotspot: `sudo ./kr_pi.sh hotspot-on`.
2. On the phone: mobile data off, join the Wi-Fi `KrishiRakshak` (password in `cpp/pi/kr_pi.sh`, `KR_PSK`).
3. Open the app and take or choose a photo.
