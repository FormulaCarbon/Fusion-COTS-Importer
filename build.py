#!/usr/bin/env python3
"""Package the add-in as a Fusion 360 .bundle.

    python3 build.py

Writes dist/VendorSearch.bundle: a zip holding a VendorSearch.bundle folder
that can be unpacked into Fusion's ApplicationPlugins directory.
"""

import shutil
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ADDIN_NAME = "VendorSearch"
BUILD = ROOT / "build"
DIST = ROOT / "dist"

RUNTIME = [
    "__init__.py",
    "VendorSearch.py",
    "VendorSearch.manifest",
    "config.py",
    "vendor.py",
    "commands",
    "vendors",
    "lib",
    "AddInIcon.svg",
]

REQUIRED = ["__init__.py", f"{ADDIN_NAME}.py", f"{ADDIN_NAME}.manifest"]

SKIP_DIRS = ("__pycache__", ".git", ".vscode", ".idea")
SKIP_PREFIXES = ("lib/bin",)
SKIP_SUFFIXES = (".pyc", ".pyo", ".dist-info")
SKIP_NAMES = (".env", ".DS_Store")


def keep(rel: str) -> bool:
    """Decide whether a file, named relative to the add-in root, ships."""
    parts = Path(rel).parts
    if any(p in SKIP_DIRS for p in parts):
        return False
    if rel.startswith(SKIP_PREFIXES):
        return False
    if any(p.endswith(SKIP_SUFFIXES) for p in parts):
        return False
    return parts[-1] not in SKIP_NAMES


def stage(bundle: Path) -> int:
    """Copy the runtime files into the bundle and return the file count."""
    contents = bundle / "Contents" / ADDIN_NAME
    count = 0

    for item in RUNTIME:
        src = ROOT / item
        if not src.exists():
            print(f"  skipping missing {item}", file=sys.stderr)
            continue

        if src.is_dir():
            for path in sorted(src.rglob("*")):
                if path.is_dir():
                    continue
                rel = path.relative_to(src)
                if not keep(f"{item}/{rel.as_posix()}"):
                    continue
                dst = contents / item / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, dst)
                count += 1
        elif keep(item):
            dst = contents / item
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            count += 1

    shutil.copy2(ROOT / "PackageContents.xml", bundle / "PackageContents.xml")
    return count


def main() -> int:
    if BUILD.exists():
        shutil.rmtree(BUILD)

    bundle = BUILD / f"{ADDIN_NAME}.bundle"
    count = stage(bundle)

    for name in REQUIRED:
        if not (bundle / "Contents" / ADDIN_NAME / name).exists():
            print(f"error: {name} missing from bundle", file=sys.stderr)
            return 1

    DIST.mkdir(exist_ok=True)
    archive = DIST / f"{ADDIN_NAME}.bundle"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(bundle.rglob("*")):
            if not path.is_dir():
                zf.write(path, path.relative_to(BUILD))

    kb = archive.stat().st_size / 1024
    print(f"{archive.relative_to(ROOT)}: {count} files, {kb:.0f} KB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
