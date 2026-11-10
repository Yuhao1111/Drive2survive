#!/usr/bin/env python3
"""Build a small GitHub Pages site with every MP4 video still playable inline.

The main branch retains all original data. _site/ is generated, never committed.
"""
from pathlib import Path
import shutil
import json

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "_site"
ROOT_FILES = [
    "index.html", "videos.html", "index_original.html",
    "research.css", "research.js", "README_CN_EN.md",
    "CAMERA_PLAYBACK_UPDATE_CN_EN.md", "source_register.csv",
    "validation.json",
]
OTHER_DIRS = ["figures", "reports", "source", "validation", "cameras"]
MEDIA_SUFFIXES = {".mp4", ".jpg", ".jpeg", ".png", ".csv", ".json"}

def copy(rel):
    src = ROOT / rel
    if not src.is_file():
        raise FileNotFoundError(f"Required website file missing: {rel}")
    dst = DEST / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)

def main():
    if DEST.exists():
        shutil.rmtree(DEST)
    DEST.mkdir(parents=True)
    for filename in ROOT_FILES:
        copy(Path(filename))
    for name in OTHER_DIRS:
        directory = ROOT / name
        if directory.exists():
            shutil.copytree(directory, DEST / name)

    for item in (ROOT / "data").iterdir():
        if item.is_file() and item.name != "panels.json":
            copy(item.relative_to(ROOT))

    mp4 = jpg = 0
    for item in (ROOT / "media").rglob("*"):
        if item.is_file() and item.suffix.lower() in MEDIA_SUFFIXES:
            copy(item.relative_to(ROOT))
            if item.suffix.lower() == ".mp4":
                mp4 += 1
            if item.suffix.lower() in {".jpg", ".jpeg"}:
                jpg += 1

    if mp4 < 48 or jpg < 38:
        raise RuntimeError(f"Media incomplete: MP4={mp4}, JPG={jpg}")

    # GIF files duplicate MP4s and account for >200MB. Link to MP4 instead.
    js = DEST / "research.js"
    text = js.read_text(encoding="utf-8")
    text = text.replace('href="${c.gif}">GIF', 'href="${c.mp4}">MP4')
    text = text.replace(
        'href="${raw.result_path}">Saved result',
        'href="https://raw.githubusercontent.com/Yuhao1111/Drive2survive/main/${raw.result_path}">Saved result',
    )
    js.write_text(text, encoding="utf-8")

    alt = DEST / "videos.html"
    text = alt.read_text(encoding="utf-8")
    text = text.replace("/execution.gif", "/execution.mp4")
    text = text.replace("GIF", "MP4")
    alt.write_text(text, encoding="utf-8")

    (DEST / ".nojekyll").touch()
    files = [p for p in DEST.rglob("*") if p.is_file()]
    size = sum(p.stat().st_size for p in files)
    manifest = {
        "published_mp4": mp4,
        "published_jpg": jpg,
        "published_files": len(files),
        "published_bytes": size,
        "excluded": ["media/**/*.gif", "camera_playback/", "data/maps/", "data/runs/", "data/panels.json"],
        "note": "Original source data and GIFs are kept intact on the main branch.",
    }
    (DEST / "PAGES_BUILD_MANIFEST.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    if size > 300_000_000:
        raise RuntimeError(f"Pages package too large: {size / 1e6:.1f} MB")

if __name__ == "__main__":
    main()
