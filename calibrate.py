import argparse
from pathlib import Path

import numpy as np
from PIL import Image

from flyeye import FlyPilot
from flysim import FlyBrain, load_gains

ROOT = Path(__file__).parent
SCALES = (20, 30, 45, 60, 90, 120, 180)


def sweep(path, frames, steps, seed, trained=False):
    fb = FlyBrain(path)
    pilot = FlyPilot(fb, sim_steps=steps)
    gains, tag = load_gains(fb)
    print(f"Graph: {path.name}; gains: {tag}", flush=True)
    print("max_hz DNa02_mean DNa02_max ceiling_frac dx_nonzero mean_abs_dx fwd_mean back_mean",
          flush=True)
    rows = []
    for scale in SCALES:
        pilot.eye.max_hz = scale
        samples = []
        for img in frames:
            height, width = img.shape
            for cx in (width / 2, width / 3, 2 * width / 3):
                dx, _, _, hz = pilot.step(img, cx, height / 2, gains=gains, seed=seed)
                samples.append(dict(hz, dx=float(dx)))
        steer = np.array([[s["steer_L"], s["steer_R"]] for s in samples])
        dx = np.array([s["dx"] for s in samples])
        ceiling = float(np.mean(np.any(steer >= 400.0, axis=1)))
        moving = float(np.mean(dx != 0))
        fwd = np.mean([(s["fwd_L"] + s["fwd_R"]) / 2 for s in samples])
        back = np.mean([s["back"] for s in samples])
        print(f"{scale:6d} {steer.mean():10.3f} {steer.max():9.3f} "
              f"{ceiling:12.3f} {moving:10.3f} {np.abs(dx).mean():11.3f} "
              f"{fwd:8.3f} {back:9.3f}", flush=True)
        rows.append((scale, ceiling, moving))
    eligible = [scale for scale, ceiling, moving in rows if ceiling <= 0.10 and moving >= 0.40]
    recommended = max(eligible) if eligible else None
    if recommended is None:
        best = min(rows, key=lambda row: (row[1], -row[2], -row[0]))
        print(f"Recommendation ({path.name}): none qualifies; best by ceiling fraction: "
              f"max_hz={best[0]}, ceiling_frac={best[1]:.3f}, dx_nonzero={best[2]:.3f}",
              flush=True)
    else:
        print(f"Recommendation ({path.name}): max_hz={recommended}", flush=True)
    return recommended


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--graph", type=Path, required=True)
    ap.add_argument("--frames", type=Path, default=ROOT / "data" / "frames")
    ap.add_argument("--steps", type=int, default=60)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    if args.steps < 1 or args.seed < 0:
        ap.error("--steps must be positive and --seed must be nonnegative")
    male = ROOT / "build" / "graph.npz"
    if args.write and args.graph.samefile(male):
        ap.error("--write is disabled for the male graph")
    paths = sorted(args.frames.glob("*.jpg"))
    if not paths:
        ap.error(f"no JPEG frames found in {args.frames}")
    frames = []
    for path in paths:
        with Image.open(path) as source:
            frames.append(np.asarray(source.convert("L"), dtype=np.float32) / 255.0)
    print(f"Frames: {len(frames)}; positions per frame: 3; steps: {args.steps}; seed: {args.seed}",
          flush=True)
    recommended = sweep(args.graph, frames, args.steps, args.seed)
    sweep(male, frames, args.steps, args.seed, trained=True)
    if args.write:
        if recommended is None:
            print("Not written: no recommended drive scale.")
        else:
            with np.load(args.graph, allow_pickle=False) as z:
                payload = {key: z[key] for key in z.files}
            payload["drive_hz"] = np.asarray(recommended, dtype=np.float64)
            with args.graph.open("wb") as target:
                np.savez(target, **payload)
            print(f"Stored drive_hz={float(recommended)} in {args.graph}")


if __name__ == "__main__":
    main()
