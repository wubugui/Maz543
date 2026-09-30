"""Integrate saved closed mesh tetrahedra; density is an explicit steel fit."""
import bpy,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];density=7850
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'outputs/MAZ543A_Converter_Freewheels.blend'))
bpy.context.scene.frame_set(0)
def properties(ob):
    m=ob.data;m.calc_loop_triangles();volume=0;moment=0
    # Mesh-local roller coordinates are centred at its own axis. Race and
    # retainer meshes are centred on the shared X shaft, as in the saved file.
    for tri in m.loop_triangles:
        a,b,c=[m.vertices[i].co for i in tri.vertices];v=a.dot(b.cross(c))/6;volume+=v
        moment+=v/10*sum(a[k]*a[k]+b[k]*b[k]+c[k]*c[k]+a[k]*b[k]+a[k]*c[k]+b[k]*c[k] for k in [1,2])
    assert volume>0 and moment>0,ob.name
    return {'node':ob.name,'volumeM3':volume,'massKg':density*volume,'axialInertiaKgM2':density*moment}
parts=[properties(bpy.data.objects['CV_front_roller_0'])]+[properties(bpy.data.objects[n]) for n in ['CV_front_wedged_outer_race','CV_front_retainer_-1','CV_front_retainer_1']]
report={'densityKgM3':density,'roller':parts[0],'outerAssemblyInertiaKgM2':sum(p['axialInertiaKgM2'] for p in parts[1:]),'parts':parts,
 'limits':'Closed native-mesh mass integrals using fitted uniform steel density. Outer assembly excludes unbuilt reactor blades, screws and fluid entrainment. No factory inertia measurement.'}
(ROOT/'outputs/converter-freewheel-inertia.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps(report,indent=2))
