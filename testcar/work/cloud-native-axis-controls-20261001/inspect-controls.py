import bpy,json,hashlib
from pathlib import Path
R=Path('/workspace/scratch/a29d03198654');S=R/'Maz543/testcar/outputs/cloud-va180-panel-fit-20261001/MAZ543A_Master.blend';O=R/'maz-native-axis-controls-20261001'
assert hashlib.sha256(S.read_bytes()).hexdigest()=='8e962d6dc2565974be8a0e96930606599ddbf6098780951dc96cbb9e13e3fd70'
assert bpy.app.version[:3]==(4,5,13)
bpy.ops.wm.open_mainfile(filepath=str(S));bpy.context.scene.frame_set(0);bpy.context.view_layer.update()
def simple(v):
 if isinstance(v,(str,bool,int,float)) or v is None:return v
 if hasattr(v,'name_full'):return v.name_full
 try:return [simple(x) for x in v]
 except:return str(v)
def rna(o):return {p.identifier:simple(getattr(o,p.identifier)) for p in o.bl_rna.properties if p.identifier!='rna_type'}
result={'version':bpy.app.version_string,'autoexec':bpy.context.preferences.filepaths.use_scripts_auto_execute,'hinges':[]}
for n in ['cab_pivot_002','cab_pivot_003','cab_pivot_006','cab_pivot_007']:
 h=bpy.data.objects[n];result['hinges'].append({'name':n,'type':h.type,'matrix_basis':simple(h.matrix_basis),'matrix_world':simple(h.matrix_world),'parent_inverse':simple(h.matrix_parent_inverse),'rotation_mode':h.rotation_mode,'rotation_euler':simple(h.rotation_euler),'rotation_quaternion':simple(h.rotation_quaternion),'scale':simple(h.scale),'location':simple(h.location),'delta_location':simple(h.delta_location),'delta_rotation_euler':simple(h.delta_rotation_euler),'delta_rotation_quaternion':simple(h.delta_rotation_quaternion),'delta_scale':simple(h.delta_scale),'parent_type':h.parent_type,'parent':h.parent.name if h.parent else None,'parent_rna':rna(h.parent) if h.parent else None,'constraints':[rna(c) for c in h.constraints],'custom_properties':{k:simple(h[k]) for k in h.keys()},'animation_data':rna(h.animation_data) if h.animation_data else None,'children':[x.name for x in h.children_recursive]})
(O/'inspect-controls.json').write_text(json.dumps(result,indent=2)+'\n'); print('INSPECTION_DONE',flush=True)
