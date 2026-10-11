# Technical Findings — Modern Warplanes: PvP Warfare v1.20.6

## 1. App identity and build configuration

The application is a Unity-based online PvP jet fighter game. The base package
`com.EvilChaotic.ModernWarplanes` was built with Unity 6000.3.11f1 (the Unity 6.3
line) using the IL2CPP scripting backend with metadata version 39, compiled for
32-bit ARM (`armeabi-v7a`) in the delivered split, with NDK r27c. The minimum
supported Android version is 7.1 (SDK 25) and it targets Android 16 (SDK 36),
which places it squarely in the modern Play Store compatibility window. The game
declares `installLocation="internalOnly"` and requires OpenGL ES 3.0. The launcher
is the standard `com.unity3d.player.UnityPlayerActivity` locked to
`userLandscape` orientation with notch support enabled.

The manifest declares 34 activities, 12 services, 11 receivers and 4 providers.
The overwhelming majority of these belong to bundled SDKs rather than game code,
which is typical for Unity titles where the Java layer is mostly glue around the
native engine.

## 2. Multiplayer and networking stack

The networking stack is the most interesting architectural aspect. The game ships
**Photon Unity Networking** (`Photon3Unity3D.dll`, the Photon 3 real-time client)
plus a custom `UDP.dll` and `SharedRuntime.dll` assembly, indicating dedicated
gameplay traffic over UDP. Voice chat is implemented with **WebRTC** — the C#
side uses the `Byn.Awrtc` adapter library, and the native side ships as
`libwebrtccsharpwrap.so` (6.1 MB) linking against OpenSLES, GLESv2 and libandroid.
This means in-battle voice is peer/server-relayed WebRTC, while matchmaking and
rooms run over Photon, and a third custom UDP channel carries gameplay state.

Remote content is delivered through Unity Addressables from the developer CDN:
`https://static.planetcommander.ru/warplanes/Addressables/14/` (catalog dated
2026-09-15 in the shipped `settings.json`). The domain confirms the publisher
infrastructure (the same studio ships "Planet Commander"). Content bundles found
in the catalog include `vulcanolevel_assets_all_*.bundle`, `atlantic_assets_all_*.bundle`,
plus `monoscripts` and `unitybuiltinassets` bundles — i.e., maps ("Vulcano",
"Atlantic") are downloadable content rather than ship-in-APK assets.

## 3. Monetization and analytics

Monetization is ad-mediated plus IAP:

- **AppLovin MAX** mediation SDK (full debugger suite present: ~20 `MaxDebugger*`
  activities, `AppLovinFullscreenActivity`, native crash reporter `.so`)
- **Google AdMob** via `com.google.android.gms.ads` with application ID
  `ca-app-pub-3197197901838056~1428016441`
- **Google Play Billing** v5+ (`ProxyBillingActivityV2`, `com.android.vending.BILLING`,
  `CHECK_LICENSE`) and **Unity IAP 5.0.0** as the Unity-side wrapper
- **Play Games Services v2** (`com.google.android.gms.games.APP_ID` = `252168717131`)

Analytics/telemetry: Unity Gaming Services (Core 1.16.0, Analytics 6.2.2) plus
Google DataTransport (CCT backend) for the Google-side event pipeline. The
`user-messaging-platform.properties` and TCF debugger activities indicate a
consent management flow for EEA users (GDPR/TCF strings via the UMP SDK).

## 4. Permissions profile (all 14 + 1 custom)

`INTERNET`, `ACCESS_NETWORK_STATE`, `ACCESS_WIFI_STATE`, `RECORD_AUDIO`,
`MODIFY_AUDIO_SETTINGS` (voice chat), `BLUETOOTH` (headset routing),
`POST_NOTIFICATIONS` (Unity Android Notifications), `VIBRATE`, `WAKE_LOCK`,
`FOREGROUND_SERVICE`, `com.android.vending.BILLING`,
`com.android.vending.CHECK_LICENSE`, `com.google.android.gms.permission.AD_ID`,
`ACCESS_ADSERVICES_AD_ID`, `ACCESS_ADSERVICES_ATTRIBUTION`,
`ACCESS_ADSERVICES_TOPICS` (Privacy Sandbox ad attribution).

