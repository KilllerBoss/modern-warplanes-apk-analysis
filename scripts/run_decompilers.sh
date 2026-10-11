#!/bin/bash
# Run apktool + jadx decompilation in parallel, log to files
cd /home/z/my-project/apk_dl
mkdir -p decompiled logs

APK="extracted/com.EvilChaotic.ModernWarplanes.apk"

echo "[*] Starting apktool $(date)"
nohup java -jar /home/z/my-project/tools/apktool.jar d -f -o decompiled/apktool "$APK" \
  > logs/apktool.log 2>&1 &
APKTOOL_PID=$!
echo "apktool PID: $APKTOOL_PID"

echo "[*] Starting jadx $(date)"
JAVA_OPTS="-Xmx3g" nohup /home/z/my-project/tools/jadx/bin/jadx \
  -d decompiled/jadx --show-bad-code -j 2 "$APK" \
  > logs/jadx.log 2>&1 &
JADX_PID=$!
echo "jadx PID: $JADX_PID"

echo "[*] Waiting for both to finish..."
wait $APKTOOL_PID; APKTOOL_RC=$?
echo "apktool exit: $APKTOOL_RC ($(date))"
wait $JADX_PID; JADX_RC=$?
echo "jadx exit: $JADX_RC ($(date))"
echo "[+] Both done. Sizes:"
du -sh decompiled/apktool decompiled/jadx 2>/dev/null
