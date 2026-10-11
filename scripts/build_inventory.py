#!/usr/bin/env python3
"""Asset inventory builder for Modern Warplanes APK decompilation.
Walks extracted APK, classifies files by magic bytes, parses Unity
AssetBundle manifests, extracts Addressables catalog info, and emits
INVENTORY.md + inventory.json.
"""
import os, json, struct, hashlib
from collections import defaultdict

BASE = "/home/z/my-project/apk_dl/extracted/base_unzipped/assets"
LIBS = "/home/z/my-project/apk_dl/extracted/v7a_libs"
OUT_DIR = "/home/z/my-project/apk_dl/decompiled"
os.makedirs(OUT_DIR, exist_ok=True)

def classify_magic(path):
    """Classify file by extension first, then magic bytes."""
    base = os.path.basename(path)
    root, ext = os.path.splitext(base)
    # Unity-specific extensions that are binary despite appearances
    if ".split" in base:
        return "unity-streamed-segment", "Unity streamed data segment (.splitN)"
    if ext == ".resource":
        return "unity-resource", "Unity resource data"
    if ext == ".assets":
        return "unity-serialized", "Unity serialized .assets file"
    if ext == ".unity3d":
        return "unity-bundle", "Unity asset bundle (.unity3d)"
    if not ext and len(root) == 32 and all(c in "0123456789abcdef" for c in root):
        return "unity-data-hex", "Unity 6 content-addressed data file"
    try:
        with open(path, "rb") as f:
            head = f.read(64)
    except OSError:
        return "unreadable", ""
    if head.startswith(b"UnityFS"):
        return "unity-bundle", "Unity AssetBundle (UnityFS)"
    if head.startswith(b"UnityWeb") or head.startswith(b"UnityRaw"):
        return "unity-web", "Unity streamed bundle"
    if head.startswith(b"\x7fELF"):
        return "elf", "ELF native library"
    if head.startswith(b"\x89PNG"):
        return "png", "PNG image"
    if head.startswith(b"\xff\xd8\xff"):
        return "jpg", "JPEG image"
    if head.startswith(b"\xaf\x1b\xb1\xfa"):
        ver = struct.unpack("<I", head[4:8])[0]
        return "il2cpp-metadata", f"il2cpp global-metadata (v{ver})"
    if head.startswith(b"PK\x03\x04"):
        return "zip", "ZIP container"
    if head.startswith(b"OggS"):
        return "ogg", "Ogg audio"
    if head.startswith(b"RIFF"):
        return "riff", "RIFF (WAV/AVI)"
    if head.startswith(b"{") or head.startswith(b"["):
        # only JSON if the sampled head is fully printable text
        if all(32 <= b < 127 or b in (9, 10, 13) for b in head):
            return "json", "JSON text"
        return "binary-data", "Binary data"
    # Unity serialized file: header version + target as text digits
    try:
        s = head.split(b"\n")[0].decode("ascii", "ignore")
        if s.strip().isdigit():
            return "unity-serialized", "Unity serialized file"
    except Exception:
        pass
    if head[:5] == b"%PDF-":
        return "pdf", "PDF document"
    return "", ""

def human(n):
    for u in ["B", "KB", "MB", "GB"]:
        if n < 1024 or u == "GB":
            return f"{n:.1f} {u}" if u != "B" else f"{n} B"
        n /= 1024

def parse_bundle_manifest(path):
    """Parse Unity AssetBundle .manifest YAML (light parser)."""
    bundle_assets, crc, deps = [], None, []
    in_assets = False
    name = os.path.basename(path).replace(".manifest", "")
    try:
        with open(path, "r", errors="ignore") as f:
            for line in f:
                if line.startswith("CRC:"):
                    crc = line.split(":", 1)[1].strip()
                elif line.startswith("Assets:"):
                    in_assets = True
                elif line.startswith("Dependencies:"):
                    in_assets = False
                    d = line.split(":", 1)[1].strip()
                    if d and d != "[]":
                        deps.append(d)
                elif in_assets and line.startswith("- "):
                    bundle_assets.append(line[2:].strip())
                elif line and not line.startswith((" ", "-", "\t")):
                    in_assets = False
    except OSError:
        pass
    return {"name": name, "crc": crc, "assets": bundle_assets, "dependencies": deps}

