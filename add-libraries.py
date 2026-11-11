"""Add an audited two-library supplement without replacing existing framework measurements."""
from pathlib import Path
import argparse
import html
import json

from audit import audit

LABELS = {
    'crab': ('Crab', 'Native server'), 'webman': ('webman', 'Workerman'),
    'hyperf': ('Hyperf', 'Swoole'), 'symfony': ('Symfony', 'FrankenPHP'),
    'spiral': ('Spiral', 'RoadRunner'), 'laravel': ('Laravel', 'Octane · FrankenPHP'),
    'tempest': ('Tempest', 'FrankenPHP'),
    'reactphp': ('ReactPHP HTTP', 'ext-event · HTTP library'),
    'amphp': ('AMP HTTP Server', 'Revolt · ext-event · HTTP library'),
}
ORIGINAL = set(LABELS) - {'reactphp', 'amphp'}


def read(directory, filename):
    return json.loads((directory / filename).read_text())


def row_for(service, metadata, summary):
    label, runtime = LABELS[service]
    version = metadata['sources']['apps'][service]['version'].removeprefix('v')
    values = []
    for case in ['hello', 'db']:
        row = next(r for r in summary if (r['case'], r['connections'], r['service']) == (case, 64, service))
        values.append(f'<td class="num" title="Trial range: {row["rps_min"]:,.0f}–{row["rps_max"]:,.0f} requests/s">{row["rps"]:,.0f}</td>')
    attr = ' class="crab-row"' if service == 'crab' else ''
    return f'              <tr{attr}><th scope="row">{label} {html.escape(version)} <span class="faint">{runtime}</span></th>{"".join(values)}</tr>'


def publish(results, baseline, site):
    audit(baseline, require_full=True)
    audit(results, require_libraries=True)
    old, new = read(baseline, 'metadata.json'), read(results, 'metadata.json')
    old_summary, new_summary = read(baseline, 'summary.json'), read(results, 'summary.json')
    assert set(old['sources']['apps']) == ORIGINAL, 'Baseline must contain the existing seven frameworks'
    old_versions, new_versions = read(baseline, 'versions.json'), read(results, 'versions.json')
    php = old_versions['crab']['metadata']['php']
    assert all(new_versions[s]['metadata']['php'] == php for s in ['reactphp', 'amphp']), 'PHP version differs from baseline'
    assert old['cpu'] == new['cpu'] or cpu_model(old) == cpu_model(new), 'CPU model differs from baseline'
    assert old['host'] == new['host'], 'Host platform differs from baseline'
    assert old['images'] == new['images'], 'Runtime image pins differ from baseline'
    summary = old_summary + new_summary
    metadata = dict(new, sources={'apps': old['sources']['apps'] | {s: new['sources']['apps'][s] for s in ['reactphp', 'amphp']}})
    rows = {s: row_for(s, metadata, summary) for s in LABELS}
    path = site / 'index.html'
    text = path.read_text()
    start = text.index('      <section class="section" aria-labelledby="benchmarks">')
    end = text.index('      </section>', start) + len('      </section>')
    original_section = text[start:end]
    for service in ORIGINAL:
        assert rows[service] in original_section, 'Existing website row does not match baseline: ' + service
    order = sorted(LABELS, key=lambda s: -next(r['rps'] for r in summary if (r['case'], r['connections'], r['service']) == ('hello', 64, s)))
    base_url = 'https://github.com/crabphp/benchmarks/tree/main/results/'
    section = f'''      <section class="section" aria-labelledby="benchmarks">
        <h2 id="benchmarks">Benchmarks</h2>
        <div class="table-wrap">
          <table>
            <caption>Requests per second · PHP {html.escape(php)} · 64 connections · median of five runs.</caption>
            <thead>
              <tr><th scope="col">Framework / server</th><th scope="col" class="num">Hello</th><th scope="col" class="num">Database</th></tr>
            </thead>
            <tbody>
{chr(10).join(rows[s] for s in order)}
            </tbody>
          </table>
        </div>
        <p class="faint">ReactPHP and AMP are HTTP libraries, not full application frameworks. Each uses a router, explicit input validation and its native async MySQL driver.</p>
        <p class="faint">{html.escape(cpu_model(old))} · 2 CPU / 2 GiB RAM limit per app (shared host). Frameworks tested {old['started_utc'][:10]}; ReactPHP and AMP tested separately {new['started_utc'][:10]}. Separate runs, not a simultaneous comparison. <a href="{base_url + baseline.name}">Framework results</a> · <a href="{base_url + results.name}">ReactPHP / AMP results</a> · <a href="https://github.com/crabphp/benchmarks">Run it yourself <span aria-hidden="true">↗</span></a></p>
      </section>'''
    path.write_text(text[:start] + section + text[end:])
    print('Updated', path, 'with a separately dated two-library supplement; existing seven rows unchanged.')


def cpu_model(metadata):
    return next(line.split(':', 1)[1].strip() for line in metadata['cpu'].splitlines() if line.startswith('Model name:')).split(' CPU @')[0].replace('(R)', '').replace('(TM)', '')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('results', type=Path)
    parser.add_argument('--baseline', required=True, type=Path)
    parser.add_argument('--site', required=True, type=Path)
    args = parser.parse_args()
    publish(args.results, args.baseline, args.site)
