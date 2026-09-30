"""Build independent r3 fitted service candidate using native Boolean and drivers.
Never promotes or overwrites the r2 or production assets. CPU/background only.
"""
import bpy,json,math,os,hashlib
from pathlib import Path
from mathutils import Vector
from mathutils.kdtree import KDTree
ROOT=Path(__file__).resolve().parents[1]
INPUT=ROOT/'outputs/cloud-three-cover-r2-portable-20260930'
OUT=ROOT/'outputs/cloud-cover-service-r3-20260930';OUT.mkdir(parents=True,exist_ok=True)
def bounds(o):
 e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh();p=[e.matrix_world@v.co for v in m.vertices];e.to_mesh_clear()
 if not p: raise RuntimeError('Empty geometry '+o.name)
 return {'min':[min(v[i] for v in p) for i in range(3)],'max':[max(v[i] for v in p) for i in range(3)]}
def parent(o,p):
 bpy.context.view_layer.update();m=o.matrix_world.copy();o.parent=p;o.matrix_world=m;bpy.context.view_layer.update()
def archive_copy(o):
 c=o.copy();c.data=o.data.copy();c.name='ARCHIVE_R2_'+o.name;bpy.context.scene.collection.objects.link(c)
 coll=bpy.data.collections.get('ARCHIVE_R2_SERVICE_20260930')
 if not coll:coll=bpy.data.collections.new('ARCHIVE_R2_SERVICE_20260930');bpy.context.scene.collection.children.link(coll)
 for co in list(c.users_collection):co.objects.unlink(c)
 coll.objects.link(c);c.hide_render=True;c.hide_set(True);c['purpose']='Unmodified r2 comparison original, excluded from assembly';return c
