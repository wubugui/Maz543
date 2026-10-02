"""Restore the exact65read-only probe records; never invoke Blender."""
import argparse,hashlib,importlib.util,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--package',type=Path,default=Path(__file__).resolve().parent);p.add_argument('--out',type=Path,required=True);a=p.parse_args();assert not a.out.exists()
sha=lambda b:hashlib.sha256(b).hexdigest()
def relative(s):
 q=Path(s);assert not q.is_absolute() and '..' not in q.parts and q.parts;return q
mb=(a.package/'FREEZE-MANIFEST.json').read_bytes();assert sha(mb)=='a9520a3da99b872d67e0bba2bc40f56c5ebfe58646e4d42a360e7e5bb6c7de46';manifest=json.loads(mb);idx=json.loads((a.package/'package-index.json').read_bytes());assert idx['source_manifest_sha256']==sha(mb)
cp=a.package/'pack-wheel-interface-evidence.py';assert sha(cp.read_bytes())==idx['codec_sha256']=='2334d0734b5e6edbd289692be6d4c8da50daba4b3f770142400971c75091a11d'
spec=importlib.util.spec_from_file_location('pinned_codec',cp);codec=importlib.util.module_from_spec(spec);spec.loader.exec_module(codec);bundle=json.loads(codec.restore(a.package/'records-table'))
expected={r['path']:r for r in manifest['files']};assert len(expected)==len(idx['records'])==65;restored={}
for r in idx['records']:
 name=r['path'];relative(name);assert name in expected and name not in restored;assert {k:r[k] for k in ['path','bytes','sha256']}==expected[name]
 if r['storage']=='json-table':raw=(json.dumps(bundle.pop(name),indent=2,ensure_ascii=True,allow_nan=False)+'\n').encode()
 else:assert r['storage']=='direct-text';raw=(a.package/relative(r['stored_path'])).read_bytes()
 assert len(raw)==r['bytes'] and sha(raw)==r['sha256'],name;raw.decode();restored[name]=raw
assert not bundle and sum(len(b) for b in restored.values())==1094662
a.out.mkdir(parents=True,exist_ok=False)
for name,raw in [*restored.items(),('FREEZE-MANIFEST.json',mb)]:
 q=a.out/relative(name);q.parent.mkdir(parents=True,exist_ok=True)
 with q.open('xb') as f:f.write(raw)
print(json.dumps({'files_restored':65,'bytes_restored':1094662,'extra_source_manifest_exact':True,'asset_bytes':0}))
