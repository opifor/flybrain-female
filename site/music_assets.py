"""Put the music and its credits beside the stream page."""
import argparse
import json
from pathlib import Path
import re
import subprocess


ROOT = Path(__file__).resolve().parents[1]
CATALOGUE = ROOT / "data/music/catalog.json"
OUTPUT = ROOT / "site/web/music"
LIMIT = 8_000_000


def build(catalogue=CATALOGUE, output=OUTPUT):
    catalogue, output = Path(catalogue).resolve(), Path(output)
    rows = json.loads(catalogue.read_text(encoding="utf-8"))
    output.mkdir(parents=True, exist_ok=True)
    credits, ids = [], set()
    for row in rows:
        track_id = str(row["id"])
        if not re.fullmatch(r"[A-Za-z0-9_-]+", track_id) or track_id in ids:
            raise ValueError("track ids must be unique, plain filename stems")
        ids.add(track_id)
        credit = {key: row[key] for key in ("title", "artist", "license", "page", "duration")}
        source = Path(row["file"])
        if not source.is_absolute():
            # Catalogue paths are rooted in the checkout that holds the recordings.
            source = catalogue.parent.parent.parent / source
        target = output / f"{track_id}.ogg"
        if not target.exists():
            pending = output / f"{track_id}.tmp.ogg"
            try:
                subprocess.run(["ffmpeg", "-nostdin", "-y", "-v", "error", "-i", str(source),
                                "-vn", "-c:a", "libvorbis", "-q:a", "3", str(pending)], check=True)
                if not 0 < pending.stat().st_size <= LIMIT:
                    raise ValueError(f"{track_id} exceeds the 8 MB music budget")
                pending.replace(target)
            finally:
                pending.unlink(missing_ok=True)
        if not 0 < target.stat().st_size <= LIMIT:
            raise ValueError(f"{track_id} exceeds the 8 MB music budget")
        credits.append(dict(id=track_id, **credit, file=target.name))
        print(f"{target.name}: {target.stat().st_size} bytes")
    pending = output / "catalog.tmp"
    pending.write_text(json.dumps(credits, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    pending.replace(output / "catalog.json")
    print(f"{len(credits)} tracks ready")
    return credits


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["build"])
    parser.add_argument("--catalogue", type=Path, default=CATALOGUE)
    args = parser.parse_args()
    build(args.catalogue)
