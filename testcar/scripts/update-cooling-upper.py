"""Rebuild only the upper modules, retaining the accepted lower surface bake."""
import bpy,bmesh,json,math,sys,ast
from pathlib import Path
from math import sin,cos,pi,sqrt
from mathutils import Vector,Matrix
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from d12_asset import engine_descendants
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'outputs/MAZ543A_Cooling_Master.blend'));root=bpy.data.objects['S543_COOLING'];REG=[]
for i in range(2):
    old=bpy.data.objects.get(f'COOL_upper_drive_{i}')
    if old:
        for o in list(old.children_recursive)+[old]:bpy.data.objects.remove(o,do_unlink=True)
for key,name in {'CAST':'D12_cast_aluminium','STEEL':'D12_forged_steel','POLISH':'D12_machined_steel','BRONZE':'D12_bearing_bronze','RUBBER':'D12_hose_rubber','GASKET':'D12_gasket','resin':'COOL_textolite'}.items():globals()[key]=bpy.data.materials[name]
def functions(path,names):
    tree=ast.parse(path.read_text());selected=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names];exec(compile(ast.Module(body=selected,type_ignores=[]),str(path),'exec'),globals())
functions(ROOT/'scripts/blender-d12.py',{'C','empty','mat','tag','mesh','prism','box','lathe','cylinder','ring','pipe'})
functions(ROOT/'scripts/blender-cooling.py',{'ct','E'})
DATA=json.loads((ROOT/'work/cooling-poses.json').read_text());S=DATA['spec']
exec(compile((ROOT/'scripts/cooling-upper-detail.py').read_text(),str(ROOT/'scripts/cooling-upper-detail.py'),'exec'))
for o in root.children_recursive:
    if o.type!='MESH' or not o.get('upperGearbox'):continue
    bm=bmesh.new();bm.from_mesh(o.data);bm.edges.ensure_lookup_table();sharp=[e.calc_face_angle(0)>.52 for e in bm.edges];bm.free()
    for edge,val in zip(o.data.edges,sharp):edge.use_edge_sharp=val
    for face in o.data.polygons:
        if max(abs(v) for v in face.normal)>.99999:face.use_smooth=False
col=bpy.data.collections['S543_COOLING']
for o in root.children_recursive:
    for oldcol in list(o.users_collection):oldcol.objects.unlink(o)
    col.objects.link(o)
for name in DATA['frames'][0]['pose']:
    if not name.startswith('COOL_upper_'):continue
    o=bpy.data.objects[name]
    for frame in DATA['frames']:
        p=frame['pose'][name];o.location=C(p['p']);o.rotation_euler=(p['rx'],0,0)
        o.keyframe_insert(data_path='location',frame=frame['frame']);o.keyframe_insert(data_path='rotation_euler',frame=frame['frame'])
    for fc in o.animation_data.action.fcurves:
        for key in fc.keyframe_points:key.interpolation='LINEAR'
bpy.context.scene.frame_set(0)
functions(ROOT/'scripts/cooling-lower-surfaces.py',{'bake_cooling_surfaces'})
bake_cooling_surfaces('COOL_upper_cast_alloy','upperGearbox','COOL_upper_cast')
report=[{'name':o.name,'role':o.get('coolingRole'),'source':o.get('sourceId'),'dimensions':o.get('dimensionStatus')} for o in root.children_recursive if o.type in ['MESH','CURVE']]
(ROOT/'outputs/cooling-parts-register.json').write_text(json.dumps(report,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'outputs/MAZ543A_Cooling_Master.blend'),compress=True)
exec(compile((ROOT/'scripts/export-cooling-native.py').read_text(),str(ROOT/'scripts/export-cooling-native.py'),'exec'))
