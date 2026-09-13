"""Render room pages from the same ground and declaration block."""
import json
from pathlib import Path

import betroom
import hall
import tiproom
import musicroom

WEB = Path(__file__).parent / "web"


def page(declaration, cards, style, script):
    text = (WEB / "room.html").read_text(encoding="utf-8")
    values = {"title": declaration.name, "declaration": json.dumps(declaration.public()).replace("<", "\\u003c"),
              "cards": cards, "style": style, "script": script,
              "door": '' if declaration.path == "/hall" else
                      '\n'.join(f'<div id="door-{edge}" class="door {edge}" data-token="/hall">'
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
.detail{color:#9aa7b8;font-size:16px;margin-top:24px}
body.hall .grid{grid-template-columns:repeat(2,568px);grid-auto-rows:600px}
body.hall .card{width:100%;height:100%;border-color:#9aa7b8;padding:42px}
body.hall .name{font-size:42px;margin-top:120px}
body.hall #status{white-space:nowrap;text-overflow:ellipsis}
"""
    return {"betroom": betting,
            **{name: page(declaration, '<div id="cards" class="grid"></div>', style, script)
               for name, declaration in (("hall", hall.DECLARATION), ("tiproom", tiproom.DECLARATION),
                                         ("musicroom", musicroom.DECLARATION))}}


def main():
    for name, text in pages().items():
        (WEB / (name + ".html")).write_text(text, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
