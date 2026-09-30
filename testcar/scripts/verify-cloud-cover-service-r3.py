"""Saved read-back: actual active geometry, no whole-object contact exclusions.
Discrete surface intersections are reported, including mounting areas. This is
not continuous swept-volume, finite clearance, or complete containment proof.
"""
import bpy,bmesh,json,math,itertools
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs/cloud-cover-service-r3-20260930'
MOVING=['BL_Front_cover_front_panel','BL_Front_cover_hinge_knuckle_-1','BL_Front_cover_hinge_knuckle_1','BL_Front_cover_latch_-0.46','BL_Front_cover_latch_0.46']
LIP='BL_Front_cover_lip';CTRL='BL_Cover_service_DIAGNOSTIC_CONTROL';report={'scope':'Native save/reopen; 21 release states at 5deg and 20 open states at 3deg, stationary vehicle','collisionMethod':'Evaluated triangle BVH surface intersections, no pin/lug/latch/lip exclusions. Broadphase evaluated bounds. Not a continuous sweep or complete containment test.','status':'CANDIDATE_NOT_PROMOTED','files':[]}
def pose(s):
 c=bpy.data.objects[CTRL];c['service_stage']=s;c.update_tag();bpy.context.view_layer.update()
def bounds(pts):return {'min':[min(p[i] for p in pts) for i in range(3)],'max':[max(p[i] for p in pts) for i in range(3)]}
def overlap(a,b):return all(a['min'][i]<=b['max'][i] and b['min'][i]<=a['max'][i] for i in range(3))
def snap(o,top=False):
 ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();m.calc_loop_triangles();local=[v.co.copy() for v in m.vertices]
 if not local:raise RuntimeError('Empty evaluated geometry '+o.name)
 world=[ev.matrix_world@p for p in local];tris=[tuple(t.vertices) for t in m.loop_triangles]
 d={'local':local,'world':world,'tris':tris,'bounds':bounds(world),'tree':BVHTree.FromPolygons(world,tris,all_triangles=True),'matrix':[list(r) for r in ev.matrix_world]}
 if top:
  bm=bmesh.new();bm.from_mesh(m);d['topology']={'vertices':len(local),'triangles':len(tris),'nonManifoldEdges':sum(not e.is_manifold for e in bm.edges),'signedVolumeM3':bm.calc_volume(signed=True)};bm.free()
 ev.to_mesh_clear();return d
def kd(points):
 k=KDTree(len(points))
 for i,p in enumerate(points):k.insert(p,i)
 k.balance();return k
def haus(a,b,ka):
 kb=kd(b);return max(max(ka.find(p)[2] for p in b),max(kb.find(p)[2] for p in a))
def collision(na,a,nb,b):
 if not overlap(a['bounds'],b['bounds']):return None
 hits=a['tree'].overlap(b['tree'])
 if not hits:return None
 pa=[a['world'][v] for ia,_ in hits for v in a['tris'][ia]];pb=[b['world'][v] for _,ib in hits for v in b['tris'][ib]]
 return {'a':na,'b':nb,'trianglePairs':len(hits),'aHitTriangleBoundsXYZ':bounds(pa),'bHitTriangleBoundsXYZ':bounds(pb),'classification':'UNRESOLVED_SURFACE_INTERSECTION; no blanket mounting exemption'}
