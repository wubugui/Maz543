"""Source-indexed timing train; execute in blender-d12.py mesh namespace.

MAZ-543 1973 fig.7 supplies topology, teeth and speed magnitudes. Shaft positions,
modules, tooth form, bearings and coupling sizes are explicitly reconstructions.
"""
from mathutils import Matrix
TIMING=POSES['timing'];BEVEL=json.loads((ROOT/'work/bevel-profiles.json').read_text())
SPURS=json.loads((ROOT/'work/timing-spurs.json').read_text())['sections']
CAPS=json.loads((ROOT/'work/timing-caps.json').read_text())

def timing_basis(axis):
    u=Vector(axis).normalized();ref=Vector((0,1,0) if abs(u.x)>.9 else (1,0,0))
    v=(ref-u*ref.dot(u)).normalized();return u,v,u.cross(v)

def timing_tag(ob,part,role='timing-internal'):
    ob['d12Part']=part;ob['sourceId']='MAZ-1973-F7';ob['d12Role']=role;ob['timingTrain']=True
    ob['dimensionStatus']='Original MAZ teeth and topology; shaft positions, profiles and dimensions reconstructed'
    return ob

def local_point(world,shaft):
    p=Vector(world)-Vector(shaft['origin']);return tuple(p.dot(v) for v in timing_basis(shaft['axis']))

def gear_point(point,gear,shaft):
    x,y,z=point;a=gear['phase'];y,z=y*cos(a)-z*sin(a),y*sin(a)+z*cos(a)
    u,v,w=timing_basis(gear['axis'])
    return local_point(Vector(gear['origin'])+u*x+v*y+w*z,shaft)

def build_timing_gear(id,gear):
    sh=TIMING['shafts'][gear['shaft']];parent=bpy.data.objects[sh['node']];vs=[];fs=[]
    if gear['kind']=='bevel':
        data=BEVEL[gear['profile']];outer=data[gear['member']];n=len(outer)
        delta=data['delta' if gear['member']=='A' else 'Delta'];bore=gear['bore']
        for scale in [data['innerScale'],1.]:
            R=data['R']*scale
            for y,z in outer:
                v=Vector((1,y,z)).normalized()*R;vs.append(gear_point(v,gear,sh))
            for j in range(96):
                a=j*2*pi/96;vs.append(gear_point((R*cos(delta),bore*cos(a),bore*sin(a)),gear,sh))
        count=n+96
        # Swept roots may be undercut, so a radial quad fan can cross a tooth
        # space. Constrained triangulation preserves the actual angular outline.
        fs.extend(tuple(reversed(f)) for f in CAPS[id][0])
        fs.extend(tuple(j+count for j in f) for f in CAPS[id][1])
        for j in range(n):
            k=(j+1)%n
            fs.append((j,j+count,k+count,k))
        for j in range(96):
            k=(j+1)%96;fs.append((n+j,n+k,n+k+count,n+j+count))
    else:
        data=SPURS[id];n=len(data['vertices']);out=data['outer']
        for x in [-.007,.007]:
            for y,z in data['vertices']:vs.append(gear_point((x,y,z),gear,sh))
        for f in data['faces']:fs.extend([tuple(reversed(f)),tuple(i+n for i in f)])
        for lo,hi in [(0,out),(out,n)]:
            for j in range(lo,hi):
                k=lo+(j-lo+1)%(hi-lo);fs.append((j,k,k+n,j+n))
    name='D12_cam_24_bevel_'+id[-1] if id.startswith('cam24_') else 'D12_timing_gear_'+id
    ob=mesh(name,vs,fs,POLISH,parent,source='MAZ-1973-F7',role='timing-internal')
    timing_tag(ob,id);ob['timingGearId']=id;ob['toothCount']=gear['teeth'];ob['moduleFit']=gear['module'];ob['phaseFit']=gear['phase']
    ob['toothGeometry']='Spherical involute with swept root relief' if gear['kind']=='bevel' else 'Planar involute with swept root relief'
    if id.startswith('cam24_'):
        ob['camTrain']=True;ob['camBank']=id[-1]
    return ob

