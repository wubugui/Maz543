"""Read-only exact legacy platform retention and coexisting native-step inventory.

No generation, reparenting, hiding, movement, separation or native save. Exact
oriented source triangles establish retention, not actual manufacturer identity.
"""
import bpy, hashlib, json
from collections import Counter
from pathlib import Path
import numpy as np
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'outputs/cloud-va180-panel-fit-20261001/MAZ543A_Master.blend'
OUT=ROOT/'work/cloud-native-step-assembly-20261001';OUT.mkdir(parents=True,exist_ok=True)
LOOKUP=OUT/'seed-lookup/result.json';PAYLOAD=OUT/'seed-lookup/box-triangles.json'
EXPECTED='8e962d6dc2565974be8a0e96930606599ddbf6098780951dc96cbb9e13e3fd70'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
(OUT/'native-assembly-report.json').write_text('{"status":"IN_PROGRESS_NOT_ACCEPTED"}\n')
assert sha(SOURCE)==EXPECTED and bpy.app.version[:3]==(4,5,13)
lookup=json.loads(LOOKUP.read_bytes());payload=json.loads(PAYLOAD.read_bytes())
assert lookup['seed']['sha256']=='5c5849b68a5fa62e903b46b5554b8eb942495eabb3a12cb26caf24742cd9681c'
assert lookup['status']=='FOUR_EXACT_SEED_BOX_COMPONENTS_IDENTIFIED_NATIVE_RETENTION_NOT_TESTED'
assert next(x['sha256'] for x in lookup['artifacts'] if x['file']=='box-triangles.json')==sha(PAYLOAD)
bpy.ops.wm.open_mainfile(filepath=str(SOURCE));bpy.context.scene.frame_set(0);bpy.context.view_layer.update()
dg=bpy.context.evaluated_depsgraph_get();assert dg.mode=='VIEWPORT'

def snapshot(name):
 o=bpy.data.objects[name];e=o.evaluated_get(dg);m=e.to_mesh()
 try:
  xyz=np.asarray([tuple(v.co) for v in m.vertices],dtype=np.float64);w=np.asarray(e.matrix_world,dtype=np.float64)
  xyz=xyz@w[:3,:3].T+w[:3,3];m.calc_loop_triangles();tri=np.asarray([tuple(t.vertices) for t in m.loop_triangles],dtype=np.int32)
  return xyz,tri
 finally:e.to_mesh_clear()

def canonical(triangle):
 t=tuple(tuple(float(x) for x in p) for p in triangle)
 return min(t,t[1:]+t[:1],t[2:]+t[:2])

def bvh(xyz,tri):return BVHTree.FromPolygons(xyz.tolist(),tri.tolist(),all_triangles=True,epsilon=0.)

def contacts(a,b):
 if np.any(a[0].max(0)<b[0].min(0)) or np.any(b[0].max(0)<a[0].min(0)):return []
 return sorted([list(p) for p in bvh(*a).overlap(bvh(*b))])

names=['cab_0062','cab_0063']+[f'BL_Cab_{s}_{k}' for s in [-1,1] for k in ['side_monocoque','step']]+[f'BL_Step_{s}_{j}' for s in [-1,1] for j in range(20)]+[f'BL_Door_{s}_{j}_pressed_shell' for s in [-1,1] for j in range(2)]
meshes={};objects=[];missing=[]
for name in names:
 o=bpy.data.objects.get(name)
 if o is None:missing.append(name);continue
 xyz,tri=snapshot(name);meshes[name]=(xyz,tri)
 r={'name':name,'type':o.type,'parent':o.parent.name if o.parent else None,
 'data':o.data.name,'world_matrix':[list(x) for x in o.matrix_world],
 'hide_render':o.hide_render,'hide_viewport':o.hide_viewport,'hide_local':o.hide_get(),
 'evaluated_vertices':len(xyz),'evaluated_triangles':len(tri),'bounds_world_m':[xyz.min(0).tolist(),xyz.max(0).tolist()],
 'position_topology_sha256':hashlib.sha256(xyz.tobytes()+tri.tobytes()).hexdigest(),
 'materials':[x.name if x else None for x in o.data.materials],
 'modifiers':[{'name':m.name,'type':m.type,'show_viewport':m.show_viewport,'show_render':m.show_render} for m in o.modifiers]}
 if o.type=='CURVE':
  r['curve']={'dimensions':o.data.dimensions,'bevel_depth':o.data.bevel_depth,'bevel_resolution':o.data.bevel_resolution,
   'use_fill_caps':o.data.use_fill_caps,'splines':[{'type':s.type,'cyclic':s.use_cyclic_u,
   'points_local':[[*p.co] for p in s.points],'bezier_points_local':[[*p.co] for p in s.bezier_points]} for s in o.data.splines]}
 objects.append(r)
