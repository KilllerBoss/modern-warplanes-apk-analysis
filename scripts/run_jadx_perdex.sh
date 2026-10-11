#!/bin/bash
# Decompile each classes.dex separately to bound memory usage
cd /home/z/my-project/apk_dl
mkdir -p dexs decompiled logs
export JAVA_OPTS="-Xmx1700m"

# Extract individual dex files
for d in classes classes2 classes3 classes4; do
  unzip -o -q extracted/com.EvilChaotic.ModernWarplanes.apk "$d.dex" -d dexs/
done
ls -la dexs/

# Decompile one at a time
for d in classes classes2 classes3 classes4; do
  echo "=== jadx on $d.dex $(date +%T) ==="
  /home/z/my-project/tools/jadx/bin/jadx \
    -d "decompiled/jadx-$d" --no-res --show-bad-code -j 2 \
    "dexs/$d.dex" > "logs/jadx_$d.log" 2>&1
  echo "$d exit: $?"
done
echo "=== ALL DEX DONE $(date +%T) ==="
