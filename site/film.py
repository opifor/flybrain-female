"""Frame sequence for the scroll film at the top of the landing page.

    python site/film.py build <dir>    scene0.mp4 .. scene6.mp4 in <dir>, in order
    python site/film.py placeholder    a synthetic stand-in until the clips exist

Both write site/web/film/f0001.webp .. fNNNN.webp at 1920x1080, 12 fps, and a
manifest.json with the frame range of each scene. The page scrubs the frames
with scroll position, so the film is stored as still images rather than video:
a browser cannot seek a video element frame by frame fast enough to follow a
scroll wheel, but it can draw a decoded image in one paint.

Needs ffmpeg and ffprobe on PATH. The placeholder also needs Pillow.
"""

import json
import math
import random
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "web" / "film"
W, H, FPS = 1920, 1080, 12
MW, MH = 854, 480
SCENES = 7

# Overlay text per scene. The page owns the markup; this copy goes into the
# manifest so the frames and the words travel together.
TEXT = [
    "FEMALE FLYBRAIN / sister build of FLYBRAIN. same experiment, the other sex.",
    "Blind at first. On a white screen 19,215 neurons fired at once.",
    "Relabelled by cell type. 22,889 labels changed; the noise fell to 691.",
    "Both eyes. 783 left, 789 right, one shared grid.",
    "She walks. Two constants instead of a training run.",
    "She typed the ticker herself.",
    "$HER. Launched by the female fly, from her own wallet.",
]

# Every clip is fitted into the same 16:9 box, letterboxed on black if it has
# to be, so the page can cover-fit one aspect ratio and never stretch.
FIT = (
    f"scale={W}:{H}:force_original_aspect_ratio=decrease,"
    f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1,fps={FPS}"
)


def run(cmd, **kw):
    try:
        return subprocess.run(cmd, check=True, capture_output=True, **kw)
    except subprocess.CalledProcessError as e:
        sys.stderr.write(e.stderr.decode(errors="replace"))
        raise SystemExit(f"command failed: {cmd[0]}")


def webp_args(pattern, quality):
    return ["-f", "image2", "-c:v", "libwebp", "-quality", str(quality),
            "-compression_level", "4", "-start_number", "1", str(pattern)]


def reset_out():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)


def small_set():
    # Phones get a quarter-size copy of the same frames; the page picks the
    # set by viewport width so a 4G visitor is not asked for 40 MB.
    m = OUT / "m"
    if m.exists():
        shutil.rmtree(m)
    m.mkdir()
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
         "-i", str(OUT / "f%04d.webp"), "-vf", f"scale={MW}:{MH}"]
        + webp_args(m / "f%04d.webp", 55))


def write_manifest(counts):
    scenes, start = [], 0
    for i, n in enumerate(counts):
        scenes.append({"start": start, "end": start + n - 1, "text": TEXT[i]})
        start += n
    manifest = {"frames": start, "fps": FPS, "width": W, "height": H, "v": int(time.time()),
                "small": {"dir": "m", "width": MW, "height": MH}, "scenes": scenes}
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=1) + "\n")
    small_set()
    size = sum(p.stat().st_size for p in OUT.iterdir())
    print(f"{start} frames, {len(scenes)} scenes, {size / 1e6:.1f} MB in {OUT}")


def build(src):
    src = Path(src)
    clips = [src / f"scene{i}.mp4" for i in range(SCENES)]
    missing = [c.name for c in clips if not c.exists()]
    if missing:
        raise SystemExit("missing clips: " + ", ".join(missing))

    # Each clip is extracted on its own so the scene boundaries in the manifest
    # are exact frame counts, not durations rounded to 12 fps and summed.
    with tempfile.TemporaryDirectory() as tmp:
        counts = []
        for i, clip in enumerate(clips):
            d = Path(tmp) / f"s{i}"
            d.mkdir()
            run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(clip),
                 "-vf", FIT, "-an"] + webp_args(d / "f%05d.webp", 72))
            frames = sorted(d.glob("f*.webp"))
            if not frames:
                raise SystemExit(f"no frames from {clip.name}")
            counts.append(len(frames))
            print(f"{clip.name}: {len(frames)} frames")
        reset_out()
        k = 0
        for i in range(SCENES):
            for f in sorted((Path(tmp) / f"s{i}").glob("f*.webp")):
                k += 1
                shutil.move(str(f), OUT / f"f{k:04d}.webp")
    write_manifest(counts)


