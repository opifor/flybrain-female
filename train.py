import argparse
from pathlib import Path
from time import perf_counter

import numpy as np
from PIL import Image

from flyeye import FlyPilot
from flysim import BUILD, FlyBrain, load_gains


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
            asym = float(np.sum(window * (np.arange(300) - 149.5))
                         / max(float(window.sum()), 1e-9) / 150)
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


def evaluate_roam(pilot, data, gains, seed, deadline=float("inf")):
    rates, moves, signs, speeds, clicks = [], [], [], [], []
    for img, cx, cy, asym in data:
        if perf_counter() >= deadline:
            return None
        dx, dy, click, hz = pilot.step(img, cx, cy, gains=gains, seed=seed)
        rates.append([hz[k] for k in pilot.motor])
        moves.append(dx)
        speeds.append(-dy / 90.0)
        clicks.append(click)
        if abs(asym) > 0.005:
            signs.append(float(np.sign(dx) == np.sign(asym)))
    rate, dx, speed = np.array(rates), np.array(moves), np.array(speeds)
    if not np.isfinite(rate).all():
        raise ValueError("Motor rates must be finite")
    right = np.mean(dx > 0)
    positive, negative = np.mean(speed > 0.15), np.mean(speed < -0.15)
    click = np.mean(clicks)
    ceiling = np.mean(np.any(rate[:, :2] >= 400, axis=1))
    loss = (12 * max(0, ceiling - 0.08) + 10 * max(0, 0.38 - right)
            + 10 * max(0, right - 0.62) + 12 * max(0, 0.28 - positive)
            + 12 * max(0, 0.18 - negative) + 4 * max(0, 0.10 - click)
            + 4 * max(0, click - 0.35) + (1 - np.mean(signs) if signs else 0)
            + 0.2 * np.mean(np.maximum(0, rate[:, :2] - 300) / 100))
    return dict(objective=float(loss), rates=rate, moving=float(np.mean(dx != 0)),
                accuracy=float(np.mean(signs)) if signs else float("nan"),
                sign_samples=len(signs), right=float(right), positive=float(positive),
                negative=float(negative), ceiling=float(ceiling), clicks=float(click))


def report(groups, before, after, roam=False):
    print("split    group       before_hz before_ceiling after_hz after_ceiling", flush=True)
    for split in ("train", "held-out"):
        a, b = before[split], after[split]
        label = "check" if roam and split == "held-out" else split
        for i, group in enumerate(groups):
            ar, br = a["rates"][:, i], b["rates"][:, i]
            print(f"{label:8s} {group:8s} {ar.mean():11.3f} {np.mean(ar >= 400):14.3f} "
                  f"{br.mean():8.3f} {np.mean(br >= 400):13.3f}", flush=True)
        print(f"{label} objective {a['objective']:.6f} {b['objective']:.6f}", flush=True)
        print(f"{label} dx_nonzero {a['moving']:.3f} {b['moving']:.3f}", flush=True)
        print(f"{label} steering_sign_accuracy {a['accuracy']:.3f} {b['accuracy']:.3f} "
              f"(n={a['sign_samples']})", flush=True)


def main():
    start = perf_counter()
    ap = argparse.ArgumentParser()
    ap.add_argument("--graph", type=Path, required=True)
    ap.add_argument("--frames", type=Path, default=Path("data/frames"))
    ap.add_argument("--steps", type=int, default=60)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--evals", type=int)
    ap.add_argument("--minutes", type=float, default=20)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--roam", action="store_true")
    ap.add_argument("--drive-hz", type=float)
    ap.add_argument("--back-scale", type=float, default=1.0)
    args = ap.parse_args()
    if args.evals is None:
        args.evals = 300 if args.roam else 600
    if args.out is None:
        args.out = Path("assets/gains_female_roam.npz" if args.roam else "assets/gains_female.npz")
    if args.roam and (args.evals > 300 or args.minutes > 25):
        ap.error("roaming training is limited to 300 evaluations and 25 minutes")
    if (args.steps < 1 or args.evals < 1 or args.seed < 0
            or not np.isfinite(args.minutes) or args.minutes <= 0):
        ap.error("steps, evals and minutes must be positive; seed must be nonnegative")
    deadline = start + args.minutes * 60
    fb = FlyBrain(args.graph)
    fb.back_scale = args.back_scale
    if args.drive_hz is not None:
        fb.drive_hz = args.drive_hz
    pilot = FlyPilot(fb, sim_steps=args.steps)
    if args.roam:
        pilot.eye.adapt = True
    codes = tunable_codes(fb, pilot)
    scorer = evaluate_roam if args.roam else evaluate
    if args.roam:
        initial, _ = load_gains(fb)
        motor = np.unique(np.concatenate(list(pilot.motor.values())))
        weight = np.bincount(fb.type_code,
                            weights=np.asarray(abs(fb.W[motor, :]).sum(axis=0)).ravel(),
                            minlength=fb.n_types)
        fixed = np.flatnonzero(initial != 1) if initial is not None else np.array([], dtype=int)
        ranked = codes[np.argsort(-weight[codes], kind="stable")]
        codes = np.array(list(dict.fromkeys([*fixed, *ranked]))[:120], dtype=np.int64)
    print(f"Tunable types: {len(codes)}; steps: {args.steps}; seed: {args.seed}", flush=True)
    data = {"train": samples(args.frames, range(1, 7)),
            "held-out": samples(args.frames, range(7, 9))}
    if args.roam:
        data["train"] = samples(args.frames, range(1, 9))
    print(f"Samples: train={len(data['train'])}; check={len(data['held-out'])}; ceiling >= 400 Hz",
          flush=True)
    gains = np.ones(fb.n_types, dtype=np.float32)
    if args.roam and initial is not None:
        gains = initial.copy()
    before = {key: scorer(pilot, value, gains, args.seed) for key, value in data.items()}
    best = before["train"]
    held = before["held-out"]
    check_label = "check" if args.roam else "held-out"
    theta = np.log(gains[codes])
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
        candidate = scorer(pilot, data["train"], gains, args.seed, deadline - reserve)
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
            held = scorer(pilot, data["held-out"], gains, args.seed)
            print(f"eval={ev} best={best['objective']:.6f} {check_label}={held['objective']:.6f} "
                  f"sigma={sigma:.6f} elapsed={perf_counter() - start:.1f}s", flush=True)
            if args.roam:
                print({k: v for k, v in best.items() if k != "rates"}, flush=True)
    gains[codes] = np.exp(theta)
    held = scorer(pilot, data["held-out"], gains, args.seed)
    print(f"eval={last_eval} best={best['objective']:.6f} {check_label}={held['objective']:.6f} "
          f"sigma={sigma:.6f} elapsed={perf_counter() - start:.1f}s", flush=True)
    report(pilot.motor, before, {"train": best, "held-out": held}, args.roam)
    if best["objective"] < before["train"]["objective"]:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        with args.out.open("wb") as target:
            settings = dict(adapt=np.bool_(pilot.eye.adapt),
                            back_scale=np.float32(pilot.back_scale),
                            drive_hz=np.float32(pilot.eye.max_hz),
                            click_hz=np.float32(pilot.click_hz)) if args.roam else {}
            np.savez(target, codes=codes, theta=theta.astype(np.float32),
                     type_names=fb.type_names[codes].astype(str), graph=args.graph.stem,
                     **settings)
        print(f"Written: {args.out}", flush=True)
    else:
        print("Not written: training objective did not improve.", flush=True)


if __name__ == "__main__":
    main()
