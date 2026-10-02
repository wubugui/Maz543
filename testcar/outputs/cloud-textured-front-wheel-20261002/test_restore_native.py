"""Small integrity controls for the canonical native-byte restorer."""
import hashlib,importlib.util,json,tempfile
from pathlib import Path
spec=importlib.util.spec_from_file_location('restore_native',Path(__file__).with_name('restore_native.py'));module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
PAYLOAD=bytes(range(256))+b'final native-byte tail\x00\xff'
def fixture(root):
    (root/'source-parts').mkdir();rows=[]
    for i,off in enumerate(range(0,len(PAYLOAD),64)):
        data=PAYLOAD[off:off+64];name=f'source-parts/part-{i:03d}.bin';(root/name).write_bytes(data)
        rows.append({'index':i,'path':name,'offset':off,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'git_blob_sha1':hashlib.sha1(('blob '+str(len(data))+'\0').encode()+data).hexdigest()})
    m={'schema':module.SCHEMA,'bytes':len(PAYLOAD),'sha256':hashlib.sha256(PAYLOAD).hexdigest(),'part_size_max_bytes':64,'parts':rows};(root/'manifest.json').write_text(json.dumps(m));return m
results=[]
for case in ['complete','missing','corrupt','reordered','wrong_whole_hash','unsafe_path','existing_output']:
    with tempfile.TemporaryDirectory() as tmp:
        root=Path(tmp);m=fixture(root);out=root/'restored.blend'
        if case=='missing':(root/m['parts'][-1]['path']).unlink()
        elif case=='corrupt':p=root/m['parts'][0]['path'];p.write_bytes(b'X'+p.read_bytes()[1:])
        elif case=='reordered':m['parts'][0],m['parts'][1]=m['parts'][1],m['parts'][0]
        elif case=='wrong_whole_hash':m['sha256']='0'*64
        elif case=='unsafe_path':m['parts'][0]['path']='../outside.bin'
        elif case=='existing_output':out.write_bytes(b'KEEP_EXISTING')
        (root/'manifest.json').write_text(json.dumps(m))
        failed=False
        try:result=module.restore(root/'manifest.json',out)
        except (ValueError,FileExistsError):failed=True
        if case=='complete':assert not failed and out.read_bytes()==PAYLOAD and result['sha256']==hashlib.sha256(PAYLOAD).hexdigest()
        else:assert failed and (out.read_bytes()==b'KEEP_EXISTING' if case=='existing_output' else not out.exists())
        assert not list(root.glob('*.partial-*'))
        results.append({'case':case,'passed':True})
print(json.dumps({'status':'PASS','controls':results},indent=2))
