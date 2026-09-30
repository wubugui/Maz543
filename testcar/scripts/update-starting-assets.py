import bpy,sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from d12_asset import engine_descendants,attach_engine
from suspension_asset import descendants
# Engine module excludes the now independently authored starter and ring gear.
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'outputs/D12A525A_Engine_Master.blend'))
old=bpy.data.objects.get('D12_C5_starter')
if old:
 for ob in reversed([old]+descendants(old)):bpy.data.objects.remove(ob,do_unlink=True)
for ob in list(bpy.data.objects):
 if ob.name.startswith('D12_flywheel_tooth_') or ob.name=='D12_flywheel_starting_ring':bpy.data.objects.remove(ob,do_unlink=True)
root=bpy.data.objects['D12A_525A'];bpy.context.scene.frame_set(1)
reg=[{'node':o.name,'part':o.get('d12Part'),'source':o.get('sourceId'),'role':o.get('d12Role'),'dimensions':o.get('dimensionStatus')} for o in descendants(root) if 'd12Part' in o]
(ROOT/'outputs/d12-parts-register.json').write_text(json.dumps(reg,indent=2),encoding='utf-8')
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'outputs/D12A525A_Engine_Master.blend'),compress=True)
bpy.ops.object.select_all(action='DESELECT');objects=[o for o in descendants(root) if o.type in ['MESH','CURVE']]
for o in objects:o.select_set(True)
bpy.context.view_layer.objects.active=objects[0];bpy.ops.object.convert(target='MESH')
for holder in [root]+[o for o in descendants(root) if o.type=='EMPTY']:
 batches={}
 for ob in holder.children:
  if ob.type=='MESH':batches.setdefault((ob.data.materials[0].name,ob.get('d12Role'),ob.get('sourceId'),ob.get('timingGearId'),bool(ob.get('timingTrain')),bool(ob.get('waterPump')),ob.get('waterHalf'),ob.get('figureItem')),[]).append(ob)
 for key,batch in batches.items():
  if len(batch)<2:continue
  bpy.ops.object.select_all(action='DESELECT')
  for o in batch:o.select_set(True)
  bpy.context.view_layer.objects.active=batch[0];bpy.ops.object.join();ob=bpy.context.object;ob.name=holder.name+'_'+key[0]+'_'+str(key[1]);ob['detail_meshes']=len(batch);ob['d12Role']=key[1]
bpy.ops.object.select_all(action='DESELECT')
for o in [root]+descendants(root):
 o.select_set(True)
 if o.type=='MESH':tri=o.modifiers.new('Triangulate for tangents','TRIANGULATE');tri.min_vertices=5
bpy.context.view_layer.objects.active=root
bpy.ops.export_scene.gltf(filepath=str(ROOT/'public/models/d12a525a-engine.glb'),export_format='GLB',use_selection=True,export_yup=True,export_apply=True,export_tangents=True,export_extras=True,export_animations=False,export_draco_mesh_compression_enable=True,export_draco_mesh_compression_level=6)
for name in ['MAZ543A_Master.blend','MAZ543A_Textured.blend']:
 file=ROOT/'outputs'/name;bpy.ops.wm.open_mainfile(filepath=str(file));attach_engine()
 old=bpy.data.objects.get('S543_STARTING')
 if old:
  for ob in reversed([old]+descendants(old)):bpy.data.objects.remove(ob,do_unlink=True)
 col=bpy.data.collections.get('S543_STARTING')
 if col:bpy.data.collections.remove(col)
 with bpy.data.libraries.load(str(ROOT/'outputs/MAZ543A_Starting_Master.blend'),link=False) as (src,dst):dst.collections=['S543_STARTING']
 col=dst.collections[0];bpy.context.scene.collection.children.link(col);root=next(o for o in col.objects if o.name=='S543_STARTING')
 root.parent=bpy.data.objects['MAZ543_REFERENCE_CHASSIS'];root.location=(0,0,0)
 engine=bpy.data.objects['engine'];anchor=bpy.data.objects.new('STARTING_ENGINE_MOUNT',None);col.objects.link(anchor);anchor.parent=engine
 for n in ['C5_STARTER','C5_FLYWHEEL_RING']:bpy.data.objects[n].parent=anchor
 spec=json.loads((ROOT/'work/starting-poses.json').read_text())['spec'];p=spec['pumpPosition'];bpy.data.objects['MZN_PREOIL'].location=(p[0],-p[2],p[1])
 # Motor, ring and all D12 internals share the same crank-angle sequence.
 data=json.loads((ROOT/'work/starting-engine-poses.json').read_text())
 for n,p0 in data[0]['pose'].items():
  ob=bpy.data.objects.get(n)
  if not ob:continue
  ob.animation_data_clear();ob.location=(p0['p'][0],-p0['p'][2],p0['p'][1]);ob.rotation_euler=(p0['rx'],0,0);ob.scale=(1,1,p0.get('sy',1))
  action=bpy.data.actions.new('Causal start '+n);slot=action.slots.new(id_type='OBJECT',name=n);ob.animation_data_create().action=action;ob.animation_data.action_slot=slot
  for channel,index,getter in [('location',0,lambda p:p['p'][0]),('location',1,lambda p:-p['p'][2]),('location',2,lambda p:p['p'][1]),('rotation_euler',0,lambda p:p['rx']),('scale',2,lambda p:p.get('sy',1))]:
   values=[getter(f['pose'][n]) for f in data]
   if max(values)-min(values)<1e-12:continue
   fc=action.fcurves.new(data_path=channel,index=index);fc.keyframe_points.add(len(data));fc.keyframe_points.foreach_set('co',[v for f,x in zip(data,values) for v in (f['frame'],x)])
   for key in fc.keyframe_points:key.interpolation='LINEAR'
   fc.update()
 bpy.context.scene.frame_start=0;bpy.context.scene.frame_end=600;bpy.context.scene.render.fps=60;bpy.context.scene.frame_set(0)
 bpy.ops.wm.save_as_mainfile(filepath=str(file),compress=True)
print('STARTING_INTEGRATED: independent frame pump, engine-mounted starter, unified native start sequence',flush=True)