states=[{'stage':'latch_release','parameter':i/20,'latchDegrees':-5*i,'lidDegrees':0} for i in range(21)]+[{'stage':'lid_open','parameter':1+i/20,'latchDegrees':-100,'lidDegrees':3*i} for i in range(1,21)]
for filename in ['MAZ543A_Master.blend','MAZ543A_Textured.blend']:
 print('AUDIT_FILE',filename,flush=True);bpy.ops.wm.open_mainfile(filepath=str(OUT/filename));bpy.context.scene.frame_set(0);pose(0)
 refs={n:snap(bpy.data.objects[n],True) for n in MOVING+[LIP]};trees={n:kd(s['local']) for n,s in refs.items()}
 parts=[o for o in bpy.data.objects if o.name.startswith(('BL_Front_cover_front_panel','BL_Front_cover_middle_panel','BL_Front_cover_rear_panel','BL_Front_cover_hinge_pin_','BL_Front_cover_hinge_knuckle_','BL_Front_cover_fixed_hinge_lug_'))]
 topo=[{'object':o.name,**snap(o,True)['topology']} for o in parts]+[{'object':n,**refs[n]['topology']} for n in [LIP]+MOVING[-2:]]
 sweep={'min':[1e9]*3,'max':[-1e9]*3};pose_report=[]
 for state in states:
  pose(state['parameter']);row=dict(state);row['objects']=[]
  for n in MOVING+[LIP]:
   s=snap(bpy.data.objects[n]);delta=haus(refs[n]['local'],s['local'],trees[n]);row['objects'].append({'object':n,'matrixWorld':s['matrix'],'vertices':len(s['local']),'localVertexHausdorffM':delta})
   for i in range(3):sweep['min'][i]=min(sweep['min'][i],s['bounds']['min'][i]);sweep['max'][i]=max(sweep['max'][i],s['bounds']['max'][i])
  pose_report.append(row)
 pose(0);static={};active=0;excluded=[]
 for o in bpy.context.scene.objects:
  if o.type not in {'MESH','CURVE','SURFACE','FONT'}:continue
  if o.name in MOVING:continue
  if o.hide_render or o.name.startswith(('CUTTER_','SOURCE_','ARCHIVE')) or any(c.name.startswith('ARCHIVE') for c in o.users_collection):
   excluded.append({'object':o.name,'reason':'hidden render / construction / source or archived comparison'});continue
  active+=1;ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());box=[ev.matrix_world@Vector(v) for v in ev.bound_box]
  if overlap(bounds(box),sweep):static[o.name]=snap(o)
 print('STATIC',len(static),'ACTIVE',active,flush=True)
 # Test changed fixed lip against every shortlisted fixed object; unlike prior
 # scripts this does not omit pin, lug or assembly mounting contacts.
 installation=[]
 for n,s in static.items():
  if n==LIP:continue
  h=collision(LIP,refs[LIP],n,s)
  if h:installation.append(h)
 allhits=[]
 for state in states:
  pose(state['parameter']);moving={n:snap(bpy.data.objects[n]) for n in MOVING}
  hits=[]
  for n,s in moving.items():
   for fixed,f in static.items():
    h=collision(n,s,fixed,f)
    if h:hits.append(h)
  for a,b in itertools.combinations(MOVING,2):
   h=collision(a,moving[a],b,moving[b])
   if h:hits.append(h)
  allhits.append({**state,'intersections':hits})
  print('STATE',state['stage'],state['latchDegrees'],state['lidDegrees'],'HITS',[(h['a'],h['b'],h['trianglePairs']) for h in hits],flush=True)
 pose(0)
 # Original unmodified r2 lip comparison at the same closed pose.
 original_lip=snap(bpy.data.objects['ARCHIVE_R2_BL_Front_cover_lip'],True)
 baseline=collision(MOVING[0],refs[MOVING[0]],'ARCHIVE_R2_BL_Front_cover_lip',original_lip)
 original_installation=[]
 for n,s in static.items():
  if n==LIP:continue
  h=collision('ARCHIVE_R2_BL_Front_cover_lip',original_lip,n,s)
  if h:original_installation.append(h)
 original_latches=[{'object':n,**snap(bpy.data.objects['ARCHIVE_R2_'+n],True)['topology']} for n in MOVING[-2:]]
 # Negative control: hold the original latches locked, rotate actual lid 3deg.
 hinge=bpy.data.objects['BL_Front_cover_hinge'];f=hinge.animation_data.drivers[0];f.mute=True;hinge.rotation_euler.y=math.radians(3);bpy.context.view_layer.update();locked_control=[]
 lid=snap(bpy.data.objects[MOVING[0]])
 for n in MOVING[-2:]:
  h=collision(MOVING[0],lid,n,snap(bpy.data.objects[n]))
  if h:locked_control.append(h)
 f.mute=False;pose(0)
 # The cutter remains fixed in body space and is not a dependent of a moving lid.
 cutter=bpy.data.objects['CUTTER_R3_FIXED_closed_seating_rabbet'];cutbase=cutter.matrix_world.copy();maxcut=0;maxlip=0
 for state in states:
  pose(state['parameter']);maxcut=max(maxcut,max(abs(cutter.matrix_world[i][j]-cutbase[i][j]) for i in range(4) for j in range(4)));maxlip=max(maxlip,max(abs(bpy.data.objects[LIP].matrix_world[i][j]-refs[LIP]['matrix'][i][j]) for i in range(4) for j in range(4)))
 pose(0);maxdev=max(o['localVertexHausdorffM'] for s in pose_report for o in s['objects']);lipdev=max(o['localVertexHausdorffM'] for s in pose_report for o in s['objects'] if o['object']==LIP)
 r={'file':filename,'topology':topo,'topologyStatus':'PASS' if all(t['nonManifoldEdges']==0 and t['signedVolumeM3']>0 for t in topo) else 'FAIL','rigidity':{'maxLocalVertexHausdorffM':maxdev,'thresholdM':2e-5,'status':'PASS' if maxdev<=2e-5 else 'FAIL','poses':pose_report},'fixedRabbet':{'cutterParent':cutter.parent.name,'maxCutterWorldMatrixEntryChange':maxcut,'maxLipWorldMatrixEntryChange':maxlip,'maxLipLocalVertexHausdorffM':lipdev,'status':'PASS' if maxcut==0 and maxlip==0 and lipdev<=2e-5 else 'FAIL'},'originalClosedLipIntersection':baseline,'originalLipTopology':original_lip['topology'],'originalLipInstallationIntersections':original_installation,'originalLatchTopology':original_latches,'lockedLatchLid3DegreeNegativeControl':locked_control,'activeGeometryCount':active,'broadphaseStaticNames':list(static),'explicitNonAssemblyExclusions':excluded,'fixedLipInstallationIntersections':installation,'allDiscreteMotionIntersections':allhits,'collisionStatus':'FAIL_UNRESOLVED_CONTACTS_OR_INTERFERENCES' if installation or any(s['intersections'] for s in allhits) else 'NO_TRIANGLE_CROSSINGS_AT_DISCRETE_SAMPLES_ONLY','limitations':'All dimensions/pivots fitted. No calibrated latch, actual seal/support contact, continuous sweep, load/strength or production/vehicle acceptance.'}
 report['files'].append(r);(OUT/'saved-service-verification.json').write_text(json.dumps(report,indent=2))
 print('FILE_FINISHED',filename,r['collisionStatus'],'rigidity',maxdev,flush=True)
print('R3_SAVED_AUDIT_COMPLETE',flush=True)

# Complete both files and retain all failed findings before returning failure.
assert all(f['topologyStatus']=='PASS' and f['rigidity']['status']=='PASS' and f['fixedRabbet']['status']=='PASS' and f['collisionStatus']=='NO_TRIANGLE_CROSSINGS_AT_DISCRETE_SAMPLES_ONLY' for f in report['files']), 'R3 remains a diagnostic candidate: unresolved topology / installation / release contacts are recorded, not waived'
