"""Restore the exact native file from canonical raw Git parts, without Blender.

Never overwrites an existing output. All parts and the complete hash are checked
before creating an output; the write pass independently checks the full hash.
"""
import argparse,hashlib,json,os,tempfile
from pathlib import Path

SCHEMA='MAZ_NATIVE_BLEND_BINARY_PARTS_V1'

def checked_manifest(path):
    manifest=json.loads(path.read_text())
    if manifest.get('schema')!=SCHEMA:raise ValueError('Unsupported manifest schema')
    if not isinstance(manifest.get('bytes'),int) or manifest['bytes']<=0:raise ValueError('Invalid native size')
    if not isinstance(manifest.get('sha256'),str) or len(manifest['sha256'])!=64:raise ValueError('Invalid native digest')
    rows=manifest.get('parts');offset=0;seen=set()
    if not isinstance(rows,list) or not rows:raise ValueError('Missing ordered parts')
    for index,row in enumerate(rows):
        name=row['path'];rel=Path(name)
        if rel.is_absolute() or '..' in rel.parts or '\\' in name or str(rel)!=name:raise ValueError('Unsafe part path')
        if rel.parts!=('source-parts',f'part-{index:03d}.bin'):raise ValueError('Unexpected part name or order')
        if name in seen or row['index']!=index or row['offset']!=offset:raise ValueError('Missing, duplicate or reordered part')
        if not isinstance(row['bytes'],int) or not 0<row['bytes']<=manifest['part_size_max_bytes']:raise ValueError('Invalid part size')
        if index<len(rows)-1 and row['bytes']!=manifest['part_size_max_bytes']:raise ValueError('Short nonfinal part')
        for key,length in [('sha256',64),('git_blob_sha1',40)]:
            if len(row[key])!=length or any(c not in '0123456789abcdef' for c in row[key]):raise ValueError('Invalid digest')
        seen.add(name);offset+=row['bytes']
    if offset!=manifest['bytes']:raise ValueError('Incomplete native length')
    return manifest

def validate_parts(path,manifest):
    whole=hashlib.sha256();total=0
    for row in manifest['parts']:
        part=path.parent/row['path']
        if part.is_symlink() or not part.is_file() or part.stat().st_size!=row['bytes']:raise ValueError('Missing or wrong-sized part: '+row['path'])
        one=hashlib.sha256();git=hashlib.sha1(('blob '+str(row['bytes'])+'\0').encode())
        with part.open('rb') as f:
            while True:
                b=f.read(1048576)
                if not b:break
                one.update(b);git.update(b);whole.update(b);total+=len(b)
        if one.hexdigest()!=row['sha256'] or git.hexdigest()!=row['git_blob_sha1']:raise ValueError('Part digest mismatch: '+row['path'])
    if total!=manifest['bytes'] or whole.hexdigest()!=manifest['sha256']:raise ValueError('Complete native digest mismatch')
    return total,whole.hexdigest()

def restore(manifest_path,output):
    manifest_path=Path(manifest_path).resolve();output=Path(output)
    if output.exists() or output.is_symlink():raise FileExistsError('Output already exists; choose a new unused file')
    manifest=checked_manifest(manifest_path);validate_parts(manifest_path,manifest)
    output.parent.mkdir(parents=True,exist_ok=True)
    whole=hashlib.sha256();total=0;temporary=None
    # A verified temporary file is linked to the final name atomically without
    # replacing an existing file. Failed/partial writes never acquire .blend.
    try:
        with tempfile.NamedTemporaryFile(dir=output.parent,prefix=output.name+'.partial-',delete=False) as f:
            temporary=Path(f.name)
            for row in manifest['parts']:
                with (manifest_path.parent/row['path']).open('rb') as source:
                    while True:
                        b=source.read(1048576)
                        if not b:break
                        f.write(b);whole.update(b);total+=len(b)
            f.flush();os.fsync(f.fileno())
        if total!=manifest['bytes'] or whole.hexdigest()!=manifest['sha256']:raise ValueError('Restoration write differs from verified input')
        os.link(temporary,output)
    finally:
        if temporary is not None:temporary.unlink(missing_ok=True)
    return {'status':'EXACT_NATIVE_BYTES_RESTORED','output':str(output.resolve()),'bytes':total,'sha256':whole.hexdigest(),'parts':len(manifest['parts'])}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--manifest',type=Path,default=Path(__file__).with_name('manifest.json'));p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    print(json.dumps(restore(a.manifest,a.output),indent=2))
