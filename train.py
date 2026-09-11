import argparse
from pathlib import Path
from time import perf_counter

import numpy as np
from PIL import Image

from flyeye import FlyPilot
from flysim import BUILD, FlyBrain


def tunable_codes(fb, pilot):
    with np.load(BUILD / "gains_ui.npz", allow_pickle=False) as z:
        names = set(z["type_names"].astype(str))
    motor = np.unique(np.concatenate(list(pilot.motor.values())))
    inputs = fb.W[motor, :].copy()
    inputs.data = np.maximum(inputs.data, 0)
    weight = np.bincount(fb.type_code,
                         weights=np.asarray(inputs.sum(axis=0)).ravel(),
                         minlength=fb.n_types)
    positive = np.flatnonzero(weight > 0)
    top = positive[np.argsort(-weight[positive], kind="stable")[:60]]
    names.update(fb.type_names[top])
    names.update(fb.types[motor])
    names.update(("L1", "L2"))
    return np.flatnonzero(np.isin(fb.type_names, list(names))).astype(np.int64)


def samples(frames, numbers):
    result = []
    for number in numbers:
        with Image.open(frames / f"frame{number}.jpg") as source:
            img = np.asarray(source.convert("L"), dtype=np.float32) / 255.0
        height, width = img.shape
        for cx in (width / 3, width / 2, 2 * width / 3):
            cy = height / 2
            # Match look's integer sampling and edge clamping without shrinking the view.
            x = np.clip((cx - 150 + np.arange(300)).astype(int), 0, width - 1)
            y = np.clip((cy - 105 + np.arange(210)).astype(int), 0, height - 1)
            window = img[np.ix_(y, x)]
            asym = float(window[:, 150:].mean() - window[:, :150].mean())
            result.append((img, cx, cy, asym))
    return result


def evaluate(pilot, data, gains, seed, deadline=float("inf")):
    rates, moves, signs, losses = [], [], [], []
    for img, cx, cy, asym in data:
        if perf_counter() >= deadline:
            return None
        dx, _, _, hz = pilot.step(img, cx, cy, gains=gains, seed=seed)
        rate = np.array([hz[k] for k in pilot.motor])
        if not np.isfinite(rate).all():
            raise ValueError("Motor rates must be finite")
        diff = hz["steer_R"] - hz["steer_L"]
        steer = 0.0
        if abs(asym) > 0.05:
            correct = np.sign(diff) == np.sign(asym)
            signs.append(float(correct))
            steer = 0.0 if correct else (0.5 if diff == 0 else 1.0)
        ceiling = np.sum(np.maximum(0, rate - 320) ** 2) / 100 ** 2
        band = np.sum((np.maximum(0, 80 - rate[:4]) / 80) ** 2)
        losses.append(ceiling + 2 * np.all(rate == 0) + band + 2 * steer)
        rates.append(rate)
        moves.append(dx != 0)
    return dict(objective=float(np.mean(losses)), rates=np.array(rates),
                moving=float(np.mean(moves)),
                accuracy=float(np.mean(signs)) if signs else float("nan"),
                sign_samples=len(signs))


def report(groups, before, after):
    print("split    group       before_hz before_ceiling after_hz after_ceiling", flush=True)
    for split in ("train", "held-out"):
        a, b = before[split], after[split]
        for i, group in enumerate(groups):
            ar, br = a["rates"][:, i], b["rates"][:, i]
            print(f"{split:8s} {group:8s} {ar.mean():11.3f} {np.mean(ar >= 400):14.3f} "
                  f"{br.mean():8.3f} {np.mean(br >= 400):13.3f}", flush=True)
        print(f"{split} objective {a['objective']:.6f} {b['objective']:.6f}", flush=True)
        print(f"{split} dx_nonzero {a['moving']:.3f} {b['moving']:.3f}", flush=True)
        print(f"{split} steering_sign_accuracy {a['accuracy']:.3f} {b['accuracy']:.3f} "
              f"(n={a['sign_samples']})", flush=True)


def main():
    start = perf_counter()
    ap = argparse.ArgumentParser()
    ap.add_argument("--graph", type=Path, required=True)
    ap.add_argument("--frames", type=Path, default=Path("data/frames"))
    ap.add_argument("--steps", type=int, default=60)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--evals", type=int, default=600)
    ap.add_argument("--minutes", type=float, default=20)
    ap.add_argument("--out", type=Path, default=Path("assets/gains_female.npz"))
    args = ap.parse_args()
    if (args.steps < 1 or args.evals < 1 or args.seed < 0
            or not np.isfinite(args.minutes) or args.minutes <= 0):
        ap.error("steps, evals and minutes must be positive; seed must be nonnegative")
    deadline = start + args.minutes * 60
    fb = FlyBrain(args.graph)
    pilot = FlyPilot(fb, sim_steps=args.steps)
    codes = tunable_codes(fb, pilot)
    print(f"Tunable types: {len(codes)}; steps: {args.steps}; seed: {args.seed}", flush=True)
    data = {"train": samples(args.frames, range(1, 7)),
            "held-out": samples(args.frames, range(7, 9))}
    print("Samples: train=18 (frames 1-6); held-out=6 (frames 7-8); ceiling >= 400 Hz",
          flush=True)
    gains = np.ones(fb.n_types, dtype=np.float32)
    before = {key: evaluate(pilot, value, gains, args.seed) for key, value in data.items()}
    best = before["train"]
    held = before["held-out"]
    theta = np.zeros(len(codes), dtype=np.float32)
    rng = np.random.default_rng(args.seed)
    sigma = 0.4
    # Reserve a baseline-sized evaluation window for the final held-out report.
    reserve = perf_counter() - start
    last_eval = 0
    for ev in range(1, args.evals + 1):
        if perf_counter() >= deadline - reserve:
            break
        proposal = theta.copy()
        subset = rng.choice(len(codes), max(1, int(np.ceil(len(codes) * 0.25))), replace=False)
        proposal[subset] += rng.normal(0, sigma, len(subset)).astype(np.float32)
        np.clip(proposal, -2, 2, out=proposal)
        gains[codes] = np.exp(proposal)
        candidate = evaluate(pilot, data["train"], gains, args.seed, deadline - reserve)
        if candidate is None:
            break
        last_eval = ev
        if candidate["objective"] <= best["objective"]:
            theta, best = proposal, candidate
            sigma *= 1.05
        else:
            sigma *= 0.98
        if ev % 25 == 0:
            gains[codes] = np.exp(theta)
            held = evaluate(pilot, data["held-out"], gains, args.seed)
            print(f"eval={ev} best={best['objective']:.6f} held-out={held['objective']:.6f} "
                  f"sigma={sigma:.6f} elapsed={perf_counter() - start:.1f}s", flush=True)
    gains[codes] = np.exp(theta)
    held = evaluate(pilot, data["held-out"], gains, args.seed)
    print(f"eval={last_eval} best={best['objective']:.6f} held-out={held['objective']:.6f} "
          f"sigma={sigma:.6f} elapsed={perf_counter() - start:.1f}s", flush=True)
    report(pilot.motor, before, {"train": best, "held-out": held})
    if best["objective"] < before["train"]["objective"]:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        with args.out.open("wb") as target:
            np.savez(target, codes=codes, theta=theta.astype(np.float32),
                     type_names=fb.type_names[codes].astype(str), graph=args.graph.stem)
        print(f"Written: {args.out}", flush=True)
    else:
        print("Not written: training objective did not improve.", flush=True)


if __name__ == "__main__":
    main()
