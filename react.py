"""Leave sugar or shock for the track playing now."""
import argparse
import json
from pathlib import Path
import time
from envcfg import load_env


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("kind", choices=("sugar", "shock"))
    parser.add_argument("--who", choices=("operator", "listener", "chat"), default="operator")
    args = parser.parse_args()
    folder = Path(load_env().get("FLY_STATE_DIR", "state")) / "musicroom"
    playing = json.loads((folder / "public" / "public.json").read_text(encoding="utf-8")).get("now_playing")
    if not playing or not playing["started_at"] <= time.time() < playing["started_at"] + playing["duration"]:
        parser.exit(1, "nothing is playing\n")
    with (folder / "reactions.jsonl").open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps({"at": time.time(), "track_id": playing["track_id"], "kind": args.kind, "who": args.who}) + "\n")


if __name__ == "__main__":
    main()