def main():
    inv = {"app": "Modern Warplanes: PvP Warfare",
           "package": "com.EvilChaotic.ModernWarplanes",
           "version_name": "1.20.6", "version_code": "303341",
           "unity": "6000.3.11f1", "backend": "il2cpp (metadata v39)",
           "categories": {}, "files": []}

    roots = {"assets": BASE, "native_libs": LIBS}
    cat_stats = defaultdict(lambda: {"count": 0, "bytes": 0, "examples": []})

    for root_label, root in roots.items():
        for dirpath, _, files in os.walk(root):
            for fn in files:
                fp = os.path.join(dirpath, fn)
                rel = os.path.relpath(fp, root)
                size = os.path.getsize(fp)
                kind, desc = classify_magic(fp)
                top = root_label
                # bucket by area
                if root_label == "assets":
                    if rel.startswith("bin/Data/Managed"):
                        area = "il2cpp-metadata"
                    elif rel.startswith("bin/Data"):
                        area = "unity-player-data"
                    elif rel.startswith("aa"):
                        area = "addressables"
                    elif rel.endswith(".manifest"):
                        area = "bundle-manifests"
                    else:
                        area = "streaming-assets"
                else:
                    area = "native-libs"
                cat_stats[area]["count"] += 1
                cat_stats[area]["bytes"] += size
                if kind:
                    cat_stats[f"{area}/{kind}"]["count"] += 1
                    cat_stats[f"{area}/{kind}"]["bytes"] += size
                    if len(cat_stats[f"{area}/{kind}"]["examples"]) < 3:
                        cat_stats[f"{area}/{kind}"]["examples"].append(rel)
                inv["files"].append({"area": area, "path": rel,
                                     "size": size, "type": kind or desc or "unknown"})

    # Parse bundle manifests
    bundles = []
    aman = os.path.join(BASE, "StreamingAssets.manifest")
    bundle_list = []
    if os.path.exists(aman):
        with open(aman) as f:
            for line in f:
                if line.strip().startswith("Name:"):
                    bundle_list.append(line.split("Name:")[1].strip())
    for mf in os.listdir(BASE):
        if mf.endswith(".manifest") and mf != "StreamingAssets.manifest":
            b = parse_bundle_manifest(os.path.join(BASE, mf))
            bundles.append(b)
    inv["streaming_bundle_names"] = bundle_list
    inv["bundle_details"] = bundles

    # Addressables: pull readable strings from catalog.bin
    cat_bin = os.path.join(BASE, "aa/catalog.bin")
    remote_urls, catalog_strings = set(), []
    if os.path.exists(cat_bin):
        data = open(cat_bin, "rb").read()
        # crude printable-string scan for http(s) URLs and .bundle paths
        cur = bytearray()
        for b in data:
            if 32 <= b < 127:
                cur.append(b)
            else:
                if len(cur) >= 8:
                    s = cur.decode("ascii")
                    if ("http" in s and "://" in s) or "planetcommander" in s or "static." in s:
                        remote_urls.add(s)
                    elif s.endswith(".bundle") or ("/" in s and len(s) < 200):
                        catalog_strings.append(s)
                cur = bytearray()
        if len(cur) >= 8:
            catalog_strings.append(cur.decode("ascii"))
    inv["addressables_remote_urls"] = sorted(remote_urls)[:40]
    inv["addressables_sample_entries"] = catalog_strings[:400]

    with open(os.path.join(OUT_DIR, "inventory.json"), "w") as f:
        json.dump(inv, f, indent=1)

    # Markdown summary
    md = ["# Modern Warplanes: PvP Warfare — Asset Inventory",
          "", "Package: `com.EvilChaotic.ModernWarplanes` v1.20.6 (303341)  ",
          "Engine: Unity 6000.3.11f1 (il2cpp, metadata v39)  ",
          "APK size: ~119 MB base + 38 MB armeabi-v7a split", "",
          "## Areas", "", "| Area | Files | Size |", "|---|---|---|"]
    for area in sorted(cat_stats):
        if "/" not in area:
            s = cat_stats[area]
            md.append(f"| {area} | {s['count']} | {human(s['bytes'])} |")
    md += ["", "## Detailed file types per area", "",
           "| Area/Type | Files | Size | Example |", "|---|---|---|---|"]
    for area in sorted(cat_stats):
        if "/" in area:
            s = cat_stats[area]
            ex = s["examples"][0] if s["examples"] else ""
            md.append(f"| {area} | {s['count']} | {human(s['bytes'])} | `{ex}` |")
    md += ["", f"## Streaming AssetBundles ({len(bundle_list)}) — aircraft models & extras", ""]
    md += [f"- {b}" for b in bundle_list]
    md += ["", "## Addressables remote endpoints", ""]
    md += [f"- `{u}`" for u in inv["addressables_remote_urls"][:20]]
    with open(os.path.join(OUT_DIR, "INVENTORY.md"), "w") as f:
        f.write("\n".join(md))

    print("Files indexed:", len(inv["files"]))
    print("Bundles:", len(bundle_list), "| bundle manifests parsed:", len(bundles))
    print("Remote URLs found:", len(inv["addressables_remote_urls"]))
    for area in sorted(cat_stats):
        if "/" not in area:
            print(f"  {area}: {cat_stats[area]['count']} files, {human(cat_stats[area]['bytes'])}")

if __name__ == "__main__":
    main()
