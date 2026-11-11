"""Independently recompute the published medians from retained wrk logs."""
from pathlib import Path
import argparse, hashlib, json, math, statistics

def audit(directory: Path, require_full: bool = False, require_libraries: bool = False):
    def read(name):
        return json.loads((directory/name).read_text())
    metadata=read('metadata.json'); trials=read('trials.json'); warmups=read('warmups.json'); summary=read('summary.json')
    assert not (require_full and require_libraries), 'Choose one publication scope'
    if require_full or require_libraries:
        assert metadata['valid'] and metadata['completed_utc'], 'Not a complete valid reference run'
        original={'crab','webman','hyperf','symfony','spiral','laravel','tempest'}
        services=set(metadata.get('services', original))
        if require_libraries:
            assert not metadata['full_method'], 'A supplemental run must not claim the full method'
            assert services == {'reactphp', 'amphp'}, 'Supplement requires exactly the two HTTP libraries'
            assert services <= set(metadata['sources']['apps']), 'Missing library source pins'
            cases={('hello',64),('db',64)}
        else:
            assert metadata['full_method'], 'Not a complete valid reference run'
            # Historical seven-contender evidence remains auditable.
            assert services in [original, original | {'reactphp', 'amphp'}], 'Unknown or incomplete contender set'
            assert set(metadata['sources']['apps']) == services, 'Sources do not match contenders'
            cases={('hello',64),('hello',256),('db',64),('validate',64)}
        assert (metadata['warmup_seconds'], metadata['duration_seconds'], metadata['trials']) == (5, 15, 5)
        count=len(services)*len(cases)
        assert len(trials)==count*5 and len(warmups)==count*5 and len(summary)==count
        assert {(r['kind'],r['connections'],r['service'],r['trial']) for r in trials} == {
            (kind,connections,service,trial) for kind,connections in cases for service in services for trial in range(1,6)
        }
        assert {(r['case'],r['connections'],r['service']) for r in summary} == {
            (kind,connections,service) for kind,connections in cases for service in services
        }
        checks=read('preflight.json')
        assert len(checks)==count and all(r['ok'] for r in checks)
        assert {(r['case'], r['service']) for r in checks} == {(f'{kind}-{connections}', service) for kind, connections in cases for service in services}
        assert {r['label'] for r in warmups} == {
            f'{kind}-{connections}-{service}-warmup-{trial}'
            for kind, connections in cases for service in services for trial in range(1, 6)
        }
        for row in checks:
            assert row['metadata']['php'].startswith('8.5.') and row['metadata']['debug'] is False
            assert not (row['metadata'].get('jit') or {}).get('on', False)

    hashes={}
    for record in trials+warmups:
        suffix='trial-' + str(record['trial']) if 'trial' in record else None
        # Locate warmup records by their exact recorded measurements.
        pattern=f"{record['kind']}-{record['connections']}-{record['service']}-{'trial-*' if suffix else 'warmup-*'}.log"
        found=[]
        paths=[directory/(record['label']+'.log')] if 'label' in record else directory.glob(pattern)
        for path in paths:
            values=[json.loads(line.removeprefix('BENCH_JSON ')) for line in path.read_text().splitlines() if line.startswith('BENCH_JSON ')]
            if len(values)==1 and values[0]['duration_us']==record['duration_us'] and values[0]['requests']==record['requests']:
                found.append((path,values[0]))
        assert len(found)==1, ('Missing or ambiguous raw log',record['service'],pattern)
        path,raw=found[0]
        for key in ['rps','p50_us','p99_us','errors','bad_response','bad_body','requests']:
            assert raw[key]==record[key], (path,key)
        assert record['requests']>0
        error_count=raw['bad_response']+sum(raw['errors'][k] for k in ['connect','read','write','timeout'])
        assert error_count==record['error_count']
        if require_full or require_libraries: assert error_count==0,(path,error_count)
        hashes[path.name]=hashlib.sha256(path.read_bytes()).hexdigest()
    for row in summary:
        records=[r for r in trials if (r['kind'],r['connections'],r['service'])==(row['case'],row['connections'],row['service'])]
        assert len(records)==metadata['trials']==row['runs']
        for key,expected in {
            'rps':statistics.median(r['rps'] for r in records),
            'rps_min':min(r['rps'] for r in records),
            'rps_max':max(r['rps'] for r in records),
            'p50_ms':statistics.median(r['p50_us'] for r in records)/1000,
            'p99_ms':statistics.median(r['p99_us'] for r in records)/1000,
            'errors':sum(r['error_count'] for r in records),
        }.items():
            assert math.isclose(row[key],expected,rel_tol=1e-12),(row,key)
    result={'verified_trials':len(trials),'verified_warmups':len(warmups),'verified_summary_rows':len(summary),'full_method':metadata['full_method'],'raw_log_sha256':hashes}
    (directory/'audit.json').write_text(json.dumps(result,indent=2)+'\n')
    return result

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory',type=Path)
    scope=parser.add_mutually_exclusive_group()
    scope.add_argument('--require-full',action='store_true')
    scope.add_argument('--require-libraries',action='store_true',help='Verify a five-trial, two-library Hello/MySQL supplement at 64 connections.')
    args=parser.parse_args()
    result=audit(args.directory,args.require_full,args.require_libraries)
    print(f"Verified {result['verified_trials']} measured trials and {result['verified_warmups']} warmups from raw logs.")
