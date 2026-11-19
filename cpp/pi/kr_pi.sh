#!/usr/bin/env bash
# KrishiRakshak on the Raspberry Pi 5: offline Wi-Fi hotspot and start-at-boot service (run on the Pi, with sudo).
#
# Offline use: the Pi makes its own Wi-Fi network "KrishiRakshak"; a phone joins it and opens
# http://10.42.0.1:8080 (the address the Android app uses by default). No router and no internet are needed.
#
#   sudo ./kr_pi.sh hotspot-test [SECONDS]  hotspot for SECONDS (default 300), then back to the home Wi-Fi by itself
#                                         (safe to try: if anything goes wrong the Pi returns to the home network)
#   sudo ./kr_pi.sh hotspot-on              hotspot until hotspot-off (and at every boot, until hotspot-off)
#   sudo ./kr_pi.sh hotspot-off             back to the home Wi-Fi
#   sudo ./kr_pi.sh autostart-on            start the app at boot (systemd service krishirakshak)
#   sudo ./kr_pi.sh autostart-off           stop starting it at boot
#   ./kr_pi.sh status                       network, hotspot and app state
#
# Settings (environment variables): KR_SSID (KrishiRakshak), KR_PSK (Wi-Fi password, default krishi2026, at least
# 8 characters), KR_DIR (app folder, default: this script's folder), KR_USER (user that runs the app, default: the
# user who called sudo).
# Note: while the hotspot is on, the Pi's Wi-Fi is not connected to the home network, so SSH over Wi-Fi stops;
# with an Ethernet cable to the router, SSH keeps working over the cable.
set -euo pipefail

AP=KrishiRakshak-AP
SSID=${KR_SSID:-KrishiRakshak}
PSK=${KR_PSK:-krishi2026}
DIR=${KR_DIR:-$(cd "$(dirname "$0")" && pwd)}
RUN_USER=${KR_USER:-${SUDO_USER:-$(id -un)}}
STATE=/var/lib/krishirakshak
SERVICE=/etc/systemd/system/krishirakshak.service

need_root() { [ "$(id -u)" -eq 0 ] || { echo "run with sudo: sudo $0 $*"; exit 1; }; }

home_wifi() {
    # The Wi-Fi profile that was active before the hotspot (saved by hotspot-on), else the first other Wi-Fi profile
    if [ -s "$STATE/home_wifi" ]; then cat "$STATE/home_wifi"; return; fi
    nmcli -t -f NAME,TYPE con show | awk -F: -v ap="$AP" '$2=="802-11-wireless" && $1!=ap {print $1; exit}'
}

ensure_ap_profile() {
    [ ${#PSK} -ge 8 ] || { echo "KR_PSK must have at least 8 characters"; exit 1; }
    if ! nmcli -t -f NAME con show | grep -qx "$AP"; then
        # ipv4.method shared: the Pi is 10.42.0.1 and gives phones addresses by DHCP (NetworkManager's dnsmasq)
        # band bg (2.4 GHz): every phone can join; WPA2 with a password
        nmcli con add type wifi ifname wlan0 con-name "$AP" autoconnect no ssid "$SSID" \
            802-11-wireless.mode ap 802-11-wireless.band bg ipv4.method shared ipv6.method disabled \
            wifi-sec.key-mgmt wpa-psk wifi-sec.proto rsn wifi-sec.pairwise ccmp wifi-sec.psk "$PSK" > /dev/null
    else
        nmcli con modify "$AP" 802-11-wireless.ssid "$SSID" wifi-sec.psk "$PSK"
    fi
}

save_home_wifi() {
    mkdir -p "$STATE"
    local active
    active=$(nmcli -t -f NAME,TYPE con show --active | awk -F: -v ap="$AP" '$2=="802-11-wireless" && $1!=ap {print $1; exit}')
    [ -n "$active" ] && echo "$active" > "$STATE/home_wifi"
    return 0
}

hotspot_up() {
    ensure_ap_profile
    save_home_wifi
    nmcli con up "$AP" > /dev/null
    echo "hotspot on: Wi-Fi \"$SSID\" (password $PSK) -> open http://10.42.0.1:8080 on the phone"
}

hotspot_down() {
    nmcli con down "$AP" > /dev/null 2>&1 || true
    nmcli con modify "$AP" connection.autoconnect no > /dev/null 2>&1 || true
    local home
    home=$(home_wifi)
    if [ -n "$home" ]; then nmcli con up "$home" > /dev/null && echo "back on home Wi-Fi: $home"; fi
}

status() {
    echo "== network"; nmcli -t -f NAME,TYPE,DEVICE con show --active | grep -v ':loopback:' || true
    ip -4 -br addr show wlan0 2>/dev/null || true
    echo "== app"
    if systemctl is-enabled krishirakshak > /dev/null 2>&1; then echo "start at boot: on ($(systemctl is-active krishirakshak))"
    else echo "start at boot: off"; fi
    if curl -s --max-time 3 http://127.0.0.1:8080/api/info > /dev/null; then echo "app: answering on port 8080"
    else echo "app: not answering on port 8080"; fi
}

case "${1:-status}" in
    hotspot-test)
        need_root "$@"
        secs=${2:-300}
        hotspot_up
        echo "test mode: back to the home Wi-Fi in $secs s"
        # detached, so the switch back also happens if this terminal or SSH session is lost
        systemd-run --unit=krishirakshak-hotspot-revert --on-active="${secs}s" --quiet \
            /bin/bash "$DIR/$(basename "$0")" hotspot-off
        ;;
    hotspot-on)
        need_root "$@"
        hotspot_up
        nmcli con modify "$AP" connection.autoconnect yes connection.autoconnect-priority 100
        echo "the hotspot also starts at every boot until: sudo $0 hotspot-off"
        ;;
    hotspot-off)
        need_root "$@"
        hotspot_down
        ;;
    autostart-on)
        need_root "$@"
        [ -x "$DIR/krishirakshak" ] || { echo "no krishirakshak binary in $DIR (set KR_DIR)"; exit 1; }
        cat > "$SERVICE" <<EOF
[Unit]
Description=KrishiRakshak offline crop advisor (web app on port 8080)
After=network.target

[Service]
User=$RUN_USER
WorkingDirectory=$DIR
ExecStart=$DIR/krishirakshak --root . --serve 8080 --web app/web
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
        systemctl daemon-reload
        systemctl enable --now krishirakshak > /dev/null
        echo "app starts at boot (service krishirakshak); now: $(systemctl is-active krishirakshak)"
        ;;
    autostart-off)
        need_root "$@"
        systemctl disable --now krishirakshak > /dev/null 2>&1 || true
        rm -f "$SERVICE"; systemctl daemon-reload
        echo "app no longer starts at boot"
        ;;
    status) status ;;
    *) sed -n '2,20p' "$0"; exit 2 ;;
esac