def build_timing_train():
    for id,sh in TIMING['shafts'].items():
        if sh['existing']:continue
        u,v,w=timing_basis(sh['axis']);mount=empty(sh['node']+'_mount',root,sh['origin'])
        mount.rotation_mode='QUATERNION';mount.rotation_quaternion=Matrix((C(u),-C(w),C(v))).transposed().to_quaternion()
        mount['timingMount']=True
        joint=empty(sh['node'],mount);joint['timingShaft']=id;joint['crankRatio']=sh['rate']
    for id,g in TIMING['gears'].items():
        if id.startswith(('intake22','exhaust22')):
            bank=id[-1];kind='intake' if id.startswith('intake') else 'exhaust'
            ob=bpy.data.objects[f'D12_cam_22_spur_{bank}_{kind}'];ob['timingGearId']=id;ob['timingTrain']=True
            continue
        build_timing_gear(id,g)
    # Stepped hollow shafts through each modeled gear bore. The two inclined
    # shafts and vertical shaft end at the pitch apex; gear bodies face away.
    spans={'upper':(.030,.490,.0075),'lower':(.030,.288,.0075),
           'generator_takeoff':(.033,.340,.0075),'generator':(.018,.535,.0068),
           'inclined_L':(.042,.610,.0068),'inclined_R':(.042,.610,.0068),
           'oil_idler':(-.014,.030,.0075),'oil_pump':(-.015,.115,.007),
           'fuel_takeoff':(-.010,.064,.0055),'fuel_feed':(.009,.115,.0055)}
    for id,(lo,hi,r) in spans.items():
        sh=TIMING['shafts'][id];joint=bpy.data.objects[sh['node']];mount=joint.parent
        shaft=ring('D12_timing_shaft_'+id,r,r*.40,hi-lo,((hi+lo)/2,0,0),STEEL,joint,n=48,source='MAZ-1973-F7')
        timing_tag(shaft,id+' hollow drive shaft')
        # Concentric machined bearing lands and open bronze bushes; no solid
        # placeholder cylinders through the operating shafts.
        bearings=([.122,.447] if id.startswith('inclined') else [.092,.405] if id=='upper' else [.074,.260] if id=='lower' else [.103,.270] if id=='generator_takeoff' else [])
        for k,d in enumerate(bearings):
            land=ring(f'D12_timing_land_{id}_{k}',r+.0015,r*.40,.017,(d,0,0),POLISH,joint,n=48,source='MAZ-1973-F7');timing_tag(land,id+' bearing journal')
            bush=ring(f'D12_timing_bush_{id}_{k}',r+.0045,r+.00155,.019,(d,0,0),BRONZE,mount,n=48,source='MAZ-1973-F7');timing_tag(bush,id+' open plain bearing')
            housing=ring(f'D12_timing_bearing_body_{id}_{k}',r+.013,r+.00455,.025,(d,0,0),CAST,mount,n=64,source='MAZ-1973-F7',role='timing-housing');timing_tag(housing,id+' bearing carrier','timing-housing')
        # Visible shaft collars and lock rings are separately editable pieces.
        for k,d in enumerate([lo+.003,hi-.003]):
            collar=ring(f'D12_timing_collar_{id}_{k}',r+.0018,r,.004,(d,0,0),POLISH,joint,n=48,source='MAZ-1973-F7');timing_tag(collar,id+' shaft collar')
    # Drive stubs meet existing injection and crank axes without moving those
    # established semantic pivots. Pump/generator internals remain separate work.
    for id,lo,hi,r in [('injection',-.654,-.45,.0105),('crank',-.662,-.56,.0295)]:
        sh=TIMING['shafts'][id];ob=ring('D12_timing_stub_'+id,r,r*.4,hi-lo,((lo+hi)/2,0,0),STEEL,bpy.data.objects[sh['node']],n=64,source='MAZ-1973-F7');timing_tag(ob,id+' drive stub')
    root['timingRevision']=1
