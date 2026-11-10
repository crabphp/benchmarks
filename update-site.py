"""Update the site table only from a complete run verified against raw logs."""
from pathlib import Path
import argparse, html, json
from audit import audit

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('results',type=Path)
parser.add_argument('--site',type=Path,required=True)
args=parser.parse_args()
verification=audit(args.results,require_full=True)
metadata=json.loads((args.results/'metadata.json').read_text())
summary=json.loads((args.results/'summary.json').read_text())
versions=json.loads((args.results/'versions.json').read_text())
php_version=versions['crab']['metadata']['php']
symfony_db=next(row for row in summary if (row['case'],row['connections'],row['service'])==('db',64,'symfony'))
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
url='https://github.com/crabphp/benchmarks/tree/main/results/'+args.results.name
section=f'''      <section class="section" aria-labelledby="benchmarks">
        <h2 id="benchmarks">Benchmarks</h2>
        <div class="table-wrap">
          <table>
            <caption>Requests per second, median of five 15-second trials, with 64 persistent connections. PHP {html.escape(php_version)}, JIT off, two application workers. Hello returns JSON; Database reads one MySQL row.</caption>
            <thead>
              <tr><th scope="col">Framework</th><th scope="col" class="num">Hello</th><th scope="col" class="num">Database</th></tr>
            </thead>
            <tbody>
{chr(10).join(rows)}
            </tbody>
          </table>
        </div>
        <p class="faint">Measured {date} on a shared Linux {html.escape(metadata['docker']['Architecture'])} machine with {metadata['docker']['NCPU']} logical CPUs, using Docker. Each application has the same 2-CPU quota and 2 GiB limit; CPU cores are shared. Zero errors across all measured trials and warmups. Small synthetic workloads, not a universal ranking or a capacity estimate. <a href="{url}">Raw results and trial ranges <span aria-hidden="true">↗</span></a> · <a href="https://github.com/crabphp/benchmarks">Methodology and one-command reproduction <span aria-hidden="true">↗</span></a></p>
        <p class="faint">Symfony's database trials ranged from {symfony_db['rps_min']:,.0f} to {symfony_db['rps_max']:,.0f} requests/s. Its median should be read alongside that variability.</p>
        <details>
          <summary>Verify the benchmark evidence</summary>
          <p>{verification['verified_trials']} measured trials and {verification['verified_warmups']} warmups were checked against the retained raw logs. The audit recomputes the medians and records SHA-256 hashes of those logs. It is reproducible with the public script; it is not a third-party certification.</p>
          <p><a href="{url}/audit.json">Raw-log audit and hashes</a> · <a href="{url}/versions.json">Exact framework and PHP versions</a> · <a href="{url}/metadata.json">Machine and run settings</a> · <a href="{url}/harness">Source snapshot used for this run</a></p>
          <p>From a clone of <a href="https://github.com/crabphp/benchmarks">crabphp/benchmarks</a>, verify the published data:</p>
          <p><code>python3 audit.py results/{html.escape(args.results.name)} --require-full</code></p>
          <p>To run a new benchmark on your machine, use <code>./run.sh</code>. Prerequisites: Docker Compose, Python 3.12+ and Bash. Results will vary with hardware and host activity.</p>
        </details>
      </section>'''
p=args.site/'index.html';text=p.read_text();start=text.index('      <section class="section" aria-labelledby="benchmarks">');end=text.index('      </section>',start)+len('      </section>');p.write_text(text[:start]+section+text[end:])
print('Updated',p)
