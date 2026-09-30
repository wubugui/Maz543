"""Save a separate candidate without reference image pixels and verify geometry.

The packed local research master is preserved byte-for-byte. This script never
opens any production master. It neither publishes nor pushes anything.
"""
import bpy, json, hashlib, struct
from pathlib import Path
OUT=Path(__file__).resolve().parent
SOURCE=OUT/'FG16_Native_Structural_Study.blend'
DEST=OUT/'FG16_Native_Structural_Study_SHAREABLE.blend'
def file_sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
source_sha=file_sha(SOURCE)
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
def signatures():
    result={}
    for scene in bpy.data.scenes:
        bpy.context.window.scene=scene;scene.frame_set(1);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
        for obj in scene.objects:
            if obj.type not in {'MESH','CURVE','FONT'}:continue
            e=obj.evaluated_get(dg);m=e.to_mesh();h=hashlib.sha256()
            for row in obj.matrix_world:h.update(struct.pack('<4f',*row))
            for v in m.vertices:h.update(struct.pack('<3f',*v.co))
            for p in m.polygons:
                h.update(struct.pack('<I',len(p.vertices)));h.update(struct.pack('<'+'I'*len(p.vertices),*p.vertices))
            result[scene.name+'/'+obj.name]={'geometry_transform_sha256':h.hexdigest(),'vertices':len(m.vertices),'polygons':len(m.polygons)}
            e.to_mesh_clear()
    return result
before=signatures()
metadata=[]
for im in list(bpy.data.images):
    if im.name.startswith('1977-original'):
        metadata.append({'filename':im.name,'source_url':im.get('source_url'),'title':im.get('source_title'),'edition':im.get('source_edition'),'source_sha256':im.get('source_sha256'),'rights_status':im.get('rights_status'),'scan_pixels_in_this_file':False})
    bpy.data.images.remove(im)
text=bpy.data.texts.get('SOURCE_REFERENCE_METADATA.json') or bpy.data.texts.new('SOURCE_REFERENCE_METADATA.json');text.clear();text.write(json.dumps(metadata,ensure_ascii=False,indent=2))
text=bpy.data.texts.new('SHAREABLE_EDITION.txt');text.write('This is a separate study candidate with no original manual page pixels. Editable native geometry is identical to the packed local research master. Original source URL/edition/page filename/hash remain in SOURCE_REFERENCE_METADATA.json. No public publication occurred in this task. Assembly connections and all vehicle acceptance gates remain OPEN.\n')
bpy.context.window.scene=bpy.data.scenes['FG16_ASSEMBLED_STUDY']
bpy.ops.wm.save_as_mainfile(filepath=str(DEST),compress=True)
bpy.ops.wm.open_mainfile(filepath=str(DEST))
after=signatures()
report={'packed_local_source_sha256_before':source_sha,'packed_local_source_sha256_after':file_sha(SOURCE),'local_source_unchanged':source_sha==file_sha(SOURCE),'shareable_file':DEST.name,'shareable_bytes':DEST.stat().st_size,'shareable_sha256':file_sha(DEST),'source_reference_metadata':metadata,'image_datablocks_after_reopen':len(bpy.data.images),'geometry_transforms_identical_after_reopen':before==after,'evaluated_object_instances_checked':len(before),'scene_names':[s.name for s in bpy.data.scenes],'signatures':after,'publication':'NOT PUBLISHED; candidate only, no production promotion'}
(OUT/'shareable-readback.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
assert before==after
assert len(bpy.data.images)==0
assert source_sha==file_sha(SOURCE)
print('FG16_SHAREABLE_READBACK',json.dumps({k:report[k] for k in ['shareable_bytes','geometry_transforms_identical_after_reopen','image_datablocks_after_reopen','local_source_unchanged']}),flush=True)
