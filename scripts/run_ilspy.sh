#!/bin/bash
# Decompile game-relevant il2cpp DLLs to C# source with ILSpy
export DOTNET_ROOT=/home/z/.dotnet PATH=/home/z/.dotnet/tools:/home/z/.dotnet:$PATH
CPP2IL=/home/z/my-project/apk_dl/decompiled/cpp2il
OUT=/home/z/my-project/apk_dl/decompiled/ilspy-csharp
mkdir -p "$OUT"

DLLS="Assembly-CSharp Assembly-CSharp-firstpass SharedRuntime UDP Main.UtilityAssembly \
Photon3Unity3D Byn.Awrtc Byn.Awrtc.Native MaxSdk.Scripts NicknameGenerator LunarConsole \
I2Assembly ArabicSupport AppStoreSettings Google.Play.Games Google.Play.Core \
Google.Play.AssetDelivery Google.Play.AppUpdate Google.Play.Review Google.Play.Instant \
Newtonsoft.Json"

for d in $DLLS; do
  f="$CPP2IL/$d.dll"
  [ -f "$f" ] || { echo "skip (missing): $d"; continue; }
  echo "=== ilspycmd $d $(date +%T) ==="
  timeout 240 ilspycmd -p -lv Latest -o "$OUT/$d" "$f" 2>&1 | grep -iE "error|warning" | head -3
  echo "$d exit: $?"
done
echo "=== ALL ILSPY DONE $(date +%T) ==="
