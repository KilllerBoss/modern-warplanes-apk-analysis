#!/bin/bash
# Run jadx decompilation (solo, no resource decoding) - survives via script wrapper
cd /home/z/my-project/apk_dl
mkdir -p logs decompiled/jadx
export JAVA_OPTS="-Xmx2200m"
/home/z/my-project/tools/jadx/bin/jadx \
  -d decompiled/jadx --no-res --show-bad-code -j 2 \
  extracted/com.EvilChaotic.ModernWarplanes.apk \
  > logs/jadx2.log 2>&1
echo "jadx exit: $?" >> logs/jadx2.log
