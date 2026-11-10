"""Update the site table only from a complete run verified against raw logs."""
from pathlib import Path
import argparse, html, json
from audit import audit

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('results',type=Path)
parser.add_argument('--site',type=Path,required=True)
args=parser.parse_args()
audit(args.results,require_full=True)
metadata=json.loads((args.results/'metadata.json').read_text())
summary=json.loads((args.results/'summary.json').read_text())
versions=json.loads((args.results/'versions.json').read_text())
php_version=versions['crab']['metadata']['php']
labels={'crab':('Crab','Native server'),'webman':('webman','Workerman'),'hyperf':('Hyperf','Swoole'),'symfony':('Symfony','FrankenPHP'),'spiral':('Spiral','RoadRunner'),'laravel':('Laravel','Octane · FrankenPHP'),'tempest':('Tempest','FrankenPHP')}
rows=[]
for service,(label,runtime) in labels.items():
    version=metadata['sources']['apps'][service]['version'].removeprefix('v')
    values=[]
    for case in ['hello','db']:
        row=next(r for r in summary if (r['case'],r['connections'],r['service'])==(case,64,service))
        values.append(f'<td class="num" title="Trial range: {row["rps_min"]:,.0f}–{row["rps_max"]:,.0f} requests/s">{row["rps"]:,.0f}</td>')
    attr=' class="crab-row"' if service=='crab' else ''
    rows.append(f'              <tr{attr}><th scope="row">{label} {version} <span class="faint">{runtime}</span></th>{"".join(values)}</tr>')
date=metadata['started_utc'][:10]
cpu_model=next(line.split(':',1)[1].strip() for line in metadata['cpu'].splitlines() if line.startswith('Model name:')).split(' CPU @')[0].replace('(R)','').replace('(TM)','')
url='https://github.com/crabphp/benchmarks/tree/main/results/'+args.results.name
section=f'''      <section class="section" aria-labelledby="benchmarks">
        <h2 id="benchmarks">Benchmarks</h2>
        <div class="table-wrap">
          <table>
            <caption>Requests per second · PHP {html.escape(php_version)} · 64 connections · median of five runs.</caption>
            <thead>
              <tr><th scope="col">Framework</th><th scope="col" class="num">Hello</th><th scope="col" class="num">Database</th></tr>
            </thead>
            <tbody>
{chr(10).join(rows)}
            </tbody>
          </table>
        </div>
        <p class="faint">{html.escape(cpu_model)} · 2 CPU / 2 GiB RAM limit per app (shared host). Tested {date}. <a href="{url}">Full results</a> · <a href="https://github.com/crabphp/benchmarks">Run it yourself <span aria-hidden="true">↗</span></a></p>
      </section>'''
p=args.site/'index.html';text=p.read_text();start=text.index('      <section class="section" aria-labelledby="benchmarks">');end=text.index('      </section>',start)+len('      </section>');p.write_text(text[:start]+section+text[end:])
print('Updated',p)
