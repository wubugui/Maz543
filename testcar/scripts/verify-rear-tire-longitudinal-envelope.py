"""Read-only separating-plane proof for current rear boxes vs rear tyre geometry.

This does NOT prove whole-vehicle continuous clearance. It bounds only the
actual twelve rear-box/mount meshes against the current four rigid rear tyres,
under the explicitly recorded motion contract and current source hashes.
"""
import bpy,json,hashlib,math,os
from pathlib import Path
from mathutils import Matrix
ROOT=Path(__file__).resolve().parents[1]
MODEL=Path(os.environ.get('MAZ_MODEL_PATH',str(ROOT/'outputs/MAZ543A_Master.blend'))).resolve()
OUT=Path(os.environ.get('MAZ_ENVELOPE_OUTPUT',str(ROOT/'outputs/cloud-rear-envelope-20260930'))).resolve()
OUT.mkdir(parents=True,exist_ok=True)
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(MODEL));bpy.context.scene.frame_set(0);bpy.context.view_layer.update()
root=bpy.data.objects['MAZ543_REFERENCE_CHASSIS'];inverse=root.matrix_world.inverted()
def vertices(obj,transform):
 ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh()
 points=[transform@ev.matrix_world@v.co for v in mesh.vertices];ev.to_mesh_clear()
 if not points:raise RuntimeError('Empty native geometry '+obj.name)
 return points
rear=[o for o in bpy.data.objects if o.parent and o.type in {'MESH','CURVE','SURFACE','FONT','META'} and o.name.startswith('BL_RearRestoration_')]
assert len(rear)==12,('Unexpected current rear installation inventory',len(rear))
parts=[]
for obj in rear:
 points=vertices(obj,inverse)
 parts.append({'name':obj.name,'minX':min(p.x for p in points),'maxX':max(p.x for p in points),'vertices':len(points)})
wheels=[]
for index,expectedX in [(4,2.42),(5,2.42),(6,4.62),(7,4.62)]:
 tyres=[o for o in bpy.data.objects if o.parent and o.type in {'MESH','CURVE','SURFACE','FONT','META'} and o.name.startswith(f'BL_Tyre_{index}_')]
 assert len(tyres)==108,(index,len(tyres))
 spins={o.parent for o in tyres};assert len(spins)==1,'Multiple tyre motion frames'
 spin=spins.pop();carrier=spin.parent
 assert carrier and carrier.parent and carrier.parent.name=='wheels','Unexpected wheel hierarchy'
 spinInRoot=inverse@spin.matrix_world
 assert max(abs(spinInRoot.to_3x3()[r][c]-(1 if r==c else 0)) for r in range(3) for c in range(3))<1e-6,'Non-neutral/scaled wheel frame'
 assert abs(spinInRoot.translation.x-expectedX)<1e-6,'Native axle differs from reviewed motion contract'
 points=[];objectEnvelopes=[]
 for obj in tyres:
  assert not getattr(obj.data,'shape_keys',None),'Tyre deformation requires another envelope'
  objPoints=vertices(obj,spin.matrix_world.inverted());points.extend(objPoints)
  objectEnvelopes.append({'name':obj.name,'type':obj.type,'hiddenRender':obj.hide_render,'hiddenViewport':obj.hide_get(),'radialEnvelopeM':max(math.hypot(p.x,p.z) for p in objPoints),'collections':[c.name for c in obj.users_collection]})
 radius=max(math.hypot(p.x,p.z) for p in points)
 # Browser spin Z is native Y. Any spin angle obeys |x| <= hypot(x,z).
 # Carrier camber is about X, which leaves X unchanged. Transverse/vertical
 # suspension translations also leave X unchanged. Common chassis motion is
 # rigid and therefore preserves a separating plane in chassis coordinates.
 wheels.append({'index':index,'carrier':carrier.name,'spin':spin.name,'axleX':expectedX,'actualNativeAxleX':spinInRoot.translation.x,'radialEnvelopeM':radius,'objectEnvelopes':objectEnvelopes,'tyreObjects':len(tyres),'objectTypes':{kind:sum(o.type==kind for o in tyres) for kind in sorted({o.type for o in tyres})},'vertices':len(points),'minX':expectedX-radius,'maxX':expectedX+radius})
padding=2e-5;pairs=[]
for part in parts:
 for wheel in wheels:
  gap=max(part['minX']-wheel['maxX'],wheel['minX']-part['maxX'])
  pairs.append({'part':part['name'],'wheel':wheel['index'],'separatingGapM':gap,'conservativeGapM':gap-2*padding,'status':'SEPARATED' if gap>2*padding else 'INCONCLUSIVE'})
report={'status':'PASS_CONDITIONAL_LONGITUDINAL_SEPARATION' if all(p['status']=='SEPARATED' for p in pairs) else 'INCONCLUSIVE','geometrySourceSHA256':digest(MODEL),'sourceSHA256':{str(p.relative_to(ROOT)):digest(p) for p in [ROOT/'lib/suspension.ts',ROOT/'lib/maz543.ts',ROOT/'lib/vehicleViewport.ts']},'motionContract':{'rearSteeringRadians':0,'axleLongitudinalCoordinatesFixed':True,'arbitraryVerticalAndTransverseSuspensionMotion':True,'arbitraryCamberAboutLongitudinalX':True,'arbitraryWheelSpinAboutNativeY':True,'commonChassisRigidMotion':True,'rigidTyres':True},'mathematicalBasis':'A triangle lies within the radial envelope of its vertices. For all spin angles, abs(local x) <= max hypot(local x,local z). Camber about x and y/z translation preserve x. Disjoint closed x intervals imply disjoint meshes at every pose satisfying this motion contract, independent of time sampling. Common chassis rigid transforms preserve this separating plane.','numericalPaddingPerEnvelopeM':padding,'parts':parts,'wheels':wheels,'pairs':pairs,'minimumConservativeGapM':min(p['conservativeGapM'] for p in pairs),'notCovered':['Factory-dimensional correctness or real suspension kinematics','Tyre load deformation, flex or radial growth','Longitudinal axle/bushing deflection or rear steering','Clearance to other body, axle, brake or suspension parts','Front-wheel steering','Full-vehicle continuous sweep or dynamic loads','Actual browser-runtime pose parity']}
(OUT/'longitudinal-envelope.json').write_text(json.dumps(report,indent=2))
print(json.dumps({'status':report['status'],'parts':len(parts),'tyres':sum(w['tyreObjects'] for w in wheels),'minimumConservativeGapM':report['minimumConservativeGapM'],'radii':[w['radialEnvelopeM'] for w in wheels]},indent=2))
