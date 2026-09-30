"""Fitted return spring and seats matching the axial contact reconstruction.

Original section establishes a return spring, not these local dimensions.
The spring is ahead of both needle-bearing rows, within the magnet bore.
"""
import bpy,bmesh,json,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
S=json.loads((ROOT/'work/cooling-poses.json').read_text())['spec']

def update_springs():
    for i in range(2):
        coil=bpy.data.objects[f'COOL_release_spring_{i}'];mat=coil.data.materials[0]
        curve=bpy.data.curves.new(coil.name+'_compression_profile','CURVE');curve.dimensions='3D';curve.bevel_depth=S['releaseSpringWire'];curve.bevel_resolution=3
        spline=curve.splines.new('POLY');spline.points.add(200)
        for j,p in enumerate(spline.points):
            a=j/200*S['releaseSpringTurns']*math.tau
            p.co=(j/200*S['releaseSpringLength'],-S['releaseSpringRadius']*math.sin(a),S['releaseSpringRadius']*math.cos(a),1)
        curve.materials.append(mat);coil.data=curve
        coil['dimensionStatus']='Fitted 49 mm mean diameter, 1.4 mm wire, 5 turns, 10 mm installed length; not measured MAZ spring.'
        coil['springRateNperM']=S['axialSpringRate'];coil['preloadN']=S['clutchSpringForce']
        for part,parent,x0,x1,inner,outer in [
            ('shaft_seat',bpy.data.objects[f'COOL_armature_{i}'],-.0182,-.0162,.018,.026),
            ('fan_seat',bpy.data.objects[f'COOL_fan_{i}'],-.0048,-.0028,.0215,.031)]:
            name=f'COOL_release_{part}_{i}';old=bpy.data.objects.get(name)
            if old:bpy.data.objects.remove(old,do_unlink=True)
            n=64;verts=[(x,r*math.cos(j*math.tau/n),r*math.sin(j*math.tau/n)) for x in [x0,x1] for r in [inner,outer] for j in range(n)];faces=[]
            for j in range(n):
                k=(j+1)%n;faces.extend([(j,k,n+k,n+j),(2*n+j,3*n+j,3*n+k,2*n+k),(j,2*n+j,2*n+k,k),(n+j,n+k,3*n+k,3*n+j)])
            m=bpy.data.meshes.new(name);m.from_pydata(verts,[],faces);m.update();bm=bmesh.new();bm.from_mesh(m);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(m);bm.free()
            o=bpy.data.objects.new(name,m);parent.users_collection[0].objects.link(o);o.parent=parent;m.materials.append(mat)
            o['coolingPart']='Fitted release spring seat';o['coolingRole']='cooling-internal';o['sourceId']='MAZ-1973-F31, spring function; local seat profile not established';o['dimensionStatus']='Fitted annular seats around shaft and magnet bore; source photo/dimensions unverified.'

if __name__=='__main__':
    path=ROOT/'outputs/MAZ543A_Cooling_Master.blend';bpy.ops.wm.open_mainfile(filepath=str(path));update_springs()
    root=bpy.data.objects['S543_COOLING'];report=[dict(name=o.name,role=o.get('coolingRole'),source=o.get('sourceId'),dimensions=o.get('dimensionStatus')) for o in root.children_recursive if o.type in ['MESH','CURVE']]
    (ROOT/'outputs/cooling-parts-register.json').write_text(json.dumps(report,indent=2))
    bpy.context.scene.frame_set(0);bpy.ops.wm.save_as_mainfile(filepath=str(path),compress=True)
    print('CLUTCH_COMPRESSION_SPRINGS',len(report),flush=True)
