"""Recover exact ordinary JSON diagnostic records from readable shared tables."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

p=argparse.ArgumentParser()
p.add_argument('--codec',type=Path,required=True)
p.add_argument('--package',type=Path,required=True)
p.add_argument('--out',type=Path,required=True)
a=p.parse_args()
meta=json.loads((a.package/'source-records.json').read_bytes())
sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha(a.codec.read_bytes())==meta['table_codec_sha256']
spec=importlib.util.spec_from_file_location('wheel_interface_codec',a.codec)
codec=importlib.util.module_from_spec(spec);spec.loader.exec_module(codec)
bundle=json.loads(codec.restore(a.package/'diagnostic-tables'))
expected={r['path']:r for r in meta['original_records']}
assert set(bundle)==set(expected)
outputs={}
for name,document in bundle.items():
    assert Path(name).name==name
    raw=(json.dumps(document,indent=2)+'\n').encode()
    assert len(raw)==expected[name]['bytes'] and sha(raw)==expected[name]['sha256']
    outputs[name]=raw
assert not a.out.exists()
a.out.mkdir(parents=True)
for name,raw in outputs.items():
    with (a.out/name).open('xb') as f:f.write(raw)
print(json.dumps({'restored_files':len(outputs),'original_bytes':sum(len(b) for b in outputs.values())}))
