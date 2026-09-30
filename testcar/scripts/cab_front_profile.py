"""Photographic lower-inner cab relief; fitted depth, not a factory dimension.

The museum front photo shows a wider lower opening than the gap at roof height.
Original reconstruction kept both at about 1.11 m. Retain the roof/window layout
and widen only the inner lower shell strip; hidden longitudinal continuation is
still fitted and must be checked against an opened-cab photo.
"""
import bpy,bmesh,json
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
SOURCE='https://commons.wikimedia.org/wiki/File:MAZ-543_special_purpose_truck,_Strategic_Missile_Forces_Museum.JPG'

def rebuild_facade(o,side):
    # Triangulate the 2D shell around the real aperture and split at the nose
    # slope break before mapping to 3D. Matched rings alone create twisted quads.
    prepared=json.loads((ROOT/'work/cab-front-profile.json').read_text())
    vs=[(-5.45+max(0,h-1.94)*.40-depth,-side*(.535+u),h) for u,h,depth in prepared['vertices']]
    fs=prepared['faces']
    data=bpy.data.meshes.new(o.name+'_PhotoProfile');data.from_pydata(vs,[],fs);data.update()
    bm=bmesh.new();bm.from_mesh(data)
    for v in bm.verts:v.co=o.matrix_world.inverted()@v.co
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(data);bm.free()
    for m in o.data.materials:data.materials.append(m)
    o.data=data

def apply_front_profile():
    changed=[]
    for o in list(bpy.data.objects):
        shell=any(o.name in [f'BL_Cab_{s}_front_shell',f'BL_Cab_{s}_inner_wall'] or o.name.startswith(f'BL_Cab_{s}_nose_rivets') for s in [-1,1])
        grille=o.name.startswith('BL_Radiator_')
        if not (shell or grille) or o.get('cabFrontProfileVersion')==1:continue
        if o.type=='CURVE':
            bpy.ops.object.select_all(action='DESELECT');o.hide_set(False);o.select_set(True);bpy.context.view_layer.objects.active=o
            bpy.ops.object.convert(target='MESH');o=bpy.context.object
        if o.type!='MESH':continue
        if o.name.endswith('_front_shell'):
            rebuild_facade(o,-1 if o.name.startswith('BL_Cab_-1_') else 1)
            o['cabFrontProfileVersion']=1;o['sourceURL']=SOURCE
            o['dimensionStatus']='Front-photo lower contour fit; window unchanged. Hidden depth and exact measurements unresolved.'
            changed.append({'name':o.name,'rebuiltAroundActualAperture':True})
            continue
        world=o.matrix_world.copy();inverse=world.inverted()
        bm=bmesh.new();bm.from_mesh(o.data)
        for v in bm.verts:v.co=world@v.co
        if shell and not 'nose_rivets' in o.name:
            # Insert the two actual fold stations; do not let an n-gon choose
            # an arbitrary diagonal through a newly non-planar wall.
            for height in [1.92,2.18]:
                bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=1e-7,
                                      plane_co=(0,0,height),plane_no=(0,0,1),clear_inner=False,clear_outer=False)
        moved=0
        for v in bm.verts:
            p=v.co.copy()
            if grille:p.y*=1.10
            else:
                height=max(0,min(1,(2.18-p.z)/.26))
                inner=max(0,min(1,(.82-abs(p.y))/.265))
                p.y+=(1 if p.y>=0 else -1)*.19*height*inner
            if (p-v.co).length>1e-9:moved+=1
            v.co=inverse@p
        bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free();o.data.update()
        o['cabFrontProfileVersion']=1;o['sourceURL']=SOURCE
        o['dimensionStatus']='Front-photo proportion fit. Lower gap about 1.49 m; relief transition, hidden depth and radiator width unmeasured.'
        changed.append({'name':o.name,'changedVertices':moved})
    return changed

if __name__=='__main__':
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'outputs/MAZ543A_Master.blend'));bpy.context.scene.frame_set(0)
    changed=apply_front_profile()
    (ROOT/'outputs/cab-front-profile-changes.json').write_text(json.dumps(changed,indent=2))
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'outputs/MAZ543A_CabFit_Study.blend'),compress=True)
    print('CAB_PROFILE_STUDY',len(changed),'objects',flush=True)
