"""Add an audited Next.js row directly under Crab without changing any existing row."""
from pathlib import Path
import argparse
import html
import json
import re

from audit import audit


def read(directory, filename):
    return json.loads((directory / filename).read_text())


def image(metadata, name):
    return next(line for line in metadata['images'].splitlines() if line.startswith(name + '='))


def cpu_model(metadata):
    return next(line.split(':', 1)[1].strip() for line in metadata['cpu'].splitlines() if line.startswith('Model name:')).split(' CPU @')[0].replace('(R)', '').replace('(TM)', '')


def publish(results, baseline, site):
    audit(baseline, require_full=True)
    audit(results, require_nextjs=True)
    old, new = read(baseline, 'metadata.json'), read(results, 'metadata.json')
    assert cpu_model(old) == cpu_model(new), 'CPU model differs from baseline'
    assert old['host'] == new['host'], 'Host platform differs from baseline'
    for name in ['MYSQL_IMAGE', 'LOADGEN_IMAGE']:
        assert image(old, name) == image(new, name), name + ' differs from baseline'
    summary = read(results, 'summary.json')
    check = read(results, 'preflight.json')[0]['metadata']
    node = check['node']
    version = new['sources']['apps']['nextjs']['version']
    cells = []
    for case in ['hello', 'db']:
        row = next(r for r in summary if (r['case'], r['connections'], r['service']) == (case, 64, 'nextjs'))
        cells.append(f'<td class="num" title="Trial range: {row["rps_min"]:,.0f}–{row["rps_max"]:,.0f} requests/s">{row["rps"]:,.0f}</td>')
    row = f'              <tr><th scope="row">Next.js {html.escape(version)} <span class="faint">Node.js {html.escape(node)} · standalone</span></th>{"".join(cells)}</tr>'
    path = site / 'index.html'
    text = path.read_text()
    start = text.index('      <section class="section" aria-labelledby="benchmarks">')
    end = text.index('      </section>', start) + len('      </section>')
    section = text[start:end]
    assert 'Next.js' not in section, 'Next.js row already present'
    crab = re.search(r'              <tr class="crab-row">.*</tr>\n', section)
    assert crab, 'Crab row not found'
    section = section[:crab.end()] + row + '\n' + section[crab.end():]
    url = 'https://github.com/crabphp/benchmarks/tree/main/results/' + results.name
    note = (f'        <p class="faint">Next.js runs on Node.js {html.escape(node)} (two cluster workers, mysql2 pool), not PHP. '
            f'Tested separately {new["started_utc"][:10]}; listed under Crab for comparison, not by rank. '
            f'<a href="{url}">Next.js results</a></p>\n')
    anchor = section.rindex('        <p class="faint">')
    section = section[:anchor] + note + section[anchor:]
    path.write_text(text[:start] + section + text[end:])
    print('Updated', path, 'with a separately dated Next.js row; existing rows unchanged.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('results', type=Path)
    parser.add_argument('--baseline', required=True, type=Path)
    parser.add_argument('--site', required=True, type=Path)
    args = parser.parse_args()
    publish(args.results, args.baseline, args.site)
