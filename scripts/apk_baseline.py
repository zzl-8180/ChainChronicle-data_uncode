"""Read-only APK baseline; extracts only program/config files needed for analysis."""
import argparse
import hashlib
import json
import zipfile
from collections import Counter
from pathlib import Path

from pyaxmlparser.axmlprinter import AXMLPrinter


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("apk", type=Path)
    parser.add_argument("--work", type=Path, default=Path("work/apk"))
    parser.add_argument("--output", type=Path, default=Path("output/apk"))
    args = parser.parse_args()
    args.work.mkdir(parents=True, exist_ok=True)
    args.output.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(args.apk) as archive:
        entries = [{"path": i.filename, "size": i.file_size,
                    "compressed_size": i.compress_size, "crc32": f"{i.CRC:08x}"}
                   for i in archive.infolist()]
        with (args.output / "entries.jsonl").open("w", encoding="utf-8") as out:
            for entry in entries:
                out.write(json.dumps(entry, ensure_ascii=False) + "\n")
        manifest = AXMLPrinter(archive.read("AndroidManifest.xml"))
        root = manifest.get_xml_obj()
        ns = "{http://schemas.android.com/apk/res/android}"
        identity = {"package": root.get("package"),
                    "version_name": root.get(ns + "versionName"),
                    "version_code": root.get(ns + "versionCode"),
                    "uses_sdk": dict(root.find("uses-sdk").attrib)}
        (args.output / "AndroidManifest.xml").write_bytes(manifest.get_xml())
        wanted = {"AndroidManifest.xml", "assets/chronicle.dat",
                  "assets/bin/Data/data.unity3d", "lib/arm64-v8a/libil2cpp.so",
                  "lib/arm64-v8a/libChronicleNUtils.so"}
        for name in archive.namelist():
            if name.startswith("assets/bin/Data/") and not name.endswith("/"):
                wanted.add(name)
            if name.startswith("assets/") and name.endswith((".json", ".xml", ".txt", ".config")):
                wanted.add(name)
        extracted = []
        for name in sorted(wanted):
            if name not in archive.namelist():
                continue
            data = archive.read(name)
            dest = args.work / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)
            extracted.append({"apk_entry": name, "work_path": dest.as_posix(),
                              "size": len(data), "sha256": digest(data),
                              "head_hex": data[:32].hex()})
    summary = {"apk": str(args.apk), "size": args.apk.stat().st_size,
               "sha256": digest(args.apk.read_bytes()), "identity": identity,
               "entry_count": len(entries),
               "abi": sorted({e["path"].split("/")[1] for e in entries if e["path"].startswith("lib/")}),
               "top_level": dict(Counter(e["path"].split("/")[0] for e in entries)),
               "extracted": extracted}
    (args.output / "baseline.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k != "extracted"}, ensure_ascii=False, indent=2))
    print(f"Extracted {len(extracted)} files; original APK opened read-only.")


if __name__ == "__main__":
    main()
