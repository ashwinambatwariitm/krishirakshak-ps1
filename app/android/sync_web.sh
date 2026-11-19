#!/usr/bin/env bash
# Copy the farmer web app (app/web, the single source) into the Android app's assets, so the APK shows the same
# app as the Raspberry Pi serves at http://<pi>:8080/. Run after every change in app/web, before building the APK.
#
# Only js/config.js differs: inside the APK the page is not served by the Pi, so its API address defaults to the
# Pi's Wi-Fi hotspot (http://10.42.0.1:8080) instead of "same server". The Pi's web server allows these
# cross-origin calls (CORS headers in cpp/src/web_server.hpp).
set -euo pipefail
cd "$(dirname "$0")/../.."
DST=app/android/app/src/main/assets/web
mkdir -p "$DST"
rsync -a --delete --exclude js/config.js app/web/ "$DST/"
sed -e 's#API_BASE: localStorage.getItem("KR_API_BASE") || ""#API_BASE: localStorage.getItem("KR_API_BASE") || "http://10.42.0.1:8080"#' \
    -e 's#^ \* KrishiRakshak App Configuration$# * KrishiRakshak App Configuration (embedded in the Android APK: API defaults to the Pi hotspot)#' \
    app/web/js/config.js > "$DST/js/config.js"
grep -q '10.42.0.1:8080' "$DST/js/config.js" || { echo "config.js: API address not set"; exit 1; }
echo "synced app/web -> $DST"
