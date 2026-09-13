"""Render room pages from the same ground and declaration block."""
import json
from pathlib import Path

import betroom
import hall
import tiproom
import musicroom
import gameroom
import paintroom

WEB = Path(__file__).parent / "web"


def page(declaration, cards, style, script):
    text = (WEB / "room.html").read_text(encoding="utf-8")
    values = {"title": declaration.name, "declaration": json.dumps(declaration.public()).replace("<", "\\u003c"),
              "cards": cards, "style": style, "script": script,
              "door":
                      '\n'.join(f'<div id="door-{edge}" class="door {edge}"'
                                + ('' if declaration.path == '/hall' else ' data-token="/hall"') + '>'
                                f'{"the hall" if edge in ("top", "bottom") else ""}</div>'
                                for edge in ("top", "bottom", "left", "right"))}
    for key, value in values.items():
        text = text.replace("{{" + key + "}}", value)
    return text


def pages():
    betting = page(betroom.DECLARATION, '<div id="fast" class="grid"></div>',
                   (WEB / "betroom.css").read_text(encoding="utf-8"),
                   (WEB / "betroom.js").read_text(encoding="utf-8"))
    script = (WEB / "room_cards.js").read_text(encoding="utf-8")
    style = """
.grid{grid-template-columns:repeat(4,268px);grid-auto-rows:280px;gap:32px}
.card{align-self:center;justify-self:center;padding:22px;border-color:#aaaaaa}
.name{font-size:22px;line-height:1.4;overflow-wrap:anywhere}
body.tiproom .name{font-size:18px}
body.musicroom .grid{grid-template-columns:repeat(4,280px);grid-auto-rows:200px;gap:16px}
body.musicroom .card{width:100%;height:100%;padding:14px}
body.musicroom .name{font-size:20px;line-height:1.3}
body.musicroom .detail{margin-top:12px;line-height:1.3;overflow-wrap:anywhere}
body.gameroom .grid{grid-template-columns:repeat(4,280px);grid-auto-rows:200px;gap:16px}
body.gameroom .card{width:100%;height:100%;padding:14px;display:flex;align-items:center;justify-content:center}
body.gameroom .name{font-size:28px}
body.gameroom .detail{display:none}
body.gameroom .card.resting{background:#303030;color:#777;border-color:#444}
body.paintroom .grid{grid-template-columns:repeat(4,280px);grid-auto-rows:200px;gap:16px}
body.paintroom .card{width:100%;height:100%;padding:14px;background:#181b2099}
body.paintroom .swatch{width:120px;height:120px;margin:0 auto 8px;background:var(--paint)}
body.paintroom .name{text-align:center;font-size:20px}
body.paintroom .detail{display:none}
#paint-canvas{position:absolute;top:0;left:0;width:1280px;height:620px;pointer-events:none}
.detail{color:#9aa7b8;font-size:16px;margin-top:24px}
body.hall .grid{grid-template-columns:repeat(4,268px);grid-auto-rows:200px;column-gap:32px;row-gap:16px}
body.hall .card{width:100%;height:100%;border-color:#9aa7b8;padding:16px}
body.hall .name{font-size:20px;margin-top:0}
body.hall .detail{font-size:18px;line-height:1.3;margin-top:12px}
body.hall #status{white-space:nowrap;text-overflow:ellipsis}
"""
    return {"betroom": betting,
            "paintroom": page(paintroom.DECLARATION,
                '<img id="paint-canvas" src="/paintroom/canvas.png" alt="Her current canvas"><div id="cards" class="grid"></div>', style, script),
            **{name: page(declaration, '<div id="cards" class="grid"></div>', style, script)
               for name, declaration in (("hall", hall.DECLARATION), ("tiproom", tiproom.DECLARATION),
                                         ("musicroom", musicroom.DECLARATION),
                                         ("gameroom", gameroom.DECLARATION))}}


def main():
    for name, text in pages().items():
        (WEB / (name + ".html")).write_text(text, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
