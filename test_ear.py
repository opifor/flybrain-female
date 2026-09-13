"""Sound reaches the right cells, with the music's credits kept beside it."""
import re
import json
import shutil
import wave
from types import SimpleNamespace

import numpy as np
import pytest

from ear import FlyEar, analyse
from music_catalog import allowed_license, build_record, eligible
import music_catalog

has_ffmpeg = pytest.mark.skipif(shutil.which("ffmpeg") is None,
                                reason="ffmpeg is missing from PATH")


class FakeBrain:
    def __init__(self):
        self.types = np.array(["JO-A", "JO-A", "JO-A", "JO-B", "JO-B", "JO-B", "L1"])
        self.subclass = np.array(["auditory"] * 6 + ["visual"])
        self.soma_side = np.array(["L", "L", "R", "L", "R", "R", "L"])

    def where(self, type_re=None, subclass=None):
        return np.flatnonzero([
            (type_re is None or re.search(type_re, kind))
            and (subclass is None or group == subclass)
            for kind, group in zip(self.types, self.subclass)])


def write_wav(path, sound):
    with wave.open(str(path), "wb") as output:
        output.setnchannels(2)
        output.setsampwidth(2)
        output.setframerate(22050)
        output.writeframes((sound * 20000).astype("<i2").tobytes())


@has_ffmpeg
def test_stereo_bands(tmp_path):
    path = tmp_path / "song.wav"
    t = np.arange(22050 * 4) / 22050
    sound = np.zeros((len(t), 2))
    sound[:44100, 0] = np.sin(2 * np.pi * 200 * t[:44100])
    sound[44100:, 1] = np.sin(2 * np.pi * 1200 * t[44100:])
    write_wav(path, sound)
    result = analyse(path)
    assert result["table"].shape == (8, 4)
    assert result["table"].dtype == np.float32
    assert result["rate"] == 2
    assert result["duration"] == 4
    np.testing.assert_array_equal(result["table"].argmax(axis=1), [0] * 4 + [3] * 4)
    with np.load(str(path) + ".ear.npz") as saved:
        np.testing.assert_array_equal(saved["table"], result["table"])
        assert saved["duration"] == 4
        assert saved["rate"] == 2
    limited = FlyEar(FakeBrain()).analyse(path, seconds=1.25)
    assert limited["table"].shape == (3, 4)
    assert limited["duration"] == pytest.approx(1.25, abs=1 / 22050)


@has_ffmpeg
@pytest.mark.parametrize("samples", [0, 1, 100, 22050])
def test_silence_and_short_audio(tmp_path, samples):
    path = tmp_path / "silence.wav"
    write_wav(path, np.zeros((samples, 2)))
    result = analyse(path)
    np.testing.assert_array_equal(result["table"], np.zeros_like(result["table"]))
    assert len(result["table"]) == (samples + 11024) // 11025


def test_drive():
    ear = FlyEar(FakeBrain(), max_hz=100)
    table = {"rate": 2, "duration": 1, "table": np.array([[.1, .2, .3, .4], [1, 0, 0, 0]])}
    result = ear.drive(table, .2)
    assert result == {(0, 1): 10, (2,): 20, (3,): 30, (4, 5): 40}
    indices = [i for group in result for i in group]
    assert len(indices) == len(set(indices))
    assert ear.counts == {"JO-A_L": 2, "JO-A_R": 1, "JO-B_L": 1, "JO-B_R": 2}
    assert ear.drive(table, .5)[(0, 1)] == 100
    for t in (-1, 1, 99, float("nan")):
        assert ear.drive(table, t) is None
    assert ear.drive({"rate": 2, "duration": 0, "table": np.empty((0, 4))}, 0) is None
    brain = FakeBrain()
    brain.soma_side[brain.types == "JO-B"] = "L"
    assert len(FlyEar(brain).drive(table, 0)) == 3


@pytest.mark.parametrize("license, accepted", [
    ("CC0", True), ("CC BY 4.0", True), ("CC BY-SA 3.0", True),
    ("CC BY-NC 4.0", False), ("CC BY-ND 4.0", False),
    ("Public domain", False), ("", False), ("All rights reserved", False)])
def test_license_filter(license, accepted):
    assert allowed_license(license) is accepted


def test_catalog_record():
    page = {"pageid": 42, "title": "File:Evening song.ogg", "imageinfo": [{
        "url": "https://upload.wikimedia.org/example.ogg", "mime": "audio/ogg",
        "size": 12345, "extmetadata": {
            "LicenseShortName": {"value": "CC BY-SA 4.0"},
            "ObjectName": {"value": "<i>Evening &amp; dawn</i>"},
            "Artist": {"value": '<a href="/wiki/User:Someone">A. Singer</a>'}}}]}
    assert eligible(page)
    record = build_record(page, "data/music/42.ogg", 120)
    assert record == {"id": 42, "title": "Evening & dawn", "artist": "A. Singer",
                      "license": "CC BY-SA 4.0", "mime": "audio/ogg", "duration": 120.0,
                      "page": "https://commons.wikimedia.org/wiki/File%3AEvening%20song.ogg",
                      "file": "data/music/42.ogg", "ear": "data/music/42.ogg.ear.npz"}
    del page["imageinfo"][0]["extmetadata"]["ObjectName"]
    assert build_record(page, "data/music/42.ogg", 120)["title"] == "Evening song"
    page["imageinfo"][0]["size"] = 41 * 1024 * 1024
    assert not eligible(page)
    page["imageinfo"][0]["size"] = 100
    page["imageinfo"][0]["mime"] = "video/ogg"
    assert not eligible(page)


def test_fetch_stops_at_count_and_reuses_download(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    directory = tmp_path / "music"
    directory.mkdir()
    (directory / "1.ogg").write_bytes(b"existing sound")
    pages = [{"pageid": number, "title": f"File:Song {number}.ogg", "imageinfo": [{
        "mime": "audio/ogg", "size": 100, "url": "https://example.org/song.ogg",
        "extmetadata": {"LicenseShortName": {"value": "CC0"}}}]} for number in (1, 2, 3)]
    downloads, analysed = [], []

    class Shelf:
        session = SimpleNamespace(close=lambda: None)

        def pages(self):
            yield from pages

        def download(self, url, path):
            downloads.append(path.name)
            path.write_bytes(b"new sound")

    def read_sound(path):
        analysed.append(path.name)
        np.savez(str(path) + ".ear.npz", rate=2, duration=60, table=np.zeros((120, 4)))

    monkeypatch.setattr(music_catalog, "Commons", Shelf)
    monkeypatch.setattr(music_catalog, "analyse", read_sound)
    monkeypatch.setattr(music_catalog.subprocess, "run", lambda *a, **k:
                        SimpleNamespace(stdout='{"format": {"duration": "60"}}'))
    records = music_catalog.fetch(2, directory)
    assert [record["id"] for record in records] == [1, 2]
    assert downloads == ["2.ogg"]
    assert analysed == ["1.ogg", "2.ogg"]
    assert json.loads((directory / "catalog.json").read_text()) == records
    assert records[0]["file"] == "music/1.ogg"
