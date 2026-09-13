"""Send changed canvases to the same relay that carries her room record."""
import hashlib
import urllib.request

_sent = {}


def publish(directory, origin, token):
    paths = [directory / "canvas.png", *sorted((directory / "gallery").glob("*.png"))]
    for path in paths:
        if not path.is_file():
            continue
        data = path.read_bytes()
        route = "/paintroom/" + ("gallery/" if path.parent.name == "gallery" else "") + path.name
        key = (origin, route)
        digest = hashlib.sha256(data).digest()
        if _sent.get(key) == digest:
            continue
        request = urllib.request.Request(origin + route, method="POST", data=data,
            headers={"Authorization": "Bearer " + token, "Content-Type": "image/png", "User-Agent": "flybrain"})
        with urllib.request.urlopen(request, timeout=5) as response:
            if response.status != 200:
                raise OSError("canvas publication failed")
        _sent[key] = digest
