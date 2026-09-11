"""Measure visual motor responses on real frames and a white screen."""
import argparse
from pathlib import Path

import numpy as np
from PIL import Image

from flyeye import FlyPilot
from flysim import FlyBrain, load_gains

ROOT = Path(__file__).parent


def measure(fb, frames, steps, seeds, click_hz=None):
    pilot = FlyPilot(fb, sim_steps=steps)
    if click_hz is not None:
        pilot.click_hz = click_hz
    gains, tag = load_gains(fb)
    samples = []
    for img in frames:
        height, width = img.shape
        for cx in (width / 3, width / 2, 2 * width / 3):
            for seed in seeds:
                dx, _, click, hz = pilot.step(img, cx, height / 2, gains=gains, seed=seed)
                samples.append(dict(hz, dx=float(dx), flag=bool(click)))
    steer = np.array([[s["steer_L"], s["steer_R"]] for s in samples])
    stop = np.array([s["stop"] for s in samples])
    print(f"Graph: {fb.graph_path.name}; gains: {tag}; steps: {steps}; seeds: {seeds}", flush=True)
    print(f"Frames: {len(frames)}; positions: 3; samples: {len(samples)}", flush=True)
    print("exc_scale click_hz DNa02_mean ceiling_frac dx_nonzero DNa01_L DNa01_R DNp09_mean DNp09_max click_frac", flush=True)
    print(f"{fb.exc_scale:.2f} {pilot.click_hz:g} {steer.mean():.3f} "
          f"{np.any(steer >= 400, axis=1).mean():.6f} "
          f"{np.mean([s['dx'] != 0 for s in samples]):.6f} "
          f"{np.mean([s['fwd_L'] for s in samples]):.3f} "
          f"{np.mean([s['fwd_R'] for s in samples]):.3f} "
          f"{stop.mean():.3f} {stop.max():.3f} "
          f"{np.mean([s['flag'] for s in samples]):.6f}", flush=True)
    white = np.ones((480, 640), dtype=np.float32)
    for seed in seeds:
        _, _, _, hz, info = pilot.step(white, 320, 240, gains=gains, seed=seed, detail=True)
        rates = " ".join(f"{key}={value:.3f}" for key, value in hz.items())
        print(f"White seed={seed} firing={info['firing']} DN_Hz {rates}", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--graph", type=Path, required=True)
    ap.add_argument("--frames", type=Path, default=ROOT / "data" / "frames")
    ap.add_argument("--steps", type=int, default=60)
    ap.add_argument("--seeds", type=int, nargs=2, default=(0, 1))
    ap.add_argument("--exc-scale", type=float, nargs="+")
    ap.add_argument("--click-hz", type=float, nargs="+")
    args = ap.parse_args()
    if args.steps < 1 or min(args.seeds) < 0:
        ap.error("--steps must be positive and seeds must be nonnegative")
    paths = sorted(args.frames.glob("*.jpg"))
    if len(paths) != 8:
        ap.error(f"expected 8 JPEG frames in {args.frames}, found {len(paths)}")
    frames = []
    for path in paths:
        with Image.open(path) as source:
            frames.append(np.asarray(source.convert("L"), dtype=np.float32) / 255.0)
    fb = FlyBrain(args.graph)
    positive = fb.W.data > 0
    for scale in args.exc_scale or (fb.exc_scale,):
        # Start from the unscaled graph weights to avoid accumulated rounding.
        fb.wdata[positive] = fb.W.data[positive] * scale
        fb.exc_scale = scale
        for click_hz in args.click_hz or (fb.click_hz,):
            measure(fb, frames, args.steps, args.seeds, click_hz)


if __name__ == "__main__":
    main()
