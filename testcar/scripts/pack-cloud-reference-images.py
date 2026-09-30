"""Pack verified retained exterior references into a separate candidate copy."""
import bpy,os,json,hashlib
from pathlib import Path
repo=Path(__file__).resolve().parents[2]
source=Path(os.environ['MAZ_CANDIDATE_DIR']).resolve()
dest=Path(os.environ['MAZ_PORTABLE_DIR']).resolve()
if source==dest:raise RuntimeError('Preserve candidate input; choose a separate output directory')
dest.mkdir(parents=True,exist_ok=True)
manifest=json.loads((repo/'migration/cloud-handoff/MANIFEST.json').read_text())
registered={f['path']:f for f in manifest['files']}
report=[]
for filename in ['MAZ543A_Master.blend','MAZ543A_Textured.blend']:
 bpy.ops.wm.open_mainfile(filepath=str(source/filename));rows=[]
 for im in bpy.data.images:
  if im.source!='FILE' or im.packed_file:continue
  path=repo/'external/maz543-references'/im.name
  rel=path.relative_to(repo).as_posix()
  if rel not in registered:raise RuntimeError('Unknown unembedded source image: '+im.name)
  data=path.read_bytes();entry=registered[rel];digest=hashlib.sha256(data).hexdigest()
  assert len(data)==entry['size'] and digest==entry['sha256'],'Reference source integrity mismatch'
  im.filepath=str(path);im.reload();im.pack()
  assert im.packed_file and tuple(im.size)!=(0,0),'Image packing failed'
  packed=bytes(im.packed_file.data)
  assert hashlib.sha256(packed).hexdigest()==digest,'Packed image differs from retained source'
  im.filepath='//references/'+im.name
  rows.append({'image':im.name,'source':rel,'sha256':digest,'bytes':len(packed),'size':list(im.size)})
 bpy.ops.wm.save_as_mainfile(filepath=str(dest/filename),compress=True)
 bpy.ops.wm.open_mainfile(filepath=str(dest/filename))
 for r in rows:
  im=bpy.data.images[r['image']]
  assert im.packed_file and hashlib.sha256(bytes(im.packed_file.data)).hexdigest()==r['sha256'],'Packed image read-back mismatch'
 report.append({'file':filename,'packedAndReadBack':rows,'objects':len(bpy.data.objects)})
(dest/'reference-pack-verification.json').write_text(json.dumps({'files':report,'scope':'Reference portability only; source dimensions and mechanical/visual acceptance unchanged'},indent=2))
print('REFERENCE_PACK_PASS',[(r['file'],len(r['packedAndReadBack'])) for r in report])
