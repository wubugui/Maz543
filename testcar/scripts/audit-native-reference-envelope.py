"""Measure actual active native geometry; this does not infer factory tolerances."""
import bpy,json,os,hashlib
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs/cloud-nominal-envelope-20260930';OUT.mkdir(exist_ok=True)
rows=[]
for filename in ['MAZ543A_Master.blend','MAZ543A_Textured.blend']:
 source=ROOT/'outputs'/filename;bpy.ops.wm.open_mainfile(filepath=str(source));bpy.context.scene.frame_set(0);bpy.context.view_layer.update()
 root=bpy.data.objects['MAZ543_REFERENCE_CHASSIS'];deps=bpy.context.evaluated_depsgraph_get();parts=[];excluded=[]
 def descendant(o):
  p=o
  while p:
   if p==root:return True
   p=p.parent
  return False
 for o in bpy.context.scene.objects:
  if o.type not in {'MESH','CURVE','SURFACE','FONT','META'} or not descendant(o):continue
  if o.hide_render or o.name.startswith(('CUTTER_','SOURCE_','ARCHIVE','TOOL_')):
   excluded.append(o.name);continue
  ev=o.evaluated_get(deps);m=ev.to_mesh()
  if not m or not m.vertices:
   raise RuntimeError('Unexpected empty active geometry '+o.name)
  points=[ev.matrix_world@v.co for v in m.vertices];ev.to_mesh_clear()
  lo=[min(p[i] for p in points) for i in range(3)];hi=[max(p[i] for p in points) for i in range(3)]
  parts.append({'name':o.name,'type':o.type,'minXYZ':lo,'maxXYZ':hi})
 def envelope(selected):
  lo=[min(p['minXYZ'][i] for p in selected) for i in range(3)];hi=[max(p['maxXYZ'][i] for p in selected) for i in range(3)]
  return {'parts':len(selected),'minXYZ':lo,'maxXYZ':hi,'extentXYZ':[hi[i]-lo[i] for i in range(3)],'minimumContributors':[min(selected,key=lambda p:p['minXYZ'][i])['name'] for i in range(3)],'maximumContributors':[max(selected,key=lambda p:p['maxXYZ'][i])['name'] for i in range(3)]}
 mirrors=[p['name'] for p in parts if 'mirror' in p['name'].lower()]
 wheels=[]
 for i in range(8):
  spin=bpy.data.objects['wheels_pivot_'+str(2+7*i).zfill(3)];wheels.append({'index':i,'spinWorldXYZ':list(spin.matrix_world.translation)})
 rows.append({'file':filename,'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'rootMatrixWorld':[list(r) for r in root.matrix_world],'allActive':envelope(parts),'excludingNamedMirrors':envelope([p for p in parts if p['name'] not in mirrors]),'explicitMirrorNames':mirrors,'nonAssemblyExclusions':excluded,'wheelSpinCenters':wheels,'parts':parts})
 report={'coordinateSystem':'Actual Blender world XYZ; source vehicle longitudinal X, transverse Y, vertical Z. Root matrices retained for audit.','scope':'Active renderable descendants of the actual chassis root; no factory acceptance. Mirror-excluded envelope is a separate named subset, not a claim about official dimensional conventions. Hidden/nonassembly names are retained.','files':rows}
 (OUT/'native-envelopes.json').write_text(json.dumps(report,indent=2)+'\n')
 print(filename,json.dumps(rows[-1]['allActive']),flush=True)
