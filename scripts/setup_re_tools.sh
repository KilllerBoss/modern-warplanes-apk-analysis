#!/bin/bash
# Setup reverse-engineering toolchain (jadx + apktool) for APK analysis
set -e
TOOLS=/home/z/my-project/tools
mkdir -p "$TOOLS"
cd "$TOOLS"

echo "[*] Trying jadx download..."
ok=0
for VER in 1.5.2 1.5.1 1.5.0 1.4.7; do
  URL="https://github.com/skylot/jadx/releases/download/v${VER}/jadx-${VER}.zip"
  if curl -sfL --max-time 180 -o jadx.zip "$URL"; then
    echo "[+] jadx ${VER} downloaded ($(du -h jadx.zip | cut -f1))"
    ok=1; break
  fi
done
if [ $ok -eq 1 ]; then
  unzip -q -o jadx.zip -d jadx
  chmod +x jadx/bin/jadx
  ./jadx/bin/jadx --version
else
  echo "[-] jadx download failed"
fi

echo "[*] Trying apktool download..."
ok=0
for VER in 2.12.0 2.11.1 2.10.0 2.9.3; do
  URL="https://github.com/iBotPeaches/Apktool/releases/download/v${VER}/apktool_${VER}.jar"
  if curl -sfL --max-time 120 -o apktool.jar "$URL"; then
    echo "[+] apktool ${VER} downloaded ($(du -h apktool.jar | cut -f1))"
    ok=1; break
  fi
done
if [ $ok -eq 1 ]; then
  java -jar apktool.jar --version
else
  echo "[-] apktool download failed"
fi

echo "[*] Checking apt availability of auxiliary tools..."
which aapt aapt2 dexdump baksmali r2 radare2 2>/dev/null || true
echo "[+] Done"
