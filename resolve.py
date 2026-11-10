"""Explicit maintainer refresh; ordinary runs use the committed pins."""
from pathlib import Path
import concurrent.futures, datetime, hashlib, json, re, subprocess, urllib.request
ROOT = Path(__file__).resolve().parent
PACKAGES = {'crab':'crabphp/crab','webman':'workerman/webman','hyperf':'hyperf/hyperf-skeleton','symfony':'symfony/skeleton','spiral':'spiral/app','laravel':'laravel/laravel','tempest':'tempest/app'}
FRAMEWORKS = {'crab':'crabphp/framework','webman':'workerman/webman-framework','hyperf':'hyperf/framework','symfony':'symfony/framework-bundle','spiral':'spiral/framework','laravel':'laravel/framework','tempest':'tempest/framework'}
def latest(package):
    data=json.load(urllib.request.urlopen('https://repo.packagist.org/p2/'+package+'.json', timeout=30))['packages'][package]
    return next(v for v in data if re.fullmatch(r'v?\d+\.\d+\.\d+',v['version']))
manifest={'resolved_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'apps':{}}
for name,package in PACKAGES.items():
    skeleton=latest(package); framework=latest(FRAMEWORKS[name])
    source=skeleton['source']; repo=source['url'].removesuffix('.git').removeprefix('https://github.com/')
    url=f"https://codeload.github.com/{repo}/tar.gz/{source['reference']}"
    data=urllib.request.urlopen(url,timeout=60).read()
    manifest['apps'][name]={'skeleton':package,'skeleton_version':skeleton['version'],'commit':source['reference'],'archive_url':url,'sha256':hashlib.sha256(data).hexdigest(),'framework':FRAMEWORKS[name],'version':framework['version']}
    print(name,skeleton['version'],FRAMEWORKS[name],framework['version'],flush=True)
(ROOT/'sources.json').write_text(json.dumps(manifest,indent=2)+'\n')
