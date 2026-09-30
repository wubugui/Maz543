import bpy,json,sys,math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from suspension_asset import descendants
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'outputs/MAZ543A_Textured.blend'));scene=bpy.context.scene
poses=json.loads((ROOT/'work/starting-engine-poses.json').read_text());start=json.loads((ROOT/'work/starting-poses.json').read_text());err=0;rot=0
for f in [0,90,105,115,125,140,160,180,240,300,420,480,540,600]:
 scene.frame_set(f)
 for name,p in poses[f]['pose'].items():
  ob=bpy.data.objects.get(name);assert ob is not None,name
  err=max(err,(ob.location-Vector((p['p'][0],-p['p'][2],p['p'][1]))).length)
  rot=max(rot,abs(ob.rotation_euler.x-p['rx']))
 assert abs(bpy.data.objects['D12_crankshaft'].rotation_euler.x-bpy.data.objects['C5_FLYWHEEL_RING'].rotation_euler.x)<.0002
scene.frame_set(0);bpy.context.evaluated_depsgraph_get().update()
def bounds(o):
 vs=[o.matrix_world@Vector(v) for v in o.bound_box];return [min(v[i] for v in vs) for i in range(3)],[max(v[i] for v in vs) for i in range(3)]
pin=bpy.data.objects['C5_11_tooth_pinion'];ring=bpy.data.objects['C5_flywheel_involute_ring'];gap=bounds(ring)[0][0]-bounds(pin)[1][0]
assert .00349<gap<.00351,gap
pump=bpy.data.objects['MZN_PREOIL'];assert pump.parent.name=='S543_STARTING';assert bpy.data.objects['C5_STARTER'].parent.parent.name=='engine'
def tree(o):
 e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh();m.calc_loop_triangles();t=BVHTree.FromPolygons([e.matrix_world@v.co for v in m.vertices],[list(p.vertices) for p in m.loop_triangles],all_triangles=True);e.to_mesh_clear();return t
frame=[o for o in descendants(bpy.data.objects['frame']) if o.type=='MESH'];hits=[]
for p in descendants(pump):
 if p.type!='MESH':continue
 lo,hi=bounds(p)
 for q in frame:
  qlo,qhi=bounds(q)
  if all(lo[i]<=qhi[i] and hi[i]>=qlo[i] for i in range(3)):
   overlaps=tree(p).overlap(tree(q))
   if overlaps:hits.append([p.name,q.name,len(overlaps)])
report={'nativeD12Samples':14,'maxPositionError':err,'maxRotationError':rot,'starterAxialRestGap':gap,'pumpFrameIntersections':hits,'pumpParent':pump.parent.name,'starterMountParent':bpy.data.objects['C5_STARTER'].parent.parent.name}
(ROOT/'outputs/starting-installation-verification.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)
assert err<.000002 and rot<.0002,(err,rot)
assert not hits,hits
