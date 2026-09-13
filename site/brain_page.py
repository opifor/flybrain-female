"""Write a map of the entrances and readouts in the female brain."""
import argparse
from html import escape
from pathlib import Path
import re
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from calibration import CHOSEN, SETTINGS


def build(graph, output):
    with np.load(graph, allow_pickle=False) as z:
        types = z['types'].astype(str)
        n = len(types)
        sub = z['subclass'].astype(str) if 'subclass' in z else np.full(n, '')
        sides = z['soma_side'] if 'soma_side' in z else np.full(n, '')
        def match(values, pattern):
            return np.array([bool(re.search(pattern, t, re.I)) for t in values])
        def count(pattern):
            return int(match(types, pattern).sum())
        def row(label, value):
            return f'<li>{escape(label)}: <strong>{value:,}</strong> cells</li>'
        def group(title, intro, rows):
            return f'<section><h2>{title}</h2><p>{intro}</p><ul>{"".join(rows)}</ul></section>'
        edges = len(z['data'])
        signs = z['sign'][z['indices']]
        positive, negative = int((signs > 0).sum()), int((signs < 0).sum())
        contacts = np.rint(np.abs(z['data'].astype(float)) / 0.275)
        total = int(contacts.sum())
        summary = (f'{n:,} neurons · {edges:,} signed connections · {total:,} synaptic contacts')
        content = f'<h1>Her brain, by its doors</h1><p class="lede">{summary}</p>'
        content += (f'<p>{positive:,} excitatory connections and {negative:,} inhibitory connections, '
                    f'from the sending cell’s sign; {int(contacts[signs > 0].sum()):,} excitatory and '
                    f'{int(contacts[signs < 0].sum()):,} inhibitory contacts. '
                    'Contacts are recovered from the stored weights at 0.275 mV per contact. '
                    'This is the filtered, signed graph: pairs with at least five synapses; '
                    'modulatory and unknown-sign connections are omitted.</p>')
        sensory = []
        for t in ('L1', 'L2'):
            sensory.append(row(t + ' total', count('^' + t + '$')))
            if 'has_hex' in z:
                sensory.append(row(t + ' with a retinal hex', int(((types == t) & z['has_hex']).sum())))
        sensory += [row('ORN total', count('^ORN_'))]
        sensory += [row(t + ' / auditory subclass', int(((types == t) & (sub == 'auditory')).sum())) for t in ('JO-A', 'JO-B')]
        content += group('What she can sense', 'Screen light enters L1 and L2 through the hex retina. DoOR odorants enter matching ORN types. Sound enters JO-A and JO-B. These are population counts; a particular odorant does not drive every ORN.', sensory)
        readouts = [row(t + ' ' + side, int(((types == t) & (sides == side)).sum())) for t in ('DNa02', 'DNa01') for side in ('L', 'R')]
        readouts += [row(t, count('^' + t + '$')) for t in ('MDN', 'DNp09')]
        readouts += [row('Proboscis motor', int((sub == 'proboscis_motor_neuron').sum()))]
        readouts += [row(t, count('^' + t)) for t in ('KC', 'MBON', 'PAM', 'PPL1')]
        content += group('What we read from her', 'DNa02 steers; DNa01 moves forward; MDN moves back; DNp09 stops. A click means DNp09 reaches click_hz while speed is below 0.25. Proboscis motor cells are recorded as the click readout group, not the trigger. KC → MBON connections change with dopamine; their responses carry learned smell preferences.', readouts)
        empty = []
        for name, tp, sp in [
            ('Taste / gustatory', r'gustatory|^GRN', r'^(bitter|low-salt|sugar/water|taste_peg|water_PN)$|gustatory'),
            ('Compass EPG', r'^EPG$', r'^EPG$'),
            ('Clock', r'^(5th-LNv|[sl]-LNv|LNd.*|DN1[a-zA-Z-]*|DN2|DN3)$', r'^(LNv|DN1p|DN3)$'),
            ('Thermo / hygro', r'thermo|hygro', r'^(cold|cooling|dry|evaporative_cooling|heating|humid|moist)$')]:
            mask = match(types, tp) | match(sub, sp)
            labels = sorted(set(types[mask]) | set(sub[mask]))
            empty.append(row(name, int(mask.sum())) + '<li>Matched type <code>' + escape(tp) + '</code> or subclass <code>' + escape(sp) + '</code> (case-insensitive). Labels found: ' + escape(', '.join(v for v in labels if v) or 'none') + '.</li>')
        content += group('What nobody talks to yet', 'These entrances receive no direct input from us. The rest of the brain is not given extra sensory input either; cells may still receive activity through the connectome. These annotation searches are a map of named groups, not an exhaustive biological census.', empty)
        exc = float(z['exc_scale']) if 'exc_scale' in z else 1.0
        click = float(z['click_hz']) if 'click_hz' in z else 330.0
        drive = float(z['drive_hz']) if 'drive_hz' in z else 180.0
        content += '<section><h2>How she is tuned</h2><p>Graph defaults, not a live settings readout; saved roaming gains can override drive and click thresholds.</p>'
        content += f'<p><b>exc_scale · {exc:g}</b> scales excitatory weights; the builder chose the largest tested scale within firing-ceiling and movement limits with both eyes.</p>'
        content += f'<p><b>click_hz · {click:g} Hz</b> sets the stopping threshold for clicks; 100 and 120 Hz tied at five clicks in 48 trials, so the builder chose the lower threshold.</p>'
        content += f'<p><b>drive_hz · {drive:g} Hz</b> caps retinal input so screen brightness has a finite firing-rate range; when absent from the graph, the runtime default is 180 Hz.</p>'
        gains = SETTINGS[CHOSEN]['gains']
        content += '<p>The chosen mushroom-body setting scales outgoing weights: ' + ', '.join(f'{k} × {v:g}' for k, v in gains.items()) + '. It was chosen for sparse, distinct smell responses and limited changes to roaming. Learning still spreads partly to similar smells.</p></section>'
        names, counts = np.unique(z['superclass'], return_counts=True)
        content += group('The whole neighborhood', 'Cells by superclass, including those with no annotation.', [row(str(k) or 'Unlabelled', int(v)) for k, v in zip(names, counts)])
    index = (ROOT / 'site/web/index.html').read_text(encoding='utf-8')
    nav = re.search(r'<header class="site-nav">.*?</header>', index).group()
    nav = nav.replace('href="#live"', 'href="brain.html"').replace('href="#story"', 'href="story.html"').replace('href="#ca-text"', 'href="index.html#ca-text"')
    font = re.search(r'<link rel="stylesheet" href="https://fonts.googleapis.com[^>]+>', index).group()
    page = '<!doctype html>\n<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Her brain · Female Flybrain</title><link rel="stylesheet" href="rooms.css">' + font + '</head><body>' + nav + '<main>' + content
    page += '<footer><p>Connectome data: FlyWire FAFB v783, released CC-BY by the FlyWire Consortium, Princeton University and the University of Cambridge. Dorkenwald et al. 2024 (Nature) and Schlegel et al. 2024 (Nature).</p></footer></main></body></html>\n'
    Path(output).write_text(page, encoding='utf-8')
    print(summary)
    print(f'{positive:,} excitatory connections; {negative:,} inhibitory connections')
    return page


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['build'])
    local_graph = ROOT / 'build/graph_female.npz'
    default_graph = local_graph if local_graph.exists() else ROOT.parent / 'flycoinrh/build/graph_female.npz'
    parser.add_argument('--graph', type=Path, default=default_graph)
    parser.add_argument('--output', type=Path, default=ROOT / 'site/web/brain.html')
    args = parser.parse_args()
    build(args.graph, args.output)
