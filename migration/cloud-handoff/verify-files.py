"""Verify included original files after Git LFS pull; no external packages needed."""
import pathlib,json,hashlib,sys
root=pathlib.Path(__file__).resolve().parents[2]
m=json.loads((root/'migration/cloud-handoff/MANIFEST.json').read_text(encoding='utf8'))
all_files='--all' in sys.argv
prefixes=[a for a in sys.argv[1:] if a!='--all']
current={'testcar/outputs/MAZ543A_Master.blend','testcar/outputs/MAZ543A_Textured.blend'}
chosen=[f for f in m['files'] if all_files or (any(f['path'].startswith(p) for p in prefixes) if prefixes else f['path'] in current or f['path'].startswith(('testcar/public/','external/')))]
fail=[];count=0;total=0
for f in chosen:
 p=root/f['path'];h=hashlib.sha256()
 try:
  with p.open('rb') as stream:
   for b in iter(lambda:stream.read(4*1024*1024),b''):h.update(b)
  if p.stat().st_size!=f['size'] or h.hexdigest()!=f['sha256']:fail.append({'path':f['path'],'reason':'size/hash mismatch (possibly an unresolved LFS pointer)'})
 except OSError as e:fail.append({'path':f['path'],'reason':str(e)})
 count+=1;total+=f['size']
print(json.dumps({'files':count,'expectedBytes':total,'failures':fail},indent=2))
sys.exit(1 if fail else 0)