report={'status':'NATIVE_STEP_ASSEMBLY_INVENTORY_ONLY','source_sha256':EXPECTED,
 'input_sha256':{'seed_lookup':sha(LOOKUP),'source_triangle_payload':sha(PAYLOAD)},
 'frame':0,'blender_version':bpy.app.version_string,'depsgraph_mode':dg.mode,
 'objects':objects,'missing_expected_names':missing,'old_platform_matches':[],
 'geometry_modified':False,'source_saved':False,'whole_vehicle_acceptance':'16 OPEN',
 'limits':['Exact matching identifies retained source triangles, not factory step dimensions, part numbers or intentional supersession',
 'Object names and source generator intent alone do not establish a complete physical assembly',
 'Surface BVH overlap candidates do not distinguish intentional joins, touching or volumetric penetration',
 'Rest-pose inventory only; no continuous motion, renderer or browser acceptance',
 'Coexisting two historical authoring schemes are not permission to delete or move a material batch that also contains other parts']}
if 'cab_0062' in meshes:
 xyz,tri=meshes['cab_0062'];all_tri=xyz[tri];index={}
 for i,t in enumerate(all_tri):index.setdefault(canonical(t),[]).append(i)
 for source in payload:
  expected=[canonical(t['native_oriented_corners']) for t in source['triangles']]
  found=[index.get(t,[]) for t in expected];exact=all(len(f)==1 for f in found)
  row={'id':source['id'],'seed_component':source['component'],'native_object':'cab_0062',
   'source_oriented_triangles':len(expected),'all12_source_oriented_triangles_present_once':exact,
   'matched_native_triangle_indices':[x[0] for x in found] if exact else None,
   'triangle_match_counts':[len(x) for x in found]}
  if exact:
   ids=[x[0] for x in found];part_tri=tri[ids];vids=sorted(set(int(v) for t in part_tri for v in t));part=(xyz,part_tri)
   row.update({'native_vertex_indices':vids,'bounds_world_m':[xyz[vids].min(0).tolist(),xyz[vids].max(0).tolist()],
    'closed_surface_candidates':[]})
   for n,m in meshes.items():
    if n in ['cab_0062','cab_0063']:continue
    hit=contacts(part,m)
    if hit:row['closed_surface_candidates'].append({'other':n,'triangle_pairs':hit,'triangle_pair_count':len(hit)})
   altered=list(expected);t=[list(p) for p in altered[0]];t[0][0]+=1e-4;assert canonical(t) not in index
   reversed_triangle=canonical([expected[0][0],expected[0][2],expected[0][1]]);assert reversed_triangle not in index
   row['negative_controls']={'100um_corner_change_rejected':True,'reversed_winding_rejected':True}
  report['old_platform_matches'].append(row)
report['old_platform_exact_matches']=sum(x['all12_source_oriented_triangles_present_once'] for x in report['old_platform_matches'])
report['existing_lower_step_curves']=[n for n in meshes if n.startswith('BL_Cab_') and n.endswith('_step')]
report['existing_tread_bars']=[n for n in meshes if n.startswith('BL_Step_')]
report['source_sha256_after']=sha(SOURCE);assert report['source_sha256_after']==EXPECTED
(OUT/'native-assembly-report.json').write_text(json.dumps(report,ensure_ascii=False,separators=(',',':'))+'\n')
print('NATIVE_STEP_ASSEMBLY','old_platform_exact',report['old_platform_exact_matches'],'lower_curves',len(report['existing_lower_step_curves']),'tread_bars',len(report['existing_tread_bars']),'missing',missing,flush=True)
for x in report['old_platform_matches']:
 print('OLD_PLATFORM',x['id'],'exact',x['all12_source_oriented_triangles_present_once'],'contacts',[(y['other'],y['triangle_pair_count']) for y in x.get('closed_surface_candidates',[])],flush=True)