def placeholder(seconds=5):
    from PIL import Image, ImageDraw, ImageFont

    rng = random.Random(1)
    per_scene = seconds * FPS

    # A side view of a fly as gaussian shells: head, thorax, abdomen, two wings,
    # six legs. Rough on purpose; the real film replaces all of it.
    pts = []

    def shell(cx, cy, rx, ry, n):
        for _ in range(n):
            a = rng.uniform(0, 2 * math.pi)
            r = 0.86 + 0.14 * rng.random()
            pts.append([cx + math.cos(a) * rx * r, cy + math.sin(a) * ry * r, rng.random()])

    def fill(cx, cy, rx, ry, n):
        for _ in range(n):
            a = rng.uniform(0, 2 * math.pi)
            r = math.sqrt(rng.random())
            pts.append([cx + math.cos(a) * rx * r, cy + math.sin(a) * ry * r, rng.random()])

    shell(0.42, 0.00, 0.20, 0.19, 260)
    shell(0.12, 0.00, 0.26, 0.22, 380)
    shell(-0.38, 0.02, 0.42, 0.24, 560)
    fill(0.50, 0.05, 0.10, 0.12, 140)
    for s in (1, -1):
        for _ in range(420):
            t, a = rng.random(), rng.random() - 0.5
            ln, wd = 0.95 * t, 0.16 * math.sin(math.pi * t) * (1 + 0.3 * a)
            pts.append([0.05 - ln * 0.92, -(0.20 + ln * 0.34 + wd * a * 0.7) * s * 0.6 - 0.15, rng.random()])
    for leg in range(6):
        bx = 0.24 - (leg % 3) * 0.16
        for _ in range(50):
            t = rng.random()
            pts.append([bx - t * 0.34, 0.18 + t * 0.42 + rng.gauss(0, 0.01), rng.random()])

    font = ImageFont.load_default(size=int(H * 0.9))
    scale = H * 0.42
    reset_out()
    ffm = subprocess.Popen(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
         "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-"]
        + webp_args(OUT / "f%04d.webp", 60),
        stdin=subprocess.PIPE)
    for i in range(SCENES * per_scene):
        scene, local = divmod(i, per_scene)
        t = i / FPS
        img = Image.new("RGB", (W, H), (0, 0, 0))
        dr = ImageDraw.Draw(img)
        # the scene numeral, faint, so a scene boundary is visible while scrubbing
        dr.text((W / 2, H / 2), str(scene), font=font, fill=(26, 12, 18), anchor="mm")
        sway = math.sin(t * 0.7) * 0.18
        drift = math.sin(t * 0.35) * 0.05 * W
        c, s = math.cos(sway), math.sin(sway)
        # the cloud gathers over the first second of a scene, then holds
        gather = min(1.0, local / FPS)
        for x, y, z in pts:
            spread = (1 - gather) * 0.6
            px = (x * c - y * s) * (1 + spread) * scale
            py = (x * s + y * c) * (1 + spread) * scale
            X = W / 2 - px + drift
            Y = H / 2 + py + math.sin(t * 2.1 + z * 6) * 3
            hot = ((z * 97 + t * 0.8) % 1.0) < 0.18
            col = (255, 121, 176) if hot else (140, 74, 104)
            k = 2 if hot else 1
            dr.rectangle([X, Y, X + k, Y + k], fill=col)
        ffm.stdin.write(img.tobytes())
    ffm.stdin.close()
    if ffm.wait() != 0:
        raise SystemExit("ffmpeg failed")
    write_manifest([per_scene] * SCENES)


def main(argv):
    if len(argv) == 3 and argv[1] == "build":
        build(argv[2])
    elif len(argv) == 2 and argv[1] == "placeholder":
        placeholder()
    else:
        sys.stderr.write(__doc__)
        raise SystemExit(2)


if __name__ == "__main__":
    main(sys.argv)
