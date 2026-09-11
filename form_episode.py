"""Replay the form handoff on a fixed screenshot."""
import argparse
import json
from pathlib import Path
from time import perf_counter

import numpy as np
from PIL import Image

from flyeye import FlyPilot
from flysim import BUILD, FlyBrain, load_gains

ROOT = Path(__file__).resolve().parent
FIELDS = ("name", "ticker", "desc")


def load_form():
    with Image.open(ROOT / "data/form/create_dark_image.png") as source:
        img = np.asarray(source.convert("L"), dtype=np.float32) / 255.0
    boxes = json.loads((ROOT / "data/form/create_dark_image_boxes.json").read_text())
    return img, boxes


def inside(box, x, y, pad=10):
    return (box["x"] - pad <= x <= box["x"] + box["w"] + pad
            and box["y"] - pad <= y <= box["y"] + box["h"] + pad)


def run_episode(fb, pilot, img, boxes, gains, seed, steps=18, start=(640, 250)):
    cx, cy = map(float, start)
    centres = {k: (v["x"] + v["w"] / 2, v["y"] + v["h"] / 2)
               for k, v in boxes.items() if k in FIELDS}
    distance = lambda k: float(np.hypot(cx - centres[k][0], cy - centres[k][1]))
    minimum = {k: distance(k) for k in centres}
    filled = {k for k in centres if boxes[k].get("filled", False)}
    trace = []
    for t in range(steps):
        opened = [k for k in centres if k not in filled]
        if not opened:
            break
        target = min(opened, key=distance)
        dx, dy, click, hz = pilot.step(img, cx, cy, gains=gains, seed=seed + t)
        cx = float(np.clip(cx + dx, 2, 1278))
        cy = float(np.clip(cy + dy, 2, 718))
        for k in centres:
            minimum[k] = min(minimum[k], distance(k))
        hit = bool(click and inside(boxes[target], cx, cy))
        if hit:
            filled.add(target)
        trace.append(dict(t=t, seed=seed + t, cx=cx, cy=cy, dx=float(dx),
                          dy=float(dy), click=bool(click), target=target,
                          hit=hit, hz=hz, filled=sorted(filled)))
    return filled, trace, minimum


def evaluate(fb, pilot, img, boxes, gains, seeds, steps=18, deadline=float("inf")):
    episodes, losses = [], []
    for seed in seeds:
        if perf_counter() >= deadline:
            return None
        filled, trace, minimum = run_episode(fb, pilot, img, boxes, gains, seed, steps)
        opened = [minimum[k] / 400 for k in FIELDS if k not in filled]
        losses.append(3 - len(filled) + 0.5 * (float(np.mean(opened)) if opened else 0))
        episodes.append(dict(seed=seed, filled=filled, trace=trace, minimum=minimum))
    return dict(objective=float(np.mean(losses)),
                fields=float(np.mean([len(e["filled"]) for e in episodes])),
                distance=float(np.mean([list(e["minimum"].values()) for e in episodes])),
                clicks=int(sum(s["click"] for e in episodes for s in e["trace"])),
                episodes=episodes)


def print_result(label, result):
    for e in result["episodes"]:
        fields = ",".join(k for k in FIELDS if k in e["filled"]) or "none"
        print(f"{label} seed={e['seed']} filled={fields} "
              f"mean_min_distance={np.mean(list(e['minimum'].values())):.3f} "
              f"clicks={sum(s['click'] for s in e['trace'])}", flush=True)
    print(f"{label} mean_fields_filled={result['fields']:.3f} "
          f"mean_min_distance={result['distance']:.3f} clicks={result['clicks']}", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--graph", type=Path, required=True)
    ap.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2, 3])
    ap.add_argument("--steps", type=int, default=18)
    args = ap.parse_args()
    if args.steps < 1 or min(args.seeds) < 0:
        ap.error("steps must be positive and seeds nonnegative")
    img, boxes = load_form()
    fb = FlyBrain(args.graph)
    pilot = FlyPilot(fb, sim_steps=60)
    untrained = evaluate(fb, pilot, img, boxes, None, args.seeds, args.steps)
    print_result("female untrained", untrained)
    gains, tag = load_gains(fb)
    result = untrained if gains is None else evaluate(fb, pilot, img, boxes, gains, args.seeds, args.steps)
    print_result(f"female {tag}", result)
    male = FlyBrain(BUILD / "graph.npz")
    gains, tag = load_gains(male)
    reference = evaluate(male, FlyPilot(male, sim_steps=60), img, boxes, gains, args.seeds, args.steps)
    print_result(f"male reference {tag}", reference)
    if reference["fields"] < 1:
        raise SystemExit("Male reference failed: mean fields filled below 1.0")


if __name__ == "__main__":
    main()
