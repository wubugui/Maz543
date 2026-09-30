import bpy,json,os
from pathlib import Path
from mathutils import Vector
p=Path('testcar/outputs/cloud-three-cover-r2-portable-20260930/MAZ543A_Master.blend').resolve()
bpy.ops.wm.open_mainfile(filepath=str(p));bpy.context.scene.frame_set(0);bpy.context.view_layer.update()
names=['BL_Front_cover_lip','BL_Front_cover_latch_-0.46','BL_Front_cover_latch_0.46','BL_Front_cover_front_panel']
for name in names:
 o=bpy.data.objects[name];print('\nOBJECT',name,o.type,'parent',o.parent.name if o.parent else None,'loc',list(o.location),'matrix',[list(r) for r in o.matrix_world]);print('mods',[(m.name,m.type,getattr(m,'thickness',None),getattr(m,'offset',None),getattr(m,'operation',None),getattr(getattr(m,'object',None),'name',None)) for m in o.modifiers]);
 ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();ps=[ev.matrix_world@v.co for v in me.vertices];print('BOUNDS',[[min(p[i] for p in ps),max(p[i] for p in ps)] for i in range(3)],'N',len(ps));ev.to_mesh_clear()
 if o.type=='CURVE':
  print('CURVE',o.data.bevel_depth,[(s.type,[[list(q.co),list(o.matrix_world@q.co)] for q in s.bezier_points]) for s in o.data.splines])
print('DONE')
