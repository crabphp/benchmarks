"""Explicit maintainer refresh; ordinary runs use the committed pins."""
from pathlib import Path
import argparse, datetime, hashlib, json, re, urllib.request
ROOT = Path(__file__).resolve().parent
PACKAGES = {'crab':'crabphp/crab','webman':'workerman/webman','hyperf':'hyperf/hyperf-skeleton','symfony':'symfony/skeleton','spiral':'spiral/app','laravel':'laravel/laravel','tempest':'tempest/app','reactphp':'react/http','amphp':'amphp/http-server'}
FRAMEWORKS = {'crab':'crabphp/framework','webman':'workerman/webman-framework','hyperf':'hyperf/framework','symfony':'symfony/framework-bundle','spiral':'spiral/framework','laravel':'laravel/framework','tempest':'tempest/framework','reactphp':'react/http','amphp':'amphp/http-server'}
def latest(package):
    data=json.load(urllib.request.urlopen('https://repo.packagist.org/p2/'+package+'.json', timeout=30))['packages'][package]
    return next(v for v in data if re.fullmatch(r'v?\d+\.\d+\.\d+',v['version']))
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--only', nargs='+', choices=PACKAGES, help='Refresh only these contenders, retaining other pins.')
args = parser.parse_args()
manifest = json.loads((ROOT/'sources.json').read_text()) if args.only else {'apps': {}}
manifest['resolved_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
for name,package in PACKAGES.items():
    if args.only and name not in args.only: continue
    skeleton=latest(package); framework=latest(FRAMEWORKS[name])
    source=skeleton['source']; repo=source['url'].removesuffix('.git').removeprefix('https://github.com/')
    url=f"https://codeload.github.com/{repo}/tar.gz/{source['reference']}"
    data=urllib.request.urlopen(url,timeout=60).read()
    manifest['apps'][name]={'skeleton':package,'skeleton_version':skeleton['version'],'commit':source['reference'],'archive_url':url,'sha256':hashlib.sha256(data).hexdigest(),'framework':FRAMEWORKS[name],'version':framework['version']}
    print(name,skeleton['version'],FRAMEWORKS[name],framework['version'],flush=True)
(ROOT/'sources.json').write_text(json.dumps(manifest,indent=2)+'\n')
