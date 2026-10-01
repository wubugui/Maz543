"""Independent textured GLB export plus actual native geometry/pose references."""
import bpy
import hashlib
import json
import struct
from pathlib import Path
from mathutils import Matrix

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'outputs/cloud-va180-textured-20261001/MAZ543A_Textured.blend'
EXPECTED='6e406ecadc638130a631e12accebcd9d46de7bdc7c85ca582f0f10d28babe266'
OUT=ROOT/'work/cloud-va180-web-20261001';OUT.mkdir(parents=True,exist_ok=True)
assert not (OUT/'native-export.glb').exists()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();assert sha(SOURCE)==EXPECTED
readback=json.loads((SOURCE.parent/'readback.json').read_text())
assert readback['candidate_sha256']==EXPECTED and not readback['identity_failures']
bpy.ops.wm.open_mainfile(filepath=str(SOURCE));bpy.context.scene.frame_set(0);bpy.context.view_layer.update()
excluded={'D12A_525A','S543_COOLING','S543_SUSPENSION','S543_STARTING','C5_STARTER','C5_FLYWHEEL_RING','MZN_PREOIL','STARTING_ENGINE_MOUNT','S543_CARDAN','S543_TRANSMISSION'}
def allowed(obj):
    if obj.hide_render or obj.name.startswith(('SOURCE_','ARCHIVE_','CUTTER_')):return False
    while obj:
        if obj.name in excluded:return False
        obj=obj.parent
    return True
vehicle=bpy.data.objects['MAZ543_REFERENCE_CHASSIS']
selected=[vehicle]+[o for o in vehicle.children_recursive if allowed(o)]
selected_names={o.name for o in selected}
assert not ({'cab_0066','cab_0067','cab_0068'} & selected_names)
assert all(n not in selected_names for n in json.loads((SOURCE.parent/'build.json').read_text())['old_proxy_archive'])
roots=[bpy.data.objects[n] for n in ['LEFT DISPLAY ROOT — not vehicle datum','RIGHT DISPLAY ROOT — not vehicle datum']]
panel_names={o.name for r in roots for o in [r]+list(r.children_recursive)}
reference_names=panel_names|{'cab_0064','cab_0029','cab_0030','cab_0031','BL_Left_driver_steering_column_retained'}
rows=[];offset=0
conversion=Matrix(((1,0,0,0),(0,0,1,0),(0,-1,0,0),(0,0,0,1)))
node_poses={}
with (OUT/'native-world-reference.bin').open('wb') as stream:
    for o in sorted(selected,key=lambda o:o.name):
        if o.name in reference_names or o.name=='cab_pivot_004':
            node_poses[o.name]={'parent':o.parent.name if o.parent else None,
                               'local_gltf_matrix_rows':[list(r) for r in conversion@o.matrix_local@conversion.inverted()],
                               'world_gltf_matrix_rows':[list(r) for r in conversion@o.matrix_world@conversion.inverted()]}
        if o.name not in reference_names or o.type not in {'MESH','CURVE','FONT'}:continue
        ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();m.calc_loop_triangles()
        pts=[ev.matrix_world@v.co for v in m.vertices]
        for p in pts:stream.write(struct.pack('<fff',p.x,p.z,-p.y))
        rows.append({'name':o.name,'vertices':len(pts),'triangles':len(m.loop_triangles),'byteOffset':offset,'source_type':o.type})
        offset+=12*len(pts);ev.to_mesh_clear()
assert 'cab_0064' in {r['name'] for r in rows}
assert sum(r['source_type']=='FONT' and r['name'].startswith('VA180 B4 /') for r in rows)==7
# Export-only native conversion and triangulation. The source .blend remains
# untouched; references above describe its original evaluated geometry.
bpy.ops.object.select_all(action='DESELECT')
convert_names=[o.name for o in selected if o.type in {'CURVE','FONT','SURFACE'}]
if convert_names:
    for name in convert_names:
        o=bpy.data.objects[name];o.hide_set(False);o.select_set(True)
    bpy.context.view_layer.objects.active=bpy.data.objects[convert_names[0]]
    bpy.ops.object.convert(target='MESH',keep_original=False)
selected=[bpy.data.objects[name] for name in selected_names]
triangulated=[]
for o in selected:
    if o.type!='MESH':continue
    ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh()
    ngons=0;nonplanarity=0.0;degenerate=0
    normal_matrix=ev.matrix_world.to_3x3().inverted().transposed()
    for p in m.polygons:
        if len(p.vertices)<=4:continue
        ngons+=1;normal=normal_matrix@p.normal
        if normal.length<1e-12:degenerate+=1;continue
        normal.normalize();centre=ev.matrix_world@p.center
        nonplanarity=max(nonplanarity,max(abs(normal.dot(ev.matrix_world@m.vertices[i].co-centre)) for i in p.vertices))
    ev.to_mesh_clear()
    if ngons:
        modifier=o.modifiers.new('EXPORT ONLY native n-gon triangulation','TRIANGULATE')
        modifier.min_vertices=5;modifier.ngon_method='BEAUTY'
        if hasattr(modifier,'keep_custom_normals'):modifier.keep_custom_normals=True
        triangulated.append({'object':o.name,'evaluated_ngons_before':ngons,'world_ngon_nonplanarity_m':nonplanarity,'degenerate_ngons':degenerate})
bpy.context.view_layer.update()
for row in triangulated:
    ev=bpy.data.objects[row['object']].evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh()
    assert not any(len(p.vertices)>4 for p in m.polygons),row['object'];ev.to_mesh_clear()
bpy.ops.object.select_all(action='DESELECT')
for o in selected:o.hide_set(False);o.select_set(True)
bpy.context.view_layer.objects.active=vehicle
bpy.ops.export_scene.gltf(filepath=str(OUT/'native-export.glb'),export_format='GLB',use_selection=True,
    export_apply=True,export_yup=True,export_tangents=True,export_extras=True,export_animations=False,
    export_draco_mesh_compression_enable=True,export_draco_mesh_compression_level=6,export_draco_position_quantization=18)
assert sha(SOURCE)==EXPECTED
(OUT/'native-world-reference.json').write_text(json.dumps({'source_sha256':EXPECTED,'parts':rows,'node_poses':node_poses,
    'coordinates':'glTF Y-up world; native Blender (x,y,z) mapped to (x,z,-y)',
    'bytes':offset,'selected_object_names':sorted(selected_names),'export_only_converted_objects':convert_names,
    'export_only_native_triangulation':triangulated,'source_saved':False,
    'scope':'Actual evaluated changed/new cab geometry, all retained four seat bases, partial font outlines and native rest poses. Static button pose only; no browser acceptance.'},indent=2)+'\n')
print('VA180_CAB_NATIVE_EXPORT',len(selected),len(rows),(OUT/'native-export.glb').stat().st_size,flush=True)
