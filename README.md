# Modern Warplanes (Android) — Static Analysis & Reverse-Engineering Methodology

This repository documents a complete **static-analysis pipeline for an Android Unity/IL2CPP
game**, together with the resulting technical findings and the tooling scripts used to
produce them.

Analyzed app: **Modern Warplanes: PvP Warfare** — `com.EvilChaotic.ModernWarplanes`
v1.20.6 (versionCode 303341), obtained from a public APK mirror.

## ⚠️ Scope & legal note — read this first

This repository intentionally contains **analysis artifacts only**:

- ✅ technical findings, asset inventory, native-library ELF analysis
- ✅ methodology documentation and reproducible pipeline scripts
- ❌ **no decompiled game source code** (no smali / Java / C# dumps)
- ❌ **no game assets** (no textures, models, AssetBundles, audio)
- ❌ **no APK / XAPK redistribution**

*Modern Warplanes* is a commercial game; its code and art are copyrighted by the
respective rights holders. Publishing decompiled sources or extracted assets would
constitute redistribution of copyrighted material (and violate GitHub's Terms of
Service). The contents of this repository are the author's own factual analysis of a
publicly distributed app package, in the spirit of published app-security and privacy
research (comparable to Exodus Privacy-style app reports). All trademarks and product
names belong to their respective owners; this project is not affiliated with or endorsed
by them.

## Analyzed app

| Property | Value |
|---|---|
| Package | `com.EvilChaotic.ModernWarplanes` |
| Version | 1.20.6 (versionCode 303341) |
| Engine | Unity 6000.3.11f1 (Unity 6.3 line), **IL2CPP** backend, metadata v39 |
| Native ABI (delivered split) | armeabi-v7a (32-bit ARM), NDK r27c |
| minSdk / targetSdk | 25 (Android 7.1) / 36 (Android 16) |
| Download size | XAPK 150 MB = base APK 119 MB + `config.armeabi_v7a` split 38 MB |

## Key findings (condensed)

Full details in [`reports/02_FINDINGS.md`](reports/02_FINDINGS.md).

**Architecture.** Standard Unity IL2CPP title: a thin Java glue layer (4 DEX, ~21 MB,
dominated by SDKs — Unity player, AndroidX, AppLovin MAX, Play Core/Billing/Games) around
a 69 MB `libil2cpp.so` that carries all game logic as AOT ARM machine code. The C# type
system (104 game-relevant assemblies, 53,219 methods) was fully recovered from IL2CPP
metadata; method bodies remain in native code (expected for IL2CPP AOT).

**Networking.** Three-channel stack: **Photon 3** real-time client for matchmaking/rooms,
**WebRTC** (`Byn.Awrtc` + `libwebrtccsharpwrap.so`) for in-battle voice chat, and a custom
`UDP.dll` gameplay channel. Remote content ships via Unity Addressables from the publisher
CDN `static.planetcommander.ru`.

**Monetization.** AppLovin MAX mediation + AdMob (`ca-app-pub-3197197901838056`), Google
Play Billing + Unity IAP 5.0, Play Games Services v2 (app id `252168717131`). EEA consent
flow via Google UMP (TCF strings). Privacy Sandbox attribution permissions indicate
preparation for Android 16 ad-ID restrictions.

**Permissions.** 14 + 1 custom — all mainstream for an ad-monetized online multiplayer
game (network, audio/record for voice chat, notifications, billing, ad-ID). No location,
contacts or SMS access.

**Assets.** 1,381 indexed files: Unity 6 content-addressed player data (187.7 MB), 41
streaming AssetBundles with 37+ aircraft models, Addressables catalog for map content
("Vulcano", "Atlantic" maps are downloadable, not ship-in-APK).

**Security observations (informational).** No certificate pinning visible in the Java
layer; `LunarConsole` and a `ModernWarplanes.DebugTestMenu` are compiled into the release
build; `libil2cpp.so` is stripped but not packed or obfuscated.

## Repository layout

```
reports/        00_README.md (package overview) · 01_INVENTORY.md (asset inventory)
                02_FINDINGS.md (technical findings) · inventory.json (1,381 files)
                ELF-ANALYSIS.txt (native library analysis)
methodology/    pipeline.md (how everything was produced, incl. workarounds)
                worklog.md (raw session log)
scripts/        reproducible pipeline scripts (bash + python)
```

## Reproducing the pipeline

⚠️ Only run this against apps you are authorized to analyze. The scripts assume a
Debian-ish Linux environment:

```bash
scripts/setup_re_tools.sh      # installs apktool, jadx, apkeep, .NET SDK, Cpp2IL, ilspycmd
# 1. obtain the app package (e.g. apkeep for an XAPK from a mirror you trust)
# 2. unzip the XAPK; merge base APK + config.<abi> split
scripts/run_decompilers.sh     # apktool decode
scripts/run_jadx_perdex.sh     # jadx, one process per DEX (see pipeline.md for why)
scripts/run_cpp2il_master.sh   # Cpp2IL: IL2CPP metadata -> dummy DLLs
scripts/run_ilspy.sh           # ilspycmd: dummy DLLs -> C# sources
scripts/build_inventory.py     # asset inventory (area/magic classification)
scripts/package_deliverable.sh # assemble a local analysis package
```

Notes on the two non-obvious workarounds (details in
[`methodology/pipeline.md`](methodology/pipeline.md)):

1. **jadx OOM** — a full-APK jadx run was killed twice at ~53 % in a 4 GB container.
   Running one jadx process per DEX (`classes`…`classes4`) completes reliably.
2. **Cpp2IL metadata v39** — stable Cpp2IL releases only support metadata v24–29; Unity 6
   ships v39. A master-branch build (needs .NET 10) plus a one-line patch to
   `LibCpp2IL/BinarySearcher.cs` (let the built-in candidate validator disambiguate
   multiple `pCodegenModules` pointers instead of throwing) yields a complete dump:
   53,219 / 53,219 methods across 106 DLLs.

## Tools used (with thanks)

[apktool](https://github.com/iBotPeaches/Apktool) ·
[jadx](https://github.com/skylot/jadx) ·
[Cpp2IL](https://github.com/SamboyCoding/Cpp2IL) ·
[ILSpy](https://github.com/icsharpcode/ILSpy) ·
[apkeep](https://github.com/EFForg/apkeep)

## License

The documentation and scripts in this repository are the author's own work and are
released under the [MIT License](LICENSE). They contain no material from the analyzed
application beyond factual metadata (package names, version numbers, SDK identifiers,
file listings).
