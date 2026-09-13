"""A small shelf of freely licensed music from Wikimedia Commons."""
import argparse
import json
import math
import os
from html.parser import HTMLParser
from pathlib import Path
import subprocess
import time
from urllib.parse import quote

import requests

from ear import analyse

API = "https://commons.wikimedia.org/w/api.php"
USER_AGENT = "flybrain-female/0.1 (https://femaleflybrain.com)"
CATEGORIES = ("Electronic music", "Jazz", "Piano music", "Ambient music", "Chiptune")
MIMES = {"audio/ogg": "ogg", "application/ogg": "ogg", "audio/flac": "flac",
         "audio/mpeg": "mp3", "audio/wav": "wav"}
MAX_SIZE = 40 * 1024 * 1024


class PlainText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)


def plain(value):
    parser = PlainText()
    parser.feed(value)
    return " ".join("".join(parser.parts).split())


def allowed_license(value):
    return value.startswith(("CC0", "CC BY", "CC BY-SA")) and not any(
        restriction in value.upper() for restriction in ("-NC", "-ND"))


def metadata(page, name):
    return page["imageinfo"][0].get("extmetadata", {}).get(name, {}).get("value", "")


def eligible(page):
    info = page.get("imageinfo", [{}])[0]
    return (info.get("mime") in MIMES and 0 < info.get("size", 0) <= MAX_SIZE
            and allowed_license(metadata(page, "LicenseShortName")))


def build_record(page, file, duration):
    info = page["imageinfo"][0]
    title = plain(metadata(page, "ObjectName"))
    return {"id": page["pageid"],
            "title": title or Path(page["title"].removeprefix("File:")).stem,
            "artist": plain(metadata(page, "Artist")),
            "license": metadata(page, "LicenseShortName"),
            "page": "https://commons.wikimedia.org/wiki/" + quote(page["title"]),
            "file": Path(file).as_posix(), "mime": info["mime"],
            "duration": float(duration), "ear": Path(str(file) + ".ear.npz").as_posix()}


class Commons:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers["User-Agent"] = USER_AGENT
        self.last_request = -math.inf

    def get(self, url, **kwargs):
        time.sleep(max(0, 1 - (time.monotonic() - self.last_request)))
        self.last_request = time.monotonic()
        response = self.session.get(url, timeout=30, **kwargs)
        response.raise_for_status()
        return response

    def pages(self):
        for category in CATEGORIES:
            params = {"action": "query", "format": "json", "generator": "search",
                      "gsrnamespace": 6, "gsrsearch": f'filetype:audio incategory:"{category}"',
                      "gsrlimit": 50, "prop": "imageinfo", "iiprop": "url|size|mime|extmetadata"}
            while True:
                with self.get(API, params=params) as response:
                    result = response.json()
                if "error" in result:
                    raise RuntimeError(str(result["error"]))
                yield from result.get("query", {}).get("pages", {}).values()
                if "continue" not in result:
                    break
                params.update(result["continue"])

    def download(self, url, path):
        partial = path.with_suffix(path.suffix + ".part")
        try:
            with self.get(url, stream=True) as response, partial.open("wb") as output:
                size = 0
                for chunk in response.iter_content(65536):
                    size += len(chunk)
                    if size > MAX_SIZE:
                        raise ValueError("download exceeds 40 MB")
                    output.write(chunk)
            partial.replace(path)
        finally:
            partial.unlink(missing_ok=True)


def fetch(count, directory):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    commons = Commons()
    records, seen = [], set()
    try:
        for page in commons.pages():
            if page["pageid"] in seen or not eligible(page):
                continue
            seen.add(page["pageid"])
            info = page["imageinfo"][0]
            path = directory / f'{page["pageid"]}.{MIMES[info["mime"]]}'
            try:
                if not path.exists():
                    commons.download(info["url"], path)
                probe = subprocess.run(
                    ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                     "-of", "json", str(path)], capture_output=True, text=True,
                    check=True, timeout=30)
                duration = float(json.loads(probe.stdout)["format"]["duration"])
                if not 45 <= duration <= 480:
                    continue
                analyse(path)
                relative = Path(os.path.relpath(path, Path.cwd()))
                records.append(build_record(page, relative, duration))
                print(f'{len(records):2d}  {records[-1]["title"]}', flush=True)
            except (requests.RequestException, subprocess.SubprocessError, ValueError,
                    KeyError, OSError) as error:
                print(f'Skipping {page["pageid"]}: {error}', flush=True)
            if len(records) >= count:
                break
    finally:
        commons.session.close()
        if records:
            target = directory / "catalog.json"
            temporary = target.with_suffix(".json.tmp")
            temporary.write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n",
                                 encoding="utf-8")
            temporary.replace(target)
    return records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("fetch", "list"))
    parser.add_argument("--count", type=int, default=12)
    parser.add_argument("--dir", type=Path, default=Path("data/music"))
    args = parser.parse_args()
    if args.count < 1:
        parser.error("--count must be positive")
    if args.command == "fetch":
        records = fetch(args.count, args.dir)
        print(f"Saved {len(records)} tracks to {args.dir}")
        return 0 if len(records) >= args.count else 1
    records = json.loads((args.dir / "catalog.json").read_text(encoding="utf-8"))
    print(f'{"ID":>10}  {"SECONDS":>7}  {"LICENSE":<18}  TITLE / ARTIST')
    for record in records:
        print(f'{record["id"]:>10}  {record["duration"]:7.1f}  '
              f'{record["license"]:<18}  {record["title"]} / {record["artist"]}')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
