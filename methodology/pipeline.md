# Analysis Pipeline — How the results were produced

This document records the full reverse-engineering pipeline for
`com.EvilChaotic.ModernWarplanes` v1.20.6 (Unity 6000.3.11f1, IL2CPP, metadata v39),
including every workaround that was needed. It is written so the process can be replayed
against other Unity IL2CPP titles (that you are authorized to analyze) without repeating
the same dead ends.

## Environment

- Debian-based Linux container, 4 GB RAM (this constraint drove two of the workarounds)
- Toolchain (installed by `scripts/setup_re_tools.sh`):
  - `apkeep 1.1.0` (Rust, EFF) — app-package download
  - `apktool 2.12.0` — resource/smali decode
  - `jadx 1.5.2` — DEX → Java
  - `.NET 10 SDK` + **Cpp2IL master** (`2022.1.0+b5ad444`) — IL2CPP metadata → dummy DLLs
  - `ilspycmd 9.1.0.7988` (ILSpy) — DLL → C#

## Step 0 — Package acquisition

- Direct mirror scraping failed (Cloudflare interstitials on plain `curl`), so the XAPK
  was fetched with `apkeep` (handles the mirror's challenge/redirect flow):
  `com.EvilChaotic.ModernWarplanes@1.20.6@arm64-v8a.xapk` (150 MB).
- An XAPK is a ZIP of split APKs. This one contained the **base APK (119 MB)** plus a
  single native split: `config.armeabi_v7a` (38 MB). Note the trap: the file name says
  `arm64-v8a`, the delivered native split is actually **32-bit armeabi-v7a**. The base
  APK has no `lib/` directory of its own.
- Manifest facts confirmed up front: `minSdk 25`, `targetSdk 36`,
  `installLocation=internalOnly`, launcher `com.unity3d.player.UnityPlayerActivity`,
  OpenGL ES 3.0 required.

## Step 1 — apktool decode

Straightforward run of `apktool d` against the base APK:

- `AndroidManifest.xml` (34 activities, 12 services, 11 receivers, 4 providers — mostly
  SDK components, normal for Unity titles)
- `resources.arsc` → decoded `res/` (3.8 MB, 50+ locales)
- 4 DEX files as smali trees (`smali`, `smali_classes2..4`)
- `assets/` intact, including `bin/Data` (Unity 6 content-addressed player data),
  `aa/` (Addressables) and `StreamingAssets.manifest`

## Step 2 — Java layer with jadx (and the OOM workaround)

- A full-APK jadx run was **OOM-killed twice at ~53 %** in the 4 GB container.
- Workaround (`scripts/run_jadx_perdex.sh`): run one jadx process per DEX
  (`classes.dex` … `classes4.dex`) into separate output dirs → **15,076 Java files**.
- Each per-DEX run still reports 8–22 per-class decompilation errors; affected classes
  are emitted partially with `/* JADX ERROR */` markers. Smali from step 1 is the ground
  truth where Java looks wrong.
- Composition: Unity player, AndroidX (Room, WorkManager, DataStore), AppLovin MAX +
  mediation adapters, Google Play Core/Billing/Play Games/DataTransport, and only a
  small amount of game glue (`ru.*`, `com.EvilChaotic.*`).

## Step 3 — IL2CPP layer with Cpp2IL (metadata v39)

The interesting part. Unity 6 ships **global-metadata.dat version 39**:

1. **Stable Cpp2IL is insufficient** — releases support metadata v24–v29 only and abort
   with `LibCpp2IL: Unsupported metadata version 39`.
2. **Build from master** (`run_cpp2il_master.sh`): clone, install .NET 10 SDK,
   `dotnet build -c Release` → `2022.1.0+b5ad444` supports v23–v108.
3. **Multi-pointer crash** — the run died with
   `Found more than 1 pointer as pCodegenModules`. Root cause: the binary searcher
   finds several candidate pointers for the codegen module array and treats ambiguity
   as fatal, even though it already ships a candidate *validator*.
   **Patch (one behavioral change):** in `LibCpp2IL/BinarySearcher.cs`, replace the
   `throw` for the multiple-candidates case with a fallback that lets the built-in
   candidate validator pick the correct pointer. After rebuilding, the dump completes:
   **106 DLLs, 53,219 / 53,219 methods** recovered.
4. **ILSpy batch pass** (`run_ilspy.sh`): `ilspycmd -p -lv Latest` over the DLLs →
   **6,071 C# files**.

What you get and what you don't:

- ✅ complete **type system**: classes, structs, enums, fields, signatures, attributes,
  string-literal references
- ❌ **method bodies are empty** — IL2CPP is AOT; the actual logic lives in
  `libil2cpp.so` as ARM machine code. Reading real logic requires disassembly
  (Ghidra/radare2) using the addresses from the Cpp2IL output.

## Step 4 — Asset inventory

`scripts/build_inventory.py` walks the decoded trees and classifies every file by area
(`bin/Data`, `aa/`, `StreamingAssets`, `res/`, loose assets) and magic bytes
(Unity serialized-file header, bundle signature, ZIP, PNG/JPG, ELF…). Notable fix-ups:
Unity 6 `split0..N` streamed segments and hex-named files were initially misclassified
and are now mapped to their parent areas.

Results: **1,381 indexed files** (`reports/inventory.json`), among them 41 streaming
AssetBundles — 37+ aircraft models (F-14 … Qaher-313) — and an Addressables catalog
pointing at the publisher CDN `https://static.planetcommander.ru/warplanes/Addressables/14/`.

## Step 5 — Native libraries

The six `.so` files from the v7a split were profiled (sections, dynsym exports,
dependencies, hardening features) — summary in `reports/ELF-ANALYSIS.txt`:

| Library | Size | Notes |
|---|---|---|
| `libil2cpp.so` | 69 MB | all C# logic as ARM code; stripped; intact `il2cpp_*` exports; **no packing/obfuscation** |
| `libunity.so` | 20 MB | Unity 6.3 runtime |
| `libwebrtccsharpwrap.so` | 6.1 MB | WebRTC C# wrapper; links OpenSLES, GLESv2, libandroid |
| `libe_sqlite3.so` | 1.2 MB | SQLitePCLRaw-style |
| `libapplovin-native-crash-reporter.so` | 472 KB | MAX native crash reporter |
| `libmain.so` | 12 KB | Unity bootstrap |

## Gotchas checklist (for the next IL2CPP target)

1. Mirror file names lie about the ABI — check which `config.*` split is actually inside
   the XAPK before planning Ghidra work.
2. Budget RAM before running jadx on multi-DEX apps; per-DEX processes are cheap and
   reliable.
3. For Unity 6 (metadata v39+): Cpp2IL **master** + .NET 10, plus the `BinarySearcher`
   multi-candidate patch described above.
4. APKs with `targetSdk 30+` may ship v2/v3-only signatures — `keytool -printcert
   -jarfile` then fails with "Not a signed jar file"; use `apksigner verify --print-certs`
   instead.
5. Empty C# method bodies are *expected* — don't chase tool flags trying to "fix" it;
   go to disassembly if you need instruction-level logic.
