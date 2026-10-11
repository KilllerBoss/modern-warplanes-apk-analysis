# Worklog

---
Task ID: 1
Agent: Super Z (main)
Task: Decompile "Modern Warplanes: PvP Warfare.apk" — asset inventory focus, full-scope analysis, source tree zip deliverable

Work Log:
- Verified no APK in workspace; user chose "download from public mirror"
- Installed toolchain: apktool 2.12.0, jadx 1.5.2 (GitHub releases), apkeep 1.1.0, .NET 10 SDK, Cpp2IL master build, ilspycmd 9.1
- Downloaded XAPK via apkeep from APKPure: com.EvilChaotic.ModernWarplanes@1.20.6@arm64-v8a.xapk (150 MB) — contains base APK (119 MB) + config.armeabi_v7a split (38 MB, labeled arm64 but actually v7a)
- Identified engine: Unity 6000.3.11f1, IL2CPP metadata v39, minSdk 25, targetSdk 36
- apktool decode: complete (AndroidManifest, res, 4x smali trees, assets)
- jadx: first full-APK runs OOM-killed at ~53% twice (4 GB container limit); solved by per-DEX runs → 15,076 Java files
- Cpp2IL stable rejects metadata v39 (supports 24-29); built master (2022.1.0+b5ad444, supports 23-108); hit "Found more than 1 pointer as pCodegenModules" → patched LibCpp2IL/BinarySearcher.cs to let the built-in candidate validator disambiguate instead of throwing → 53,219/53,219 methods, 106 DLLs
- ILSpy batch decompile of 24 game-relevant DLLs → 6,071 C# files (type system recovered; method bodies remain in libil2cpp.so ARM code — ARM32 IL recovery not populated)
- Built asset inventory (scripts/build_inventory.py): 1,381 files classified by area/magic; 41 streaming bundles (37+ aircraft models); Addressables CDN static.planetcommander.ru; fixed .split/hex-file misclassification
- Wrote 00_README.md, 01_INVENTORY.md, 02_FINDINGS.md (SDK stack: AppLovin MAX, AdMob pub-3197197901838056, Play Games 252168717131, Photon, WebRTC voice, UGS analytics, IAP)
- Assembled package and zipped: /home/z/my-project/download/ModernWarplanes_v1.20.6_decompiled.zip (192 MB, 47,458 files, integrity verified)

Stage Summary:
- Deliverable: download/ModernWarplanes_v1.20.6_decompiled.zip — apktool tree, jadx Java, il2cpp C# + DLLs, native libs + ELF report, inventory JSON/MD, findings
- Key scripts persisted in scripts/: setup_re_tools.sh, run_decompilers.sh, run_jadx.sh, run_jadx_perdex.sh, run_cpp2il_master.sh, run_ilspy.sh, build_inventory.py, package_deliverable.sh
- Patched Cpp2IL source at tools/Cpp2IL-src (BinarySearcher.cs multi-candidate fix)
- Caveats documented in README: v7a-only native split, empty C# method bodies, jadx per-class error counts, v2/v3-only APK signature
