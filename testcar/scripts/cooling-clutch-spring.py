"""Fitted return spring and seats matching the axial contact reconstruction.

Original section establishes a return spring, not these local dimensions.
The spring is ahead of both needle-bearing rows, within the magnet bore.
"""
import bpy,bmesh,json,math,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
S=json.loads((ROOT/'work/cooling-poses.json').read_text())['spec']
sys.path.insert(0,str(ROOT/'scripts'))
from cooling_spring_geometry import parameters,vertices,STEPS,SIDES,PITCH_KEY,RADIUS_KEY,bake_springs

def update_springs():
    for i in range(2):
        old=bpy.data.objects[f'COOL_release_spring_{i}'];mat=old.data.materials[0]
        name=old.name;parent=old.parent;basis=old.matrix_basis.copy();collections=list(old.users_collection);props=dict(old.items())
        bpy.data.objects.remove(old,do_unlink=True)
        length,radius,arc,end_radius=parameters(S,0)
        mesh=bpy.data.meshes.new(name+'_round_wire');faces=[]
        for row in range(STEPS):
            for j in range(SIDES):
                k=(j+1)%SIDES;a=row*SIDES;b=(row+1)*SIDES
                faces.append((a+j,a+k,b+k,b+j))
        faces.extend([tuple(range(SIDES-1,-1,-1)),tuple(STEPS*SIDES+j for j in range(SIDES))])
        mesh.from_pydata(vertices(S,length,radius,arc),[],faces);mesh.update();mesh.materials.append(mat)
        coil=bpy.data.objects.new(name,mesh)
        for col in collections:col.objects.link(coil)
        coil.parent=parent;coil.matrix_basis=basis
        for key,value in props.items():coil[key]=value
        for polygon in mesh.polygons:polygon.use_smooth=len(polygon.vertices)==4
        coil.shape_key_add(name='Basis')
        for key_name,L,R in [(PITCH_KEY,length-S['clutchTravel'],radius),(RADIUS_KEY,length,end_radius)]:
            key=coil.shape_key_add(name=key_name)
            for point,co in zip(key.data,vertices(S,L,R,arc)):point.co=co
        parent.scale=(1,1,1)
        # Existing affine scale tracks must not distort the circular wire.
        if parent.animation_data and parent.animation_data.action:
            action=parent.animation_data.action
            for fc in list(action.fcurves):
                if fc.data_path=='scale':action.fcurves.remove(fc)
        coil['parametricSpring']=True
        coil['deformation']='Analytic helix: circular normal sections and constant centreline arc length; fitted dimensions, not elastic FEA.'
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
    bake_springs(json.loads((ROOT/'work/cooling-poses.json').read_text())['frames'],S)
    root=bpy.data.objects['S543_COOLING'];report=[dict(name=o.name,role=o.get('coolingRole'),source=o.get('sourceId'),dimensions=o.get('dimensionStatus')) for o in root.children_recursive if o.type in ['MESH','CURVE']]
    (ROOT/'outputs/cooling-parts-register.json').write_text(json.dumps(report,indent=2))
    bpy.context.scene.frame_set(0);bpy.ops.wm.save_as_mainfile(filepath=str(path),compress=True)
    print('CLUTCH_COMPRESSION_SPRINGS',len(report),flush=True)
