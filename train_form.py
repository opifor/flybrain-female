"""Fit female cell-type gains against the offline form handoff."""
import argparse
from contextlib import redirect_stdout
import io
from pathlib import Path
from time import perf_counter
from unittest.mock import patch

import numpy as np
from PIL import Image

from flyeye import FlyPilot
from flysim import FlyBrain
from form_episode import ROOT, evaluate, load_form
import measure


def tunable_codes(fb, pilot):
    motor = np.unique(np.concatenate(list(pilot.motor.values())))
    inputs = fb.W[motor, :].copy()
    inputs.data = np.maximum(inputs.data, 0)
    weights = np.bincount(fb.type_code, weights=np.asarray(inputs.sum(axis=0)).ravel(),
                          minlength=fb.n_types)
    positive = np.flatnonzero(weights > 0)
    top = positive[np.argsort(-weights[positive], kind="stable")[:40]]
    names = set(fb.type_names[top]) | set(fb.types[motor]) | {"L1", "L2"}
    return np.flatnonzero(np.isin(fb.type_names, list(names))).astype(np.int64)


def roaming_safe(fb, gains):
    paths = sorted((ROOT / "data/frames").glob("*.jpg"))
    if len(paths) != 8:
        raise ValueError("Expected eight real frames")
    frames = []
    for path in paths:
        with Image.open(path) as source:
            frames.append(np.asarray(source.convert("L"), dtype=np.float32) / 255.0)
    output = io.StringIO()
    # Run the existing measurement before making the candidate discoverable on disk.
    with patch.object(measure, "load_gains", return_value=(gains, "candidate")), redirect_stdout(output):
        measure.measure(fb, frames, 60, (0, 1))
    print(output.getvalue(), end="", flush=True)
    lines = output.getvalue().splitlines()
    values = lines[3].split()
    white = [int(line.split("firing=")[1].split()[0]) for line in lines if line.startswith("White seed=")]
    return float(values[3]) <= 0.15 and float(values[4]) >= 0.40 and len(white) == 2 and max(white) < 3000


def main():
    start = perf_counter()
    ap = argparse.ArgumentParser()
    ap.add_argument("--graph", type=Path, required=True)
    ap.add_argument("--evals", type=int, default=300)
    ap.add_argument("--minutes", type=float, default=25)
    args = ap.parse_args()
    if args.evals < 1 or not np.isfinite(args.minutes) or args.minutes <= 0:
        ap.error("evals and minutes must be positive")
    deadline = start + 60 * args.minutes
    out = ROOT / "assets/gains_female.npz"
    if out.exists():
        raise SystemExit("Output already exists; preserve it and use a clean worktree")
    fb = FlyBrain(args.graph)
    pilot = FlyPilot(fb, sim_steps=60)
    img, boxes = load_form()
    codes = tunable_codes(fb, pilot)
    gains = np.ones(fb.n_types, dtype=np.float32)
    before = {split: evaluate(fb, pilot, img, boxes, None, seeds)
              for split, seeds in (("train", range(4)), ("held-out", range(4, 8)))}
    best = before["train"]
    theta = np.zeros(len(codes), dtype=np.float32)
    sigma, last_eval = 0.5, 0
    rng = np.random.default_rng(0)
    # Leave time for held-out episodes and the existing roaming measurement.
    reserve = max(30.0, (perf_counter() - start) * 2)
    print(f"Tunable types: {len(codes)}; train seeds: 0-3; held-out seeds: 4-7", flush=True)
    for ev in range(1, args.evals + 1):
        if perf_counter() >= deadline - reserve:
            break
        proposal = theta.copy()
        subset = rng.choice(len(codes), max(1, int(np.ceil(len(codes) * 0.30))), replace=False)
        proposal[subset] += rng.normal(0, sigma, len(subset)).astype(np.float32)
        np.clip(proposal, -2, 2, out=proposal)
        gains[codes] = np.exp(proposal)
        candidate = evaluate(fb, pilot, img, boxes, gains, range(4), deadline=deadline - reserve)
        if candidate is None:
            break
        last_eval = ev
        accepted = candidate["objective"] <= best["objective"]
        if accepted:
            theta, best = proposal, candidate
        sigma = max(0.05, sigma * (1.1 if accepted else 0.97))
        if ev % 20 == 0:
            print(f"eval={ev} best={best['objective']:.6f} fields={best['fields']:.3f} "
                  f"sigma={sigma:.6f} elapsed={perf_counter() - start:.1f}s", flush=True)
    gains[codes] = np.exp(theta)
    held = evaluate(fb, pilot, img, boxes, gains, range(4, 8))
    print(f"eval={last_eval} best={best['objective']:.6f} held-out={held['objective']:.6f} "
          f"sigma={sigma:.6f} elapsed={perf_counter() - start:.1f}s", flush=True)
    print("split before_fields after_fields before_min_distance after_min_distance", flush=True)
    for split, after in (("train", best), ("held-out", held)):
        prior = before[split]
        print(f"{split} {prior['fields']:.3f} {after['fields']:.3f} "
              f"{prior['distance']:.3f} {after['distance']:.3f}", flush=True)
    if held["fields"] <= before["held-out"]["fields"]:
        print("Not written: held-out mean fields filled did not improve.", flush=True)
    elif not roaming_safe(fb, gains):
        print("Not written: candidate gains break roaming thresholds.", flush=True)
    else:
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("wb") as target:
            np.savez(target, codes=codes, theta=theta, type_names=fb.type_names[codes],
                     graph=args.graph.stem)
        print("Written: assets/gains_female.npz", flush=True)
    print(f"Total elapsed={perf_counter() - start:.1f}s", flush=True)


if __name__ == "__main__":
    main()
