#!/bin/bash
# Assemble final deliverable tree and zip it
set -e
PKG=/home/z/my-project/apk_dl/package/ModernWarplanes_v1.20.6_decompiled
DEC=/home/z/my-project/apk_dl/decompiled
DL=/home/z/my-project/download

rm -rf /home/z/my-project/apk_dl/package
mkdir -p "$PKG/native-libs" "$DL"

# 1. Docs
cp "$DEC/00_README.md" "$PKG/"
cp "$DEC/02_FINDINGS.md" "$PKG/"
cp "$DEC/INVENTORY.md" "$PKG/01_INVENTORY.md"
cp "$DEC/inventory.json" "$PKG/"

# 2. apktool output (manifest, res, smali, assets)
cp -r "$DEC/apktool" "$PKG/apktool"

# 3. Merge jadx java sources (per-DEX outputs) into one tree
mkdir -p "$PKG/jadx-java/sources"
for d in classes classes2 classes3 classes4; do
  if [ -d "$DEC/jadx-$d/sources" ]; then
    cp -rn "$DEC/jadx-$d/sources/." "$PKG/jadx-java/sources/" 2>/dev/null || true
  fi
done

# 4. il2cpp C# + DLLs
cp -r "$DEC/ilspy-csharp" "$PKG/il2cpp-csharp"
cp -r "$DEC/cpp2il" "$PKG/il2cpp-dlls"

# 5. Native libs + analysis report
cp /home/z/my-project/apk_dl/extracted/v7a_libs/lib/armeabi-v7a/*.so "$PKG/native-libs/"
{
  echo "Native libraries (armeabi-v7a, ELF32 ARM) — Modern Warplanes v1.20.6"
  echo "=================================================================="
  echo
  for f in "$PKG"/native-libs/*.so; do
    echo "### $(basename $f) ($(du -h "$f" | cut -f1))"
    readelf -h "$f" 2>/dev/null | grep -E "Class|Machine|Type:" | sed 's/^/    /'
    readelf -d "$f" 2>/dev/null | grep -E "SONAME" | sed 's/^/    /'
    file "$f" | sed 's/^/    /'
    echo
  done
} > "$PKG/native-libs/ELF-ANALYSIS.txt"

echo "=== Package tree ==="
du -sh "$PKG"/* | sort -rh

echo "=== Zipping (this may take a few minutes) ==="
cd /home/z/my-project/apk_dl/package
zip -q -r -9 "$DL/ModernWarplanes_v1.20.6_decompiled.zip" ModernWarplanes_v1.20.6_decompiled
echo "=== DONE ==="
ls -lh "$DL/ModernWarplanes_v1.20.6_decompiled.zip"
