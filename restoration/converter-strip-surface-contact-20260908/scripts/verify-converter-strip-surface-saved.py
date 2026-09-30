"""Read back every saved surface equilibrium against its independent solver row."""
import bpy,bmesh,json,sys,math
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from converter_strip_mesh import geometry
data=json.loads((ROOT/'work/freewheel-contact/strip-surface-verified-domain.json').read_text());fit=data['fit']
target=ROOT/'outputs/MAZ543A_Converter_StripSurfaceStudy.blend'
bpy.ops.wm.open_mainfile(filepath=str(target))
strip=bpy.data.objects['CS_curved_strip'];roller=bpy.data.objects['CS_roller_12_5x22'];checks=[]
for i,row in enumerate(data['rows']):
    bpy.context.scene.frame_set(i);bpy.context.view_layer.update()
    ob=strip.evaluated_get(bpy.context.evaluated_depsgraph_get());actual=ob.to_mesh()
    vertices,_=geometry(row['solution']['points'],fit['widthM'],fit['thicknessM'])
    error=max(math.dist(tuple(ob.matrix_world@v.co),(x,-z,y)) for v,(x,y,z) in zip(actual.vertices,vertices))
    y,z=row['centreM'];roller_error=math.dist(tuple(roller.matrix_world.translation),(0,-z,y))
    bm=bmesh.new();bm.from_mesh(actual);closed=all(e.is_manifold for e in bm.edges);volume=bm.calc_volume();bm.free();ob.to_mesh_clear()
    r={'frame':i,'maximumVertexErrorM':error,'rollerCentreErrorM':roller_error,'closed':closed,'volumeM3':volume}
    r['valid']=len(vertices)==len(strip.data.vertices) and error<8e-9 and roller_error<8e-9 and closed and volume>0
    checks.append(r)
report={'file':str(target),'states':len(checks),'checks':checks,'limits':bpy.data.objects['S543_CURVED_STRIP_STUDY']['limits']}
(ROOT/'outputs/converter-strip-surface-saved-native.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print(json.dumps({'states':len(checks),'failures':[r for r in checks if not r['valid']],'maxError':max(r['maximumVertexErrorM'] for r in checks)}),flush=True)
assert all(r['valid'] for r in checks)
