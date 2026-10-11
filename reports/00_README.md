# Modern Warplanes: PvP Warfare — Decompilation Package

**Package:** `com.EvilChaotic.ModernWarplanes` v1.20.6 (versionCode 303341)
**Engine:** Unity 6000.3.11f1 — IL2CPP (metadata v39), ARM (armeabi-v7a)
**Source APK:** APKPure mirror, obtained via `apkeep` (base APK 119 MB + config.armeabi_v7a split 38 MB)
**Produced:** 2026-10-11

## What is in this package

| Directory | Contents | How it was produced |
|---|---|---|
| `apktool/` | Decoded `AndroidManifest.xml`, `resources.arsc` → `res/`, all 4 DEX files as smali, original `assets/`, `apktool.yml` | apktool 2.12.0 |
| `jadx-java/` | Full Java sources for the Android layer (Unity player, AndroidX, AppLovin MAX, Play Core, Billing, etc.) | jadx 1.5.2, per-DEX |
| `il2cpp-csharp/` | C# sources reconstructed from IL2CPP metadata — class names, namespaces, fields, method signatures, attributes | Cpp2IL (master, patched) + ILSpy 9.1 |
| `il2cpp-dlls/` | The 106 dummy DLLs the C# sources were decompiled from (open them in ILSpy/dnSpy yourself) | Cpp2IL |
| `native-libs/` | The 6 native `.so` libraries (armeabi-v7a) + ELF analysis report | extracted from config split |
| `01_INVENTORY.md` | Master asset inventory: every area, file type, bundle and remote endpoint | see below |
| `inventory.json` | Machine-readable version of the inventory (1,381 indexed files) | Python script |
| `02_FINDINGS.md` | Condensed technical findings: SDK stack, permissions, architecture | — |

## Important caveats

1. **C# method bodies are not recovered.** The game logic is AOT-compiled into
   `native-libs/libil2cpp.so` as ARM machine code. What IL2CPP tools recover is the
   complete *type system*: every class, struct, enum, field, property, method
   signature, string literal reference and attribute. Reading actual instruction
   logic requires disassembly of `libil2cpp.so` (Ghidra/radare2 + the addresses in
   the Cpp2IL output).
2. **The XAPK from APKPure was labeled arm64-v8a but contains the
   `config.armeabi_v7a` split** (32-bit ARM native libraries). The base APK has no
   `lib/` folder of its own. If you need the 64-bit `libil2cpp.so`, pull the
   `config.arm64_v8a` split from another mirror or an installed device.
3. **jadx reported 8–22 per-class errors per DEX** (`ERROR - finished with errors`).
   These classes are still emitted, partially decompiled, marked with `/* ... */
   /* JADX ERROR */` comments. Smali in `apktool/smali*` is 100 % complete — use it
   as ground truth where Java looks wrong.
4. **APK signature:** the APK uses v2/v3 signature schemes only (no JAR/v1
   signature), which is expected for `targetSdk 36`. `keytool -printcert -jarfile`
   reports "Not a signed jar file" for this reason.

## Quick navigation tips

- App entry point: `apktool/AndroidManifest.xml` → `com.unity3d.player.UnityPlayerActivity`
- Unity runtime configuration: `apktool/assets/bin/Data/` (Unity 6 hashed player-data layout)
- Remote content: `apktool/assets/aa/` (Addressables catalog; CDN host `static.planetcommander.ru`)
- Aircraft models: 41 streaming AssetBundles listed in `apktool/assets/StreamingAssets.manifest`
- Game C# namespaces: start at `il2cpp-csharp/Assembly-CSharp/` (UI, aircraft,
  battle, economy) and `il2cpp-csharp/Assembly-CSharp-firstpass/` (plugins, SDK glue)

## Reproduction / tooling provenance

- `apkeep 1.1.0` (EFF) — APKPure download (`acknowledge_dangers=true,arch=arm64-v8a`)
- `apktool 2.12.0` — resource + smali decode
- `jadx 1.5.2` — DEX → Java (run per-DEX: `classes`, `classes2`, `classes3`, `classes4`)
- `Cpp2IL 2022.1.0+b5ad444` (built from master, 2026-09-12) — IL2CPP metadata v39 dump.
  One-line patch applied: `LibCpp2IL/BinarySearcher.cs` no longer throws when
  multiple `pCodegenModules` candidates are found; the built-in candidate validator
  disambiguates instead. Result: 53,219 / 53,219 methods, 106 DLLs.
- `ilspycmd 9.1.0.7988` (ILSpy) — DLL → C# (`-p -lv Latest`)
