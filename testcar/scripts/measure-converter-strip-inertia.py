"""Mass properties of the current saved roller and periodically repeated pocket."""
import bpy,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];source=ROOT/'outputs/MAZ543A_Converter_CurvedStripStudy.blend';density=7850.
bpy.ops.wm.open_mainfile(filepath=str(source))
def properties(name):
    mesh=bpy.data.objects[name].data;mesh.calc_loop_triangles();volume=0.;moment=0.
    for tri in mesh.loop_triangles:
        a,b,c=[mesh.vertices[i].co for i in tri.vertices];v=a.dot(b.cross(c))/6;volume+=v
        moment+=v/10*sum(a[k]**2+b[k]**2+c[k]**2+a[k]*b[k]+a[k]*c[k]+b[k]*c[k] for k in [1,2])
    assert volume>0 and moment>0
    return {'name':name,'volumeM3':volume,'massKg':density*volume,'axialInertiaKgM2':density*moment}
roller=properties('CS_roller_12_5x22');sector=properties('CS_outer_pocket')
report={'nativeSha256':hashlib.sha256(source.read_bytes()).hexdigest(),'densityKgM3':density,'roller':roller,'sector':sector,
 'repeatedSectors':12,'outerInertiaKgM2':12*sector['axialInertiaKgM2'],
 'limits':'Current fitted sector repeated twelve times; uniform fitted steel density. No reactors, actual thrust rings, screws, fluid or factory assembly-inertia acceptance.'}
(ROOT/'outputs/converter-strip-inertia.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps(report,indent=2))
