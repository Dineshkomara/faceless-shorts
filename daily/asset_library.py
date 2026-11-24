#!/usr/bin/env python3
"""Small local library for reusable faceless-shorts props, scene kits and utilities."""
import argparse
import hashlib
import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LIBRARY = ROOT / "asset-library"
INDEX = LIBRARY / "index.json"
ALLOWED = {".js", ".mjs", ".json", ".svg", ".png", ".jpg", ".webp", ".glb", ".gltf", ".obj", ".mtl", ".wav", ".mp3"}
MAX_FILE = 80 * 1024 * 1024


def read_index():
    LIBRARY.mkdir(parents=True, exist_ok=True)
    if not INDEX.exists():
        INDEX.write_text(json.dumps({"schema_version": 1, "assets": []}, indent=2) + "\n")
    return json.loads(INDEX.read_text())


def save_index(data):
    tmp = INDEX.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    tmp.replace(INDEX)


def under(root, path):
    root = root.resolve()
    path = path.resolve()
    if path != root and root not in path.parents:
        raise ValueError(f"Path must stay inside {root}: {path}")
    return path


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def search(args):
    data = read_index()
    terms = set(re.findall(r"[a-z0-9]+", args.query.lower()))
    matches = []
    for asset in data["assets"]:
        hay = " ".join([asset.get("id", ""), asset.get("description", ""), *asset.get("tags", [])]).lower()
        hits = terms & set(re.findall(r"[a-z0-9]+", hay))
        if not terms or hits:
            matches.append((len(hits), asset))
    matches.sort(key=lambda item: (-item[0], item[1].get("id", "")))
    if not matches:
        print("No matching reusable asset. Create a focused, clean asset and archive it after QA.")
        return
    for score, asset in matches:
        print(f"{asset['id']}  [{', '.join(asset.get('tags', []))}]")
        print(f"  {asset.get('description', '')}")
        print(f"  files: {', '.join(asset.get('files', []))}")
        if asset.get("preview"):
            print(f"  preview: {asset['preview']}")
        if asset.get("integration_notes"):
            print(f"  use: {asset['integration_notes']}")


def archive(args):
    project = under(ROOT, Path(args.project))
    asset_id = re.sub(r"[^a-z0-9-]+", "-", args.id.lower()).strip("-")
    if not asset_id:
        raise ValueError("Asset ID must contain letters or numbers")
    data = read_index()
    if any(a.get("id") == asset_id for a in data["assets"]):
        raise ValueError(f"Asset already exists: {asset_id}; use a new versioned ID instead of overwriting")
    item_dir = LIBRARY / "items" / asset_id
    item_dir.mkdir(parents=True, exist_ok=False)
    files = []
    for rel in args.file:
        source = under(project, project / rel)
        if not source.is_file() or source.is_symlink():
            raise ValueError(f"Not a regular file within project: {rel}")
        if source.suffix.lower() not in ALLOWED:
            raise ValueError(f"Unsupported asset type: {source.suffix}")
        if source.stat().st_size > MAX_FILE:
            raise ValueError(f"Asset file exceeds {MAX_FILE // (1024*1024)} MB: {rel}")
        target = item_dir / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        files.append({"path": rel, "sha256": digest(target), "bytes": target.stat().st_size})
    if not files:
        shutil.rmtree(item_dir)
        raise ValueError("Provide at least one --file")
    preview = None
    if args.preview:
        source = under(project, project / args.preview)
        if not source.is_file() or source.suffix.lower() not in {".png", ".jpg", ".webp"}:
            raise ValueError("Preview must be a PNG, JPG, or WebP file inside the project")
        preview = "preview" + source.suffix.lower()
        shutil.copy2(source, item_dir / preview)
    entry = {
        "id": asset_id,
        "description": args.description,
        "category": args.category,
        "tags": sorted(set(t.strip().lower() for t in args.tag if t.strip())),
        "source_project": project.name,
        "source_paths": [f["path"] for f in files],
        "files": [f["path"] for f in files],
        "checksums": {f["path"]: f["sha256"] for f in files},
        "sizes": {f["path"]: f["bytes"] for f in files},
        "preview": str((item_dir / preview).relative_to(LIBRARY)) if preview else None,
        "integration_notes": args.integration_notes,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    (item_dir / "asset.json").write_text(json.dumps(entry, indent=2, ensure_ascii=False) + "\n")
    data["assets"].append(entry)
    save_index(data)
    print(f"Archived {asset_id} ({len(files)} files) to {item_dir}")


def use(args):
    project = under(ROOT, Path(args.project))
    data = read_index()
    asset = next((a for a in data["assets"] if a.get("id") == args.id), None)
    if asset is None:
        raise ValueError(f"Unknown asset ID: {args.id}")
    source_dir = LIBRARY / "items" / args.id
    installed = []
    skipped = []
    for rel in asset["files"]:
        source = under(source_dir, source_dir / rel)
        target = under(project, project / rel)
        if not source.is_file() or digest(source) != asset.get("checksums", {}).get(rel):
            raise ValueError(f"Library file is missing or has changed: {args.id}/{rel}")
        if target.exists():
            if target.is_file() and digest(target) == asset["checksums"][rel]:
                skipped.append(rel)
                continue
            raise ValueError(f"Conflict at {rel}; refusing to overwrite project files")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        installed.append(rel)
    manifest_path = project / ".asset-library.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {"schema_version": 1, "assets": []}
    if not any(a.get("id") == args.id for a in manifest["assets"]):
        manifest["assets"].append({"id": args.id, "installed": installed, "already_present": skipped,
                                   "used_at": datetime.now(timezone.utc).isoformat(timespec="seconds")})
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Used {args.id}: installed {len(installed)}, already identical {len(skipped)}; no files overwritten")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)
    s = sub.add_parser("search", help="Search the reusable asset registry")
    s.add_argument("query", nargs="?", default="")
    s.set_defaults(func=search)
    a = sub.add_parser("archive", help="Archive reusable files from a finished project")
    a.add_argument("--project", required=True)
    a.add_argument("--id", required=True)
    a.add_argument("--description", required=True)
    a.add_argument("--category", default="procedural")
    a.add_argument("--tag", action="append", default=[])
    a.add_argument("--file", action="append", default=[])
    a.add_argument("--preview")
    a.add_argument("--integration-notes", default="Inspect dependencies and phone-size appearance; reuse only if it makes the current concept clearer.")
    a.set_defaults(func=archive)
    u = sub.add_parser("use", help="Copy a library bundle into a project without overwriting files")
    u.add_argument("--project", required=True)
    u.add_argument("--id", required=True)
    u.set_defaults(func=use)
    args = p.parse_args()
    try:
        args.func(args)
    except Exception as e:
        print(f"asset-library: {e}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
