"""Replace only four flange meshes, preserving native animation and surface bakes."""
import bpy,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from cooling_interfaces import build_flange,SOURCE,STATUS
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'outputs/MAZ543A_Cooling_Master.blend'))
for kind in ['lower','upper']:
    for i in range(2):
        name=f'COOL_lower_cardan_flange_{i}' if kind=='lower' else f'COOL_upper_input_flange_{i}'
        old=bpy.data.objects[name];parent=old.parent;props=dict(old.items());cols=list(old.users_collection)
        bpy.data.objects.remove(old,do_unlink=True)
        o=build_flange(name,parent,bpy.data.materials['D12_forged_steel'],*( (.174,.184,.011) if kind=='lower' else (.166,.175,.009)))
        for k,v in props.items():o[k]=v
        o['sourceId']=SOURCE;o['dimensionStatus']=STATUS
        for c in list(o.users_collection):c.objects.unlink(o)
        for c in cols:c.objects.link(o)
root=bpy.data.objects['S543_COOLING']
report=[{'name':o.name,'role':o.get('coolingRole'),'source':o.get('sourceId'),'dimensions':o.get('dimensionStatus')} for o in root.children_recursive if o.type in ['MESH','CURVE']]
(ROOT/'outputs/cooling-parts-register.json').write_text(json.dumps(report,indent=2))
bpy.context.scene.frame_set(0)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'outputs/MAZ543A_Cooling_Master.blend'),compress=True)
exec(compile((ROOT/'scripts/export-cooling-native.py').read_text(),str(ROOT/'scripts/export-cooling-native.py'),'exec'))
