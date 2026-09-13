"""Publish the paired plume records: py site/matches.py."""

import json
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "site/web/matches"
REPO = "https://github.com/opifor/flybrain-female"
UPSTREAM = "https://github.com/fruitflydev/flycoinrh"
CARDS = [
    dict(id="plume-1", title="Same plume, her brain",
         claim="Neither brain tracks the plume under the same protocol.",
         records=["plume_female_experiment.json", "plume_experiment_male_upstream.json"],
         reports=["plume_report_female.md", "plume_report_male_upstream.md"],
         picture="plume_her_vs_him.png", commits=["88b5f0b", "d770a24"]),
    *[dict(id=f"plume-{v}", title=f"Same plume, protocol v{v}",
           claim="Does the revised protocol bring out tracking in either brain?",
           records=[f"plume_v{v}_{sex}_experiment.json" for sex in ("female", "male")],
           reports=[f"plume_v{v}_report_{sex}.md" for sex in ("female", "male")],
           picture=f"plume_v{v}_her_vs_him.png") for v in (2, 3)],
]


def section(report, heading):
    return report.split(f"## {heading}\n", 1)[1].split("\n## ", 1)[0].strip()


def revision(path):
    value = subprocess.check_output(
        ["git", "log", "-1", "--format=%H", "--", path], cwd=ROOT, text=True).strip()
    if not value:
        raise ValueError(f"No published revision for {path}")
    return value


def rows(record):
    result = []
    for key, prediction in record["summary"]["predictions"].items():
        if key not in ("P1_surge", "P2_cast", "P3_upwind_progress", "P4_source_reached"):
            continue
        metrics = []
        if key == "P1_surge":
            metrics = [("", prediction["effect"], prediction["se"], 1000, "mm/s")]
        elif key == "P2_cast":
            metrics = [(name, prediction[field]["effect"], prediction[field]["se"], scale, unit)
                       for name, field, scale, unit in (("crosswind", "vy", 1000, "mm/s"),
                                                       ("spread", "heading_change_deg", 1, "deg"))]
        elif key == "P3_upwind_progress":
            metrics = [(name, value["mean"], value["se"], 1000, "mm")
                       for name, value in prediction.items() if isinstance(value, dict) and "mean" in value]
        if metrics:
            effect = "; ".join(f"{name + ': ' if name else ''}{mean * scale:+.3g} {unit}"
                               for name, mean, se, scale, unit in metrics)
            error = "; ".join(f"{name + ': ' if name else ''}{se * scale:.3g} {unit}"
                              for name, mean, se, scale, unit in metrics)
        else:
            effect = "; ".join(f"{name}: {value:.3g} fraction" for name, value in prediction.items()
                               if isinstance(value, (int, float)))
            error = "not reported"
        result.append(dict(prediction=key.replace("_", " "), statement=prediction["statement"],
                           verdict=prediction["verdict"], effect=effect, se=error))
    if len(result) != 4:
        raise ValueError("Expected all four predictions")
    return result


def publish(card):
    names = card["records"] + card["reports"] + [card["picture"]]
    missing = [name for name in names if not (ROOT / "build" / name).is_file()]
    if missing:
        print(f"Skipped {card['id']}: missing " + ", ".join(missing))
        return None
    reports = [(ROOT / "build" / name).read_text(encoding="utf-8") for name in card["reports"]]
    records = [json.loads((ROOT / "build" / name).read_text(encoding="utf-8")) for name in card["records"]]
    if any(record.get("partial", True) for record in records):
        print(f"Skipped {card['id']}: incomplete record")
        return None
    protocol = records[0]["protocol"]
    if records[1].get("protocol", "v1") != protocol:
        raise ValueError("The two brains must use the same protocol")
    brains = []
    for i, sex in enumerate(("female", "male")):
        record_path = "build/" + card["records"][i]
        report_path = "build/" + card["reports"][i]
        ref = revision(record_path)
        commit = card.get("commits", [ref, ref])[i]
        source = UPSTREAM if commit == "d770a24" else REPO
        brains.append(dict(name=sex, predictions=rows(records[i]), links=dict(
            report=f"{REPO}/blob/{revision(report_path)}/{report_path}",
            record=f"{REPO}/raw/{ref}/{record_path}", commit=f"{source}/commit/{commit}")))
    data = dict(title=card["title"], claim=card["claim"],
                date=re.search(r"Run (\d{4}-\d{2}-\d{2})", reports[0]).group(1),
                picture=f"matches/{card['id']}.png", protocol=f"Plume tracking, {protocol}",
                brains=brains, meaning=section(reports[0], "What the result means").split("\n\n")[0],
                measured=section(reports[0], "Measured versus chosen").split("\n\n"),
                links=dict(protocol=f"{REPO}/blob/{revision('plume_experiment.py')}/plume_experiment.py"))
    OUT.mkdir(parents=True, exist_ok=True)
    write_json(OUT / f"{card['id']}.json", data)
    shutil.copyfile(ROOT / "build" / card["picture"], OUT / f"{card['id']}.png")
    print(f"Wrote site/web/matches/{card['id']}.png")
    return f"matches/{card['id']}.json"


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"Wrote {path.relative_to(ROOT).as_posix()}")


if __name__ == "__main__":
    cards = [path for card in CARDS if (path := publish(card))]
    OUT.mkdir(parents=True, exist_ok=True)
    write_json(OUT / "index.json", cards)
