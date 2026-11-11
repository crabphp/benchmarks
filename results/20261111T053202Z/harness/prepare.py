"""Build a self-contained context from checksummed public source archives."""
from pathlib import Path
import hashlib, io, json, os, shutil, tarfile, urllib.request
ROOT=Path(__file__).resolve().parent
CONTEXT=Path(os.environ['BENCH_CONTEXT'])
SOURCES=json.loads((ROOT/'sources.json').read_text())
if CONTEXT.exists(): shutil.rmtree(CONTEXT)
CONTEXT.mkdir(parents=True)
for name in ['common','crab','webman','hyperf','spiral','symfony','laravel','laravel-octane','tempest','reactphp','amphp','loadgen','mysql']:
    shutil.copytree(ROOT/name,CONTEXT/name)
cache=ROOT/'.work/downloads'; cache.mkdir(parents=True,exist_ok=True)
for name,pin in SOURCES['apps'].items():
    archive=cache/(pin['sha256']+'.tar.gz')
    if not archive.exists(): archive.write_bytes(urllib.request.urlopen(pin['archive_url'],timeout=60).read())
    data=archive.read_bytes()
    if hashlib.sha256(data).hexdigest()!=pin['sha256']: raise RuntimeError('Source checksum failed: '+name)
    dest=CONTEXT/(name+'-source');dest.mkdir()
    with tarfile.open(fileobj=io.BytesIO(data)) as tf:
        prefix=tf.getmembers()[0].name+'/'
        for member in tf.getmembers():
            if not member.name.startswith(prefix): continue
            member.name=member.name[len(prefix):]
            if member.name: tf.extract(member,dest,filter='data')
    # HTTP libraries have no application skeleton; our explicit adapters supply it.
    if name in ['reactphp', 'amphp']:
        shutil.rmtree(dest)
        dest.mkdir()
        shutil.copy2(ROOT/name/'composer.json', dest/'composer.json')
    composer=json.loads((dest/'composer.json').read_text())
    composer.pop('require-dev',None);composer.pop('autoload-dev',None)
    composer['minimum-stability']='dev' if name == 'spiral' else 'stable';composer['prefer-stable']=True
    composer['require'][pin['framework']]=pin['version'].removeprefix('v')
    composer['config']=composer.get('config',{})|{'platform':{'php':'8.5.0'}}
    composer.pop('repositories',None)
    if name=='crab':
        composer['require'].pop('crabphp/engine',None)
    if name=='webman':
        composer['require'].update({'webman/database':'^2.1','webman/validation':'^2.2'})
    if name=='hyperf': composer['require']['hyperf/validation']='~3.2.0'
    if name=='laravel': composer['require']['laravel/octane']='2.23.0'
    if name=='symfony':
        for pkg in ['console','dotenv','framework-bundle','property-access','runtime','serializer','validator','yaml']:
            composer['require']['symfony/'+pkg]='8.1.*'
        composer['require'].update({'doctrine/doctrine-bundle':'^3.0','doctrine/dbal':'^4.0'})
        composer.setdefault('extra',{}).setdefault('symfony',{})['require']='8.1.*'
    (dest/'composer.json').write_text(json.dumps(composer,indent=2)+'\n')
    # A frozen manifest accompanies each lock, so installed dependency graphs match exactly.
    overlay=ROOT/('laravel-octane' if name=='laravel' else name)
    if (overlay/'composer.lock').exists():
        for filename in ['composer.json','composer.lock']:
            shutil.copy2(overlay/filename,dest/filename)
    print('Prepared',name,pin['version'],flush=True)
manifest={str(p.relative_to(CONTEXT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(CONTEXT.rglob('*')) if p.is_file()}
(Path(os.environ['BENCH_RESULTS'])/'source-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')

# Retain the exact harness implementation used, even before a source commit exists.
harness=Path(os.environ['BENCH_RESULTS'])/'harness'
harness.mkdir()
for filename in ['runner.py','prepare.py','audit.py','run.sh','compose.yaml','sources.json','images.env']:
    shutil.copy2(ROOT/filename,harness/filename)
(harness/'manifest.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in harness.iterdir()},indent=2)+'\n')
