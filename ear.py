"""Stereo sound becomes a slow drive into the Johnston organ."""
import math
import subprocess

import numpy as np
from scipy.signal import butter, sosfiltfilt

SAMPLE_RATE = 22050
RATE = 2


def analyse(path, seconds=None):
    """Read sound and keep half-second envelopes beside the original file."""
    command = ["ffmpeg", "-v", "error", "-i", str(path)]
    if seconds is not None:
        if not math.isfinite(seconds) or seconds <= 0:
            raise ValueError("seconds must be positive and finite")
        command += ["-t", str(seconds)]
    command += ["-f", "f32le", "-ac", "2", "-ar", str(SAMPLE_RATE), "-"]
    decoded = subprocess.run(command, capture_output=True, check=True, timeout=120)
    sound = np.frombuffer(decoded.stdout, dtype="<f4").reshape(-1, 2)
    window = SAMPLE_RATE // RATE
    rows = math.ceil(len(sound) / window)
    table = np.zeros((rows, 4), dtype=np.float32)
    # JO-A receives 100-500 Hz, where courtship song and near-field vibrations sit.
    # JO-B receives 500-2,500 Hz, giving the higher vibrations their own entrance.
    for band, limits in enumerate(((100, 500), (500, 2500))):
        if not len(sound):
            break
        sos = butter(4, limits, btype="bandpass", fs=SAMPLE_RATE, output="sos")
        filtered = sosfiltfilt(sos, sound, axis=0, padlen=min(27, len(sound) - 1))
        for row in range(rows):
            chunk = filtered[row * window:(row + 1) * window]
            table[row, band * 2:band * 2 + 2] = np.sqrt(np.mean(chunk ** 2, axis=0))
    if rows:
        # One scale for all four columns: a quiet band must stay quiet next to a
        # loud one, so the loudest passage of the track sets 1.0 everywhere.
        scale = float(np.percentile(table, 95))
        if scale > 0:
            table /= scale
        np.clip(table, 0, 1, out=table)
    result = {"rate": RATE, "duration": len(sound) / SAMPLE_RATE, "table": table}
    np.savez(str(path) + ".ear.npz", **result)
    return result


class FlyEar:
    def __init__(self, fb, max_hz=150.0):
        self.max_hz = float(max_hz)
        self.groups = {}
        for kind in ("A", "B"):
            indices = fb.where(type_re=rf"^JO-{kind}$", subclass="auditory")
            for side in ("L", "R"):
                self.groups[f"JO-{kind}_{side}"] = tuple(
                    indices[np.asarray(fb.soma_side)[indices] == side])
        self.counts = {name: len(indices) for name, indices in self.groups.items()}

    def analyse(self, path, seconds=None):
        return analyse(path, seconds=seconds)

    def drive(self, table, t):
        if not math.isfinite(t) or t < 0:
            return None
        row = math.floor(t * float(table["rate"]))
        if row >= len(table["table"]) or t >= float(table["duration"]):
            return None
        return {indices: float(value) * self.max_hz
                for indices, value in zip(self.groups.values(), table["table"][row])
                if indices}
