#!/bin/bash
# Run Cpp2IL master with IL recovery for il2cpp -> DLL dump
export DOTNET_ROOT=/home/z/.dotnet PATH=/home/z/.dotnet:$PATH
cd /home/z/my-project/apk_dl
mkdir -p decompiled/cpp2il logs
/home/z/my-project/tools/Cpp2IL-master/Cpp2IL \
  --game-path /home/z/my-project/apk_dl/extracted \
  --force-binary-path /home/z/my-project/apk_dl/extracted/v7a_libs/lib/armeabi-v7a/libil2cpp.so \
  --force-metadata-path /home/z/my-project/apk_dl/extracted/base_unzipped/assets/bin/Data/Managed/Metadata/global-metadata.dat \
  --force-unity-version 6000.3.11 \
  --output-as dll_il_recovery \
  --low-memory-mode \
  --output-to /home/z/my-project/apk_dl/decompiled/cpp2il \
  > logs/cpp2il_master.log 2>&1
echo "cpp2il master exit: $?" >> logs/cpp2il_master.log
