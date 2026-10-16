"""Parse Unity objects, preserve TextAsset bytes; never export textures/audio."""
import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

import UnityPy


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("--output", type=Path, default=Path("output/unity"))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    text_dir = args.output / "textassets"
    text_dir.mkdir(exist_ok=True)
    try:
        env = UnityPy.load(str(args.source))
        if not env.assets:
            raise ValueError("No serialized Unity asset files were loaded")
    except Exception as exc:
        error = {"source": str(args.source), "status": "LOAD_FAILED",
                 "error": f"{type(exc).__name__}: {exc}"}
        (args.output / "load_error.json").write_text(json.dumps(error, indent=2), encoding="utf-8")
        print(json.dumps(error))
        return 2
    rows, errors, texts, scripts = [], [], [], []
    for obj in env.objects:
        row = {"asset_file": obj.assets_file.name, "path_id": obj.path_id,
               "type": obj.type.name, "byte_start": obj.byte_start, "byte_size": obj.byte_size}
        try:
            row["name"] = obj.peek_name()
            if obj.type.name == "TextAsset":
                data = obj.parse_as_object()
                raw = data.m_Script.encode("utf-8", "surrogateescape")
                name = re.sub(r"[^\w.-]", "_", data.m_Name)
                dest = text_dir / f"{Path(obj.assets_file.name).name}_{obj.path_id}_{name}.bin"
                dest.write_bytes(raw)
                row.update(text_path=dest.as_posix(), text_size=len(raw),
                           text_sha256=hashlib.sha256(raw).hexdigest())
                try:
                    parsed = json.loads(raw)
                    row["json_type"] = type(parsed).__name__
                    row["json_count"] = len(parsed) if isinstance(parsed, (dict, list)) else None
                    if isinstance(parsed, dict):
                        row["json_keys"] = list(parsed)[:40]
                    dest.with_suffix(".json").write_text(json.dumps(parsed, ensure_ascii=False, indent=2), encoding="utf-8")
                except (ValueError, UnicodeError):
                    pass
                texts.append(row.copy())
            elif obj.type.name == "MonoScript":
                data = obj.parse_as_dict()
                scripts.append(dict(row, fields=data))
            elif obj.type.name in ("AssetBundle", "ResourceManager", "PlayerSettings"):
                data = obj.parse_as_dict()
                (args.output / f"{obj.type.name}_{obj.path_id}.json").write_text(
                    json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as exc:
            row["error"] = f"{type(exc).__name__}: {exc}"
            errors.append(row.copy())
        rows.append(row)
    for name, data in [("objects", rows), ("textassets", texts), ("monoscripts", scripts), ("errors", errors)]:
        with (args.output / f"{name}.jsonl").open("w", encoding="utf-8") as out:
            for item in data:
                out.write(json.dumps(item, ensure_ascii=False) + "\n")
    summary = {"source": str(args.source), "sha256": hashlib.sha256(args.source.read_bytes()).hexdigest(),
               "unitypy": UnityPy.__version__, "objects": len(rows),
               "types": dict(Counter(r["type"] for r in rows)),
               "textassets": len(texts), "monoscripts": len(scripts), "errors": len(errors),
               "serialized_files": [{"name": f.name, "unity_version": f.unity_version,
                                     "enable_type_tree": f._enable_type_tree,
                                     "externals": [str(e.path) for e in f.externals]}
                                    for f in env.assets]}
    (args.output / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k != "serialized_files"}, ensure_ascii=False, indent=2))
    print("TextAssets:", [r.get("name") for r in texts])
    return 5 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
