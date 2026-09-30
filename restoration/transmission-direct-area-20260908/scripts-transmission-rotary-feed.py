"""Executed inside blender-transmission.py after base geometry construction.
Source: fixed support50 feeds rotating body46 through step-joint cast rings.
All local dimensions, bearing counts and drilled routes remain reconstructed.
"""
def remove_tx(name):
    ob=bpy.data.objects.get(name)
    if ob:
        if name in REG:REG.remove(name)
        bpy.data.objects.remove(ob,do_unlink=True)

def bore_tx(target,cutter):
    # Lathe cylinders have duplicate pole vertices. Boolean tools must be
    # closed solids before intersection, especially for blind drilled ends.
    bm=bmesh.new();bm.from_mesh(cutter.data)
    bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-8)
    bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=1e-10)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    assert all(e.is_manifold for e in bm.edges),cutter.name
    bm.to_mesh(cutter.data);bm.free()
    bpy.context.view_layer.objects.active=target;bpy.context.view_layer.update()
    mod=target.modifiers.new('Machined rotary oil passage','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cutter
    bpy.ops.object.modifier_apply(modifier=mod.name)
    remove_tx(cutter.name)

def drill_cutter(length,radius,centre,axis='x'):
    # Two polygonal caps avoid coplanar fan triangles at blind drill ends.
    vs=[];n=48
    for d in [-length/2,length/2]:
        for j in range(n):
            a=(j+.37)*2*pi/n;u=radius*cos(a);v=radius*sin(a)
            p=(d,u,v) if axis=='x' else (u,d,v)
            vs.append(tuple(p[k]+centre[k] for k in range(3)))
    fs=[tuple(reversed(range(n))),tuple(range(n,n*2))]
    fs += [(j,(j+1)%n,(j+1)%n+n,j+n) for j in range(n)]
    return mesh('TX_rotary_bore_cutter',vs,fs,STEEL,None)

def axial_hole(target,x0,x1,radius,radial,angle=0):
    cutter=drill_cutter(x1-x0,radius,((x0+x1)/2,radial*cos(angle),radial*sin(angle)))
    bore_tx(target,cutter)

def radial_hole(target,x,r0,r1,radius,angle=0):
    cutter=drill_cutter(r1-r0,radius,(x,(r0+r1)/2,0),axis='y')
    cutter.rotation_euler.x=angle;bore_tx(target,cutter)

# Return spring guide rods carry the second pack's fixed seats into case47.
# They occupy the existing coil/seat centre holes, clearing the rotating sleeve.
remove_tx('TX_second_spring_support_hoop')
for j in range(8):
    a=j*pi/4;pos=(.096*cos(a),.096*sin(a))
    remove_tx(f'TX_second_anchor_{j}');remove_tx(f'TX_second_spring_guide_{j}')
    cylinder(f'TX_second_spring_guide_{j}',.0012,.048,(-.217,*pos),STEEL,root,n=24)
    cylinder(f'TX_second_anchor_{j}',.0025,.0015,(-.19410,*pos),FORGED,root,n=32)

body46=empty('TX_rotating_body46',ring18)
body46['sourceId']='MAZ 1973 fig.42 item46 and 000-0721.jpg'
support50=empty('TX_fixed_support50',case47)
support50['sourceId']='MAZ 1973 fig.42 item50 and 000-0721.jpg'
neck=ring('TX_direct_body46_sleeve',.105,.102,.091,(-.1895,0,0),FORGED,body46,n=192)
for j in range(8):
    cutter=box('TX_rotary_slot_cutter',(.009,.011,.004),(-.1755,.1035,0),STEEL,None,edge=0);cutter.rotation_euler.x=j*pi/4
    bore_tx(neck,cutter)

# Piston 45 uses an outboard annular pressure flange. Its original pressure
# face and 4.5 mm stroke are retained; the local front skirt clears the drum.
remove_tx('TX_direct_annular_piston')
for name in ['TX_direct_piston_seal_0','TX_direct_piston_seal_1']:remove_tx(name)
piston=bpy.data.objects['TX_piston_direct']
profile=[(-.1875,.0955),(-.1875,.1015),(-.1866,.1015),(-.1866,.1009),(-.1854,.1009),(-.1854,.1015),
         (-.1845,.1015),(-.1845,.0985),(-.180,.0985),(-.179,.0965),(-.176,.0965),(-.176,.0473),
         (-.1772,.0473),(-.1772,.0445),(-.180,.0445),(-.180,.0955)]
lathe('TX_direct_annular_piston',profile,(0,0,0),FORGED,piston,closed=True,n=192)
for ob in list(bpy.data.objects):
    if ob.name.startswith('TX_direct_reaction_drum_'):
        axial_hole(ob,-.185,-.1744,.099,0)
wall=ring('TX_direct_booster_back_wall',.105,.093,.002,(-.1915,0,0),FORGED,body46,n=192)
guide=lathe('TX_direct_booster_inner_guide',[(-.1905,.093),(-.1905,.095),(-.1816,.095),(-.1816,.0944),
    (-.1804,.0944),(-.1804,.095),(-.18025,.095),(-.18025,.093)],(0,0,0),FORGED,body46,closed=True,n=192)
for name,x,r,parent in [('outer_moving',-.186,.1015,piston),('inner_fixed',-.181,.095,body46)]:
    ob=lathe('TX_direct_piston_seal_'+name,[(x+.0005*cos(k*pi/12),r+.0005*sin(k*pi/12)) for k in range(24)],(0,0,0),RUBBER,parent,closed=True,n=192)
    ob['sealInterface']='direct booster rubber seal; nominal geometry, no elasticity solve'

# Static journal with two ring grooves and a complete circumferential oil band.
profile=[(-.239,.090),(-.239,.1015),(-.2339,.1015),(-.2339,.1007),(-.2321,.1007),(-.2321,.1015),
         (-.231,.1015),(-.231,.1008),(-.228,.1008),(-.228,.1015),(-.2269,.1015),(-.2269,.1007),
         (-.2251,.1007),(-.2251,.1015),(-.222,.1015),(-.222,.090)]
journal=lathe('TX_direct_support50_journal',profile,(0,0,0),FORGED,support50,closed=True,n=192)
IRON=mat('TX_cast_iron_feed_rings',(.075,.08,.08),.78,.4)

def step_ring(name,centre):
    # A true Z-shaped open joint: different circumferential slots in the two
    # axial halves, connected by a 40 micrometre middle slit. No solid O-ring.
    gap=.00004;half=gap/.102/2;left=pi-.01;right=pi+.01
    angles=sorted(set([j*2*pi/192 for j in range(193)]+[left-half,left+half,right-half,right+half]))
    xs=[centre-.0008,centre-gap/2,centre+gap/2,centre+.0008];verts=[];ids={};faces={}
    def vid(x,r,a):
        co=(x,r*cos(a),r*sin(a));key=tuple(round(v,12) for v in co)
        if key not in ids:ids[key]=len(verts);verts.append(co)
        return ids[key]
    for row in range(3):
        for a,b in zip(angles,angles[1:]):
            mid=(a+b)/2
            cut=(abs(mid-left)<half if row==0 else left-half<mid<right+half if row==1 else abs(mid-right)<half)
            if cut:continue
            v=[vid(x,r,t) for x in [xs[row],xs[row+1]] for r in [.1008,.102] for t in [a,b]]
            for f in [(0,1,3,2),(4,6,7,5),(0,4,5,1),(2,3,7,6),(0,2,6,4),(1,5,7,3)]:
                face=tuple(v[i] for i in f);key=tuple(sorted(face))
                if key in faces:del faces[key]
                else:faces[key]=face
    ob=mesh(name,verts,list(faces.values()),IRON,support50)
    ob['sealInterface']='Cast iron rotary feed ring with open stepped joint; fitted end gap and dimensions'
    return ob
for j,x in enumerate([-.233,-.226]):step_ring(f'TX_direct_feed_seal_{j}',x)

# Fixed feed into the annular band; the body's separate drilled route rotates
# with ring18 and always intersects that band, without hose twisting.
angle=pi/8
ring('TX_direct_support50_inlet',.0035,.0008,.024,(-.251,.096*cos(angle),.096*sin(angle)),FORGED,support50,n=48)
for ob,r in [(journal,.0008),(bpy.data.objects['TX_case47_front_web'],.0008),(bpy.data.objects['TX_end_cover_-0.25'],.0035)]:
    axial_hole(ob,-.264,-.229,.0008 if ob!=bpy.data.objects['TX_end_cover_-0.25'] else r,.096,angle)
radial_hole(journal,-.2295,.0952,.1022,.0008,angle)
radial_hole(neck,-.2295,.1018,.1043,.0006)
axial_hole(neck,-.2303,-.1907,.0006,.1035)
radial_hole(wall,-.1915,.0982,.1043,.0006)
axial_hole(wall,-.193,-.189,.0006,.099)
axial_hole(wall,-.193,-.1907,.0006,.1035)
radial_hole(neck,-.1915,.0982,.1043,.0006)

# Bearing at support50: reconstructed grooved races and kinematically rolling
# balls. Clearance and ball count are fitted; contact loads remain unsolved.
x=-.2195;R=.109;ball=.0015
inner=[(x-.0018,.105),(x-.0018,.1082)]
inner += [(x+u,R-sqrt(.00152**2-u*u)-.00002) for u in [-.0012+i*.0024/24 for i in range(25)]]
inner += [(x+.0018,.1082),(x+.0018,.105)]
outer=[(x-.0018,.113),(x-.0018,.1098)]
outer += [(x+u,R+sqrt(.00152**2-u*u)+.00002) for u in [-.0012+i*.0024/24 for i in range(25)]]
outer += [(x+.0018,.1098),(x+.0018,.113)]
lathe('TX_direct_feed_bearing_inner',inner,(0,0,0),STEEL,body46,closed=True,n=192)
lathe('TX_direct_feed_bearing_outer',outer,(0,0,0),STEEL,support50,closed=True,n=192)
for j in range(4):
    ob=box(f'TX_direct_support50_arm_{j}',(.002,.122,.005),(x,.174,0),FORGED,support50,edge=0);ob.rotation_euler.x=j*pi/2
cage=empty('TX_feed_bearing_cage',root)
for sign in [-1,1]:
    ring(f'TX_feed_cage_rail_{sign}',.10935,.10865,.00025,(x+sign*.00165,0,0),FORGED,cage,n=192)
for j in range(14):
    ob=box(f'TX_feed_cage_bridge_{j}',(.0033,.0006,.0006),(x,.109,0),FORGED,cage,edge=0)
    ob.rotation_euler.x=(j+.5)*2*pi/14
for j in range(14):
    a=j*2*pi/14;parent=empty(f'TX_feed_ball_{j}',cage,(x,R*cos(a),R*sin(a)))
    bm=bmesh.new();bmesh.ops.create_icosphere(bm,subdivisions=3,radius=ball)
    data=bpy.data.meshes.new(f'TX_feed_ball_mesh_{j}');bm.to_mesh(data);bm.free();data.materials.append(STEEL)
    ob=bpy.data.objects.new(f'TX_feed_ball_{j}_surface',data);bpy.context.collection.objects.link(ob);ob.parent=parent
    for p in data.polygons:p.use_smooth=True
    tag(ob,'Reconstructed rotary support bearing ball')

for ob in list(body46.children_recursive)+list(support50.children_recursive):
    ob['dimensionStatus']='Source topology, reconstructed local profiles, routes and bearing dimensions; not factory CAD or load acceptance.'
