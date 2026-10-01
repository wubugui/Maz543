"""Compare saved appended device with its independent native source."""
import ast
import bpy
import hashlib
import json
import numpy as np
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/cloud-va180-panel-fit-20261001'
build=json.loads((OUT/'build.json').read_text())
DEVICE=ROOT/'outputs/cloud-va180-face-study-20261001/iteration-04/study.blend'
TARGET=OUT/'MAZ543A_Master.blend'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(DEVICE)==build['device_sha256'] and sha(TARGET)==build['candidate_sha256']
tree=ast.parse((ROOT/'scripts/build-va180-panel-fit.py').read_text())
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in {'geometry','state'}],type_ignores=[]),'snapshots','exec'))
def fonts(o):
    if o.type!='FONT':return None
    return {'size':o.data.size,'extrude':o.data.extrude,'resolution_u':o.data.resolution_u,
            'align_x':o.data.align_x,'align_y':o.data.align_y,
            'packed_font_sha256':hashlib.sha256(o.data.font.packed_file.data).hexdigest()}
bpy.ops.wm.open_mainfile(filepath=str(DEVICE));bpy.context.view_layer.update()
old={n:{'state':state(bpy.data.objects[n]),'font':fonts(bpy.data.objects[n])} for n in build['device_object_name_map']}
bpy.ops.wm.open_mainfile(filepath=str(TARGET));bpy.context.scene.frame_set(0);bpy.context.view_layer.update()
root=np.array(bpy.data.objects['VA180 PARTIAL — B4 PHOTO-FORM REVIEW'].matrix_world)
fail=[];rows=[]
for original,renamed in build['device_object_name_map'].items():
    obj=bpy.data.objects.get(renamed)
    if obj is None:fail.append([original,'missing']);continue
    prior=old[original]['state'];now=state(obj)
    for key in ['type','authored_geometry_uv','hide_render','materials']:
        if now[key]!=prior[key]:fail.append([original,key])
    expected_parent=build['device_object_name_map'][prior['parent']] if prior['parent'] else 'VA180 PARTIAL — B4 PHOTO-FORM REVIEW'
    if now['parent']!=expected_parent:fail.append([original,'parent'])
    error=float(np.max(np.abs(np.array(now['world'])-root@np.array(prior['world']))))
    if error>1e-6:fail.append([original,'world',error])
    if fonts(obj)!=old[original]['font']:fail.append([original,'font'])
    rows.append({'source':original,'appended':renamed,'world_matrix_max_error':error})
report={'source_device_sha256':build['device_sha256'],'candidate_sha256':build['candidate_sha256'],
        'compared_objects':len(rows),'failures':fail,'rows':rows,
        'scope':'All 28 appended objects: authored geometry/UV, parent semantics, fitted root world transform, material slot names and hide_render; all text size/font payload. Does not certify modifier RNA, material node internals or factory dimensions.',
        'saved_blend':False}
assert sha(DEVICE)==build['device_sha256'] and sha(TARGET)==build['candidate_sha256']
(OUT/'appended-identity.json').write_text(json.dumps(report,indent=2)+'\n')
print('APPENDED_IDENTITY',json.dumps({'objects':len(rows),'failures':fail}))
assert not fail