report={'status':'CANDIDATE_NOT_PROMOTED','method':'Fixed native exact-Boolean lip rabbet plus rigid latch-proxy release, all dimensions fitted, mechanism uncalibrated','sources':{'manual':'https://djvu.online/file/zjMdLY3MFjmTL printed p173: hinged front; middle/rear removable','catalogue':'Retained 543a-8400002.gif.png; assembly drawing does not calibrate axis, notch or lock motion'},'files':[]}
for filename in ['MAZ543A_Master.blend','MAZ543A_Textured.blend']:
 source=INPUT/filename;bpy.ops.wm.open_mainfile(filepath=str(source));bpy.context.scene.frame_set(0);bpy.context.view_layer.update()
 body=bpy.data.objects['body'];panel=bpy.data.objects['BL_Front_cover_front_panel'];lip=bpy.data.objects['BL_Front_cover_lip'];hinge=bpy.data.objects['BL_Front_cover_hinge']
 assert not hinge.animation_data,'Existing hinge animation requires explicit integration'
 pb=bounds(panel);lb=bounds(lip);archive=archive_copy(lip)
 # Keep the lip lower rail and outer shoulders. Cut only the fixed closed-pose
 # central seating recess, with a fitted 2 mm minimum vertical/3 mm side gap.
 floor=pb['min'][2]-.002;y0=pb['min'][1]-.003;y1=pb['max'][1]+.003
 x0=lb['min'][0]-.005;x1=lb['max'][0]+.005;top=lb['max'][2]+.050
 bpy.ops.mesh.primitive_cube_add(size=1,location=((x0+x1)/2,(y0+y1)/2,(floor+top)/2));c=bpy.context.object;c.name='CUTTER_R3_FIXED_closed_seating_rabbet';c.dimensions=(x1-x0,y1-y0,top-floor);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);parent(c,body)
 c.hide_render=True;c.hide_set(True);c.display_type='WIRE';c['constructionOwner']=lip.name;c['fixedClosedPosition']=True;c['calibration']='Fitted 2 mm vertical / 3 mm transverse relief; not factory dimensions'
 mod=lip.modifiers.new('R3 fixed closed-position seating rabbet','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=c
 b=lip.modifiers.new('R3 recess edge break 1mm fitted','BEVEL');b.width=.001;b.segments=3
 lip['r3Modification']='Real Boolean top-central seating relief; lower rail and both shoulders retained; original archived'
 control=bpy.data.objects.new('BL_Cover_service_DIAGNOSTIC_CONTROL',None);bpy.context.scene.collection.objects.link(control);control.location=(-5.8,0,2.45);parent(control,body);control.empty_display_type='PLAIN_AXES';control.empty_display_size=.1
 control['service_stage']=0.;control.id_properties_ui('service_stage').update(min=0,max=2,soft_min=0,soft_max=2,description='UNVALIDATED fitted sequence: 0 locked closed; 1 proxy locks released 100deg; 2 lid 60deg. No factory or load certification.')
 control['warning']='Diagnostic motion of existing three-point latch proxies only. No claim of factory lock, pivot, linkage or opening angle.'
 def driver(obj,expression):
  f=obj.driver_add('rotation_euler',1);d=f.driver;d.type='SCRIPTED';v=d.variables.new();v.name='s';v.type='SINGLE_PROP';v.targets[0].id=control;v.targets[0].data_path='["service_stage"]';d.expression=expression
 driver(hinge,'max(0,min(s-1,1))*'+repr(math.radians(60)))
 latch_data=[]
 for name in ['BL_Front_cover_latch_-0.46','BL_Front_cover_latch_0.46']:
  latch=bpy.data.objects[name];archive_copy(latch);assert latch.type=='CURVE'
  # Native curve caps have duplicated rim vertices. Weld only these coincident
  # vertices, retaining the editable curve and the untouched archived original.
  def vertices():
   bpy.context.view_layer.update();ev=latch.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();ps=[v.co.copy() for v in me.vertices];ev.to_mesh_clear();return ps
  before=vertices();assert latch.data.use_fill_caps,'Unexpected uncapped original'
  weld=latch.modifiers.new('R3 weld coincident cap rims 1um','WELD');weld.merge_threshold=.000001;after=vertices()
  def nearest(a,b):
   k=KDTree(len(a))
   for i,v in enumerate(a):k.insert(v,i)
   k.balance();return max(k.find(v)[2] for v in b)
  cap_change=max(nearest(before,after),nearest(after,before));assert cap_change<1e-7,('Weld changed the proxy surface',cap_change)
  base=latch.matrix_world@latch.data.splines[0].bezier_points[0].co
  pivot=bpy.data.objects.new('BL_R3_latch_release_pivot_'+name.rsplit('_',1)[1],None);bpy.context.scene.collection.objects.link(pivot);pivot.location=base;parent(pivot,body);pivot.empty_display_type='CIRCLE';pivot.empty_display_size=.025
  parent(latch,pivot);pivot['warning']='UNVALIDATED diagnostic pivot at retained curve first point, not known factory mounting axis';latch['motionStatus']='Original r2 curve control points preserved with native cap-rim Weld; fitted rigid release before lid opening'
  driver(pivot,'max(0,min(s,1))*'+repr(math.radians(-100)))
  latch_data.append({'name':name,'pivotBlenderXYZ':list(base),'diagnosticReleasedDegrees':-100,'geometry':'original three-point Bezier control geometry with native coincident-cap-rim Weld','capWeld':{'mergeThresholdM':.000001,'verticesBefore':len(before),'verticesAfter':len(after),'vertexSetHausdorffM':cap_change}})
 bpy.context.view_layer.update();bpy.ops.wm.save_as_mainfile(filepath=str(OUT/filename),compress=True)
 report['files'].append({'file':filename,'inputSHA256':hashlib.sha256(source.read_bytes()).hexdigest(),'frontPanelClosedBoundsXYZ':pb,'originalLipBoundsXYZ':lb,'rabbet':{'fixedCutter':c.name,'parent':c.parent.name,'floorBlenderZ':floor,'widthM':y1-y0,'lowerRailMinimumHeightM':floor-lb['min'][2],'untrimmedOuterShoulderEachM':(lb['max'][1]-lb['min'][1]-(y1-y0))/2,'nominalMinimumVerticalGapM':.002,'nominalLateralGapEachM':.003,'contactStatus':'Clearance candidate only. Seal, bearing contact and load support not validated.'},'latches':latch_data,'control':{'object':control.name,'property':'service_stage','closed':0,'locksReleasedLidClosed':1,'locksReleasedLid60Degrees':2},'archivedOriginalLip':archive.name})
(OUT/'build-service-candidate.json').write_text(json.dumps(report,indent=2))
print('R3_CANDIDATE_SAVED',OUT)