Nothing in the permission set is unusual for an ad-monetized online multiplayer
game: no location, no contacts, no SMS. The `queries` block filters for GMS,
Play Billing, Custom Tabs and a handful of intent patterns (sms:/tel: links for
support/social features).

## 5. Code composition

### Java/Kotlin layer (4 DEX, ~21 MB)
Dominated by the Unity player, AndroidX (Room, WorkManager, DataStore, Browser),
AppLovin MAX and its mediation adapters, Google Play Core (Asset Delivery, App
Update, Review, Instant), Billing, Play Games, and DataTransport. Only a small
fraction is game-specific glue (`ru.` and `com.EvilChaotic.*` packages).

### C# layer (104 assemblies, 53,219 methods)
Framework and engine assemblies aside, the notable game-relevant ones are:
`Assembly-CSharp.dll` + `Assembly-CSharp-firstpass.dll` (the game itself),
`SharedRuntime.dll`, `UDP.dll`, `Main.UtilityAssembly.dll`, `Photon3Unity3D.dll`,
`Byn.Awrtc(.Native).dll` (WebRTC), `MaxSdk.Scripts.dll`, `I2Assembly.dll`
(localization), `LunarConsole.dll` (dev console — still compiled in),
`NicknameGenerator.dll`, `ArabicSupport.dll`, `AppStoreSettings.dll`,
`Newtonsoft.Json.dll`, MessagePack and BouncyCastle (from the firstpass dump).
Game namespaces include `ModernWarplanes.Chests`, `.SkillTree`, `.Upgrades`,
`.SocialNetwork`, `.Definitions`, `.ObjectPool`, `.PlayersConstruction` and a
`ModernWarplanes.DebugTestMenu` — the latter two being interesting targets for
understanding build flags.

### Native layer (armeabi-v7a)
`libil2cpp.so` 69 MB (all C# logic as ARM code; stripped, standard il2cpp_*
exports intact, no packing/obfuscation), `libunity.so` 20 MB, `libwebrtccsharpwrap.so`
6.1 MB, `libsqlite3.so` 1.2 MB (SQLitePCLRaw-style, soname `libe_sqlite3.so`),
`libapplovin-native-crash-reporter.so` 472 KB, `libmain.so` 12 KB.

## 6. Asset inventory highlights

- 1,348 files (187.7 MB) of Unity player data under `assets/bin/Data` in the
  Unity 6 content-addressed layout (hash-named serialized files + `split0..N`
  streamed segments), including the 14 MB IL2CPP metadata.
- 41 streaming AssetBundles referenced by `StreamingAssets.manifest` — 37+ aircraft
  models (F-14, F-15, F-16, F-18, F-22, F-35, F-117, J-20, J-14, MiG-29, MiG-35,
  PAK FA, Su-37, Su-47, SR-71, Typhoon, Rafale X-31, Yak-141, A-10, Harrier,
  Tornado, Tejas, Gripen, JF-17, YF-23, X-29, X-47B, X-1 Raven, X-2 Shinshin,
  Morgan, Windhover, Qaher-313, Izdeliye 4, ...) plus two shared texture bundles.
- Addressables catalog (`aa/catalog.bin`, 11 KB) pointing at the
  `static.planetcommander.ru` CDN for level/map content.
- ~10 UI/background images shipped loose in `assets/` (loading screens, seasonal
  backgrounds such as Halloween/Christmas).
- Full decoded `res/` (3.8 MB: icons, strings for 50+ locales, layouts) and
  `resources.arsc` via apktool.

## 7. Security observations (informational)

- No certificate pinning configuration visible in the Java layer; HTTPS endpoints
  are UnityWebRequest-based (standard TLS stack).
- `LunarConsole` and `ModernWarplanes.DebugTestMenu` compiled into release build.
- WebRTC + RECORD_AUDIO active during battles (expected for voice chat).
- Ad/analytics surface is broad but mainstream (MAX + AdMob + UGS + DataTransport);
  the Privacy Sandbox attribution permissions indicate preparation for Android 16
  ad-ID restrictions.
- No native-library packing or anti-tamper shell detected on `libil2cpp.so`
  (standard ELF section layout, intact dynsym exports). Server-authoritative
  gameplay is not verifiable from static analysis alone.
