import argparse
from pathlib import Path
from time import perf_counter

import numpy as np
from PIL import Image

from flysim import FlyBrain, load_gains
from flyeye import FlyPilot

ROOT = Path(__file__).parent


def compare_graph(path, img, steps, seed, trained_types=None):
    fb = FlyBrain(path)
    if trained_types is None:
        trained_types = fb.type_names.copy()
    pilot = FlyPilot(fb, sim_steps=steps)
    gains, tag = load_gains(fb)
    eye = pilot.eye
    rows = [("Neurons", str(fb.n)), ("Edges", str(fb.W.nnz)),
            ("L1/L2 with hex", f"{len(eye.on_idx)} / {len(eye.off_idx)}"),
            ("Gains", f"{tag}; exc x{fb.exc_scale:.2f}")]
    for name, uv in (("ON", eye.on_uv), ("OFF", eye.off_uv)):
        u, v = uv
        rows.append((f"Eye {name} columns", str(len(u))))
        rows.append((f"Eye {name} u/v bounds",
                     f"u=[{u.min():.4f}, {u.max():.4f}] "
                     f"v=[{v.min():.4f}, {v.max():.4f}]"))
    height, width = img.shape
    cx, cy = min(320.0, width - 1), min(240.0, height - 1)
    for t in range(1, 6):
        start = perf_counter()
        dx, dy, click, hz, info = pilot.step(
            img, cx, cy, gains=gains, seed=seed, detail=True)
        elapsed = perf_counter() - start
        for key, value in hz.items():
            rows.append((f"Step {t} {key} Hz", f"{value:.3f}"))
        rows.extend([
            (f"Step {t} dx/dy/click", f"{dx:.3f} / {dy:.3f} / {bool(click)}"),
            (f"Step {t} firing neurons", str(info["firing"])),
            (f"Step {t} spikes/s", f"{info['spikes_per_sec']:.3f}"),
            (f"Step {t} mean mV", f"{info['mean_mv']:.3f}"),
            (f"Step {t} wall seconds", f"{elapsed:.6f}"),
        ])
        cx = float(np.clip(cx + dx, 0, width - 1))
        cy = float(np.clip(cy + dy, 0, height - 1))
    return rows, trained_types


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--steps", type=int, default=60)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--image", type=Path)
    args = ap.parse_args()
    if args.steps < 1:
        ap.error("--steps must be positive")
    if args.image:
        with Image.open(args.image) as source:
            img = np.asarray(source.convert("L"), dtype=np.float32) / 255.0
        label = str(args.image)
    else:
        img = np.full((480, 640), 0.05, dtype=np.float32)
        img[145:215, 200:285] = 1.0
        img[270:335, 360:435] = 0.35
        label = "synthetic (background 0.05, upper-left 1.0, lower-right 0.35)"
    male, trained_types = compare_graph(
        ROOT / "build" / "graph.npz", img, args.steps, args.seed)
    female, _ = compare_graph(
        ROOT / "build" / "graph_female.npz", img, args.steps, args.seed, trained_types)
    print(f"Image: {label}; {img.shape[1]}x{img.shape[0]}")
    print(f"Simulation steps: {args.steps}; seed: {args.seed}; 5 cursor steps")
    widths = (max(len(k) for k, _ in male),
              max(len(v) for _, v in male), max(len(v) for _, v in female))
    fmt = f"{{:<{widths[0]}}} | {{:<{widths[1]}}} | {{:<{widths[2]}}}"
    print(fmt.format("Metric", "Male", "Female"))
    print("-+-".join("-" * w for w in widths))
    for (key, m), (_, f) in zip(male, female):
        print(fmt.format(key, m, f))


if __name__ == "__main__":
    main()
