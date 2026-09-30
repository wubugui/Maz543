"""MAZ 1973 fig.28 pump, executed in the blender-d12 helper namespace.

Native editable wet cavities, six stamped blades, seal stack and rolling bearings.
Every local dimension, blade sweep and bearing designation is reconstruction data.
"""
from mathutils import Matrix

def water_tag(ob,label=None,role='water-internal',figure=None):
    ob['waterPump']=True;ob['d12Part']=label or ob.name
    ob['sourceId']='MAZ-1973-F28';ob['d12Role']=role
    ob['dimensionStatus']='Original six blades / two bearings / seal topology; all local dimensions and bearing ball count fitted'
    if figure is not None:ob['figureItem']=str(figure)
    return ob

def water_boolean(ob,cutter,op='DIFFERENCE'):
    bpy.context.view_layer.update();bpy.context.view_layer.objects.active=ob
    m=ob.modifiers.new('Wet passage '+op,'BOOLEAN');m.operation=op;m.solver='EXACT';m.object=cutter
    bpy.ops.object.modifier_apply(modifier=m.name);bpy.data.objects.remove(cutter,do_unlink=True)

def water_split(ob):
    # Two real solids, with filled section faces; the full assembly stays closed.
    for side in [-1,1]:
        copy=ob.copy();copy.data=ob.data.copy();bpy.context.collection.objects.link(copy)
        copy.name=ob.name+('_far' if side<0 else '_near');copy['waterHalf']=side
        bm=bmesh.new();bm.from_mesh(copy.data)
        cut=bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=1e-8,plane_co=(0,0,0),plane_no=C((0,0,1)),clear_inner=side>0,clear_outer=side<0)
        edges=[e for e in cut['geom_cut'] if isinstance(e,bmesh.types.BMEdge) and e.is_boundary]
        if edges:bmesh.ops.holes_fill(bm,edges=edges,sides=0)
        bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(copy.data);bm.free()
    bpy.data.objects.remove(ob,do_unlink=True)

def build_water_pump():
    spec=POSES['waterPump'];mount=empty('D12_water_mount',root,spec['origin']);mount['waterMount']=True
    # Local X follows the lower timing shaft, downwards in the engine frame.
    u=Vector((0,-1,0));v=Vector((1,0,0));w=u.cross(v)
    mount.rotation_mode='QUATERNION';mount.rotation_quaternion=Matrix((C(u),-C(w),C(v))).transposed().to_quaternion()
    rotor=empty('D12_water_rotor',mount);water_tag(rotor,'Shaft and balanced impeller',figure=17)
    inox=mat('D12_water_stainless',(.26,.28,.27),.91,.32)
    carbon=mat('D12_water_seal_carbon',(.038,.039,.035),.2,.32)
    for m in [inox,carbon]:m['dimensionStatus']='Material family only; finish not measured'
    def L(name,profile,material,parent=mount,**kw):return water_tag(lathe('D12_water_'+name,profile,(0,0,0),material,parent,n=96,closed=True),**kw)
    def R(name,r,inside,length,x,material,parent=mount,**kw):return water_tag(ring('D12_water_'+name,r,inside,length,(x,0,0),material,parent,n=64),**kw)
    # Two spaced bearing seats, central seal chamber and annular wet volute.
    housing=L('housing',[(.006,.028),(.018,.031),(.069,.031),(.080,.037),(.099,.044),(.113,.066),(.108,.084),(.115,.099),(.151,.103),(.159,.098),(.159,.087),(.151,.089),(.143,.095),(.122,.091),(.121,.072),(.121,.030),(.113,.030),(.113,.026),(.085,.026),(.080,.020),(.071,.020),(.071,.025),(.016,.025),(.006,.025)],CAST,role='water-housing',figure=1)
    # Fitted two-start scroll grows into the two bank outlets. Neck stays circular.
    for vertex in housing.data.vertices:
        x,y,z=vertex.co.x,vertex.co.z,-vertex.co.y;r=math.hypot(y,z)
        if r>.071:
            a=math.atan2(z,y);extra=.005*(1-math.cos(2*a))/2
            vertex.co.y*=1+extra/r;vertex.co.z*=1+extra/r
    for s in [-1,1]:
        outer=cylinder('water_cast_port',.017,.058,(.134,0,s*.120),CAST,mount,'z',64)
        water_boolean(housing,outer,'UNION')
        bore=cylinder('water_bore',.012,.094,(.134,0,s*.104),CAST,mount,'z',64)
        water_boolean(housing,bore)
    # Machined centering boss and square flange. Stud holes are Boolean bores.
    flange=hollow_plate('D12_water_mount_flange',.038,.038,-.004,.006,.025,CAST,mount)
    # hollow_plate is Y-axial; rotate its actual geometry into the pump X axis.
    for vertex in flange.data.vertices:vertex.co=Vector((vertex.co.z,vertex.co.y,-vertex.co.x))
    water_tag(flange,role='water-housing',figure=1)
    for a in [-1,1]:
      for b in [-1,1]:
        hole=cylinder('water_stud_hole',.0042,.025,(.001,a*.029,b*.029),CAST,mount,n=32);water_boolean(flange,hole)
        water_tag(cylinder(f'D12_water_mount_stud_{a}_{b}',.0038,.025,(-.001,a*.029,b*.029),STEEL,mount),role='water-housing')
        water_tag(cylinder(f'D12_water_mount_nut_{a}_{b}',.0063,.005,(-.011,a*.029,b*.029),STEEL,mount,n=6),role='water-housing')
    water_split(flange)
    # Inspection telltale drain A between oil and water seals, actually bored.
    tell=cylinder('water_telltale_bore',.0023,.090,(.084,0,0),CAST,mount,'z',32);water_boolean(housing,tell)
    for j in range(4):
        keyway=box('water_seal_keyway',(.011,.008,.009),(.1165,.0315,0),CAST,mount,edge=0);keyway.rotation_euler.x=j*pi/2;water_boolean(housing,keyway)
    water_split(housing)
    bell=L('suction_bell',[(.160,.098),(.169,.098),(.169,.081),(.184,.057),(.207,.047),(.220,.029),(.222,.004),(.216,.004),(.214,.027),(.204,.041),(.181,.051),(.162,.066),(.160,.066)],CAST,role='water-housing')
    water_boolean(bell,cylinder('water_inlet_cast',.027,.074,(.194,-.062,0),CAST,mount,'y',64),'UNION')
    water_boolean(bell,cylinder('water_inlet_bore',.022,.101,(.194,-.055,0),CAST,mount,'y',64))
    water_split(bell)
    R('bell_gasket',.098,.087,.001,.1595,GASKET,role='water-housing')
    for j in range(8):
        a=(j+.5)*2*pi/8
        water_tag(cylinder(f'D12_water_bell_stud_{j}',.0028,.020,(.159,.093*cos(a),.093*sin(a)),STEEL,mount),role='water-housing')
        water_tag(cylinder(f'D12_water_bell_nut_{j}',.0048,.005,(.173,.093*cos(a),.093*sin(a)),STEEL,mount,n=6),role='water-housing')
    R('drain_union',.007,.004,.016,.222,BRONZE,role='water-housing')
    water_tag(cylinder('D12_water_drain_plug',.0075,.006,(.233,0,0),BRONZE,mount,n=6),role='water-housing')
    # Stepped shaft includes genuine bearing journals and threaded/splined nose.
    L('shaft', [(-.015,0),(-.015,.0065),(.012,.0065),(.014,.010),(.068,.010),(.069,.0115),(.079,.0115),(.091,.0085),(.123,.0085),(.125,.021),(.128,.021),(.128,0)],POLISH,rotor,figure=17)
    for j in range(10):
        a=j*2*pi/10
        o=water_tag(box(f'D12_water_drive_spline_{j}',(.012,.0015,.0016),(.004,.0072,0),POLISH,rotor,edge=.0002),figure=17);o.rotation_euler.x=a
    hub=R('drive_dog_hub',.025,.0066,.005,.0025,STEEL,rotor,figure=7)
    for j in range(10):
        slot=box('water_hub_spline_slot',(.009,.0017,.0018),(.0025,.00725,0),STEEL,rotor,edge=0);slot.rotation_euler.x=j*2*pi/10;water_boolean(hub,slot)
    water_tag(ring('D12_water_input_hub',.025,.0075,.004,(.280,0,0),STEEL,bpy.data.objects['D12_timing_lower'],n=64))
    for j in range(2):
        a=j*pi
        o=water_tag(box(f'D12_water_drive_dog_{j}',(.011,.010,.010),(-.005,.017,0),STEEL,rotor,edge=.001),figure=7);o.rotation_euler.x=a
        # Matching interdigitated driving lugs, coupled to the actual lower shaft.
        ob=water_tag(box(f'D12_water_input_dog_{j}',(.011,.010,.010),(.285,.017,0),STEEL,bpy.data.objects['D12_timing_lower'],edge=.001));ob.rotation_euler.x=a+pi/2
    R('lock_washer',.012,.0067,.0015,-.001,STEEL,rotor,figure=8)
    water_tag(cylinder('D12_water_castellated_nut',.011,.009,(-.008,0,0),STEEL,rotor,n=6),figure=9)
    # Nut slots and cotter are real geometry; central threaded shaft stays separate.
    nut=bpy.data.objects['D12_water_castellated_nut']
    water_boolean(nut,cylinder('water_nut_bore',.0066,.014,(-.008,0,0),STEEL,rotor,n=48))
    for j in range(3):
        cut=box('water_nut_slot',(.004,.030,.0022),(-.012,0,0),STEEL,rotor,edge=0);cut.rotation_euler.x=j*pi/3;water_boolean(nut,cut)
    water_tag(pipe('D12_water_cotter',[(-.012,-.012,0),(-.012,.012,0),(-.009,.013,.002),(-.006,.011,.003)],.0007,STEEL,rotor),figure=10)
    R('spacer',.013,.0101,.022,.0425,STEEL,rotor,figure=4)
    R('bearing_stop_ring',.0265,.021,.0014,.067,STEEL,figure=3)
    L('oil_thrower',[(.013,.0101),(.013,.030),(.010,.034),(.009,.034),(.0115,.029),(.0115,.0101)],STEEL,rotor,figure=5)
    R('spring_washer',.014,.0084,.0015,.0085,STEEL,rotor,figure=6)
    rp=spec['ballPitch'];br=spec['ballRadius'];groove=br+.000035
    for b,x in enumerate(spec['bearings']):
        race=[(-.0055,.0138)]+[(d,rp-math.sqrt(max(0,groove*groove-d*d))) for d in [(-1+2*j/32)*groove for j in range(33)]]+[(.0055,.0138)]
        L(f'inner_race_{b}',[(x-.0055,.010)]+[(x+d,r) for d,r in race]+[(x+.0055,.010)],POLISH,rotor,figure=2)
        outer=L(f'outer_race_{b}',[(x-.0055,.025),(x+.0055,.025)]+[(x+d,2*rp-r) for d,r in reversed(race)],POLISH,figure=2)
        water_split(outer)
        cage=empty(f'D12_water_cage_{b}',mount);water_tag(cage,'Bearing cage; count fitted',figure=2)
        for side in [-1,1]:R(f'cage_ring_{b}_{side}',rp+.0012,rp-.0012,.0007,x+side*.0038,BRONZE,cage,figure=2)
        for j in range(spec['balls']):
            a=j*2*pi/spec['balls'];pivot=empty(f'D12_water_ball_{b}_{j}',cage,(x,rp*cos(a),rp*sin(a)));water_tag(pivot,figure=2)
            bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=16,radius=br)
            ball=bpy.context.object;ball.name=f'D12_water_rolling_element_{b}_{j}';ball.parent=pivot;ball.location=(0,0,0);ball.data.materials.append(POLISH)
            for face in ball.data.polygons:face.use_smooth=True
            water_tag(ball,'Bearing ball; size/count fitted',figure=2)
            a+=pi/spec['balls'];water_tag(cylinder(f'D12_water_cage_rivet_{b}_{j}',.0009,.0076,(x,rp*cos(a),rp*sin(a)),BRONZE,cage,n=16),figure=2)
    L('oil_lip_seal',[(.072,.020),(.079,.020),(.079,.0115),(.077,.0115),(.075,.015),(.072,.015)],RUBBER,figure=11)
    R('lip_garter',.014,.0128,.001,.076,STEEL,figure=11)
    # Stationary bellows and spring press the four-tab washer onto rotating sleeve.
    profile=[(.085,.014)]
    for j in range(49):
        x=.085+j*.027/48;profile.append((x,.017+.002*(1-math.cos(j*pi/6))/2))
    profile +=[(.112,.014)]
    L('corrugated_gland',profile,RUBBER,figure=12)
    spring=[(.085+i/256*.026,.022*cos(i/256*2*pi*7),.022*sin(i/256*2*pi*7)) for i in range(257)]
    water_tag(pipe('D12_water_seal_spring',spring,.0011,STEEL,mount),figure=13)
    R('stationary_seal_washer',.027,.0092,.005,.1165,carbon,figure=14)
    R('rotating_wear_sleeve',.021,.0085,.005,.1215,POLISH,rotor,figure=16)
    for j in range(4):
        a=j*pi/2
        tab=water_tag(box(f'D12_water_seal_tab_{j}',(.005,.005,.007),(.1165,.028,0),carbon,mount,edge=.0002),figure=14);tab.rotation_euler.x=a
        pad=water_tag(box(f'D12_water_seal_buffer_{j}',(.006,.003,.008),(.1165,.032,0),RUBBER,mount,edge=.0005),figure=15);pad.rotation_euler.x=a
    # Stamped backing disk and six independently editable curved sheet blades.
    L('impeller_backplate',[(.128,.018),(.128,.083),(.1298,.083),(.1298,.018)],inox,rotor,figure=17)
    for j in range(6):
        a=j*pi/3;vs=[];fs=[];steps=32
        for side in [-1,1]:
          for k in range(steps+1):
            t=k/steps;r=.022+t*.060;theta=a+.52*t;th=.0006/r*side
            for x in [.1298,.150-.003*t]:vs.append((x,r*cos(theta+th),r*sin(theta+th)))
        n=(steps+1)*2
        for k in range(steps):
            q=k*2;fs +=[(q,q+2,q+3,q+1),(n+q+1,n+q+3,n+q+2,n+q),(q,n+q,n+q+2,q+2),(q+1,q+3,n+q+3,n+q+1)]
        fs +=[(0,1,n+1,n),(n-2,2*n-2,2*n-1,n-1)]
        water_tag(mesh(f'D12_water_impeller_blade_{j}',vs,fs,inox,rotor,edge=.00025,smooth=True),figure=17)
        water_tag(cylinder(f'D12_water_impeller_rivet_{j}',.0025,.004,(.128,.020*cos(a),.020*sin(a)),inox,rotor,n=24),figure=17)
    # Source-grounded circuit connectivity; coordinates still fitted to this model.
    for s in [-1,1]:
        control=[Vector(v) for v in [(-.665,-.355,s*.149),(-.665,-.355,s*.200),(-.50,.19,s*.241),(-.51,.398,s*.29)]]
        pts=[]
        for k in range(65):
            t=k/64;pts.append((1-t)**3*control[0]+3*t*(1-t)**2*control[1]+3*t*t*(1-t)*control[2]+t**3*control[3])
        vs=[];fs=[];n=32
        for i,p in enumerate(pts):
            tangent=(pts[min(i+1,64)]-pts[max(i-1,0)]).normalized();u=tangent.cross(Vector((1,0,0))).normalized();v=tangent.cross(u)
            for r in [.015,.012]:
                for j in range(n):vs.append(tuple(p+r*(cos(j*2*pi/n)*u+sin(j*2*pi/n)*v)))
        for i in range(64):
            for offset in [0,n]:
                for j in range(n):a=i*2*n+offset+j;b=i*2*n+offset+(j+1)%n;fs.append((a,b,b+2*n,a+2*n))
        for i in [0,64]:
            for j in range(n):a=i*2*n+j;b=i*2*n+(j+1)%n;fs.append((a,a+n,b+n,b))
        water_tag(mesh(f'D12_water_bank_supply_{s}',vs,fs,CAST,root,smooth=True),role='water-pipe')
    ground=mat('D12_water_ground_steel',(.16,.175,.16),.87,.39)
    for ob in bpy.data.objects:
        if not ob.get('waterPump') or ob.type!='MESH':continue
        if ob.data.materials and ob.data.materials[0]==POLISH:ob.data.materials[0]=ground
        bm=bmesh.new();bm.from_mesh(ob.data);bm.edges.ensure_lookup_table()
        sharp=[e.calc_face_angle(0)>.52 for e in bm.edges];bm.free()
        for p in ob.data.polygons:p.use_smooth=True
        for e,value in zip(ob.data.edges,sharp):e.use_edge_sharp=value
        # Machined annular end faces and section faces must remain planar.
        for p in ob.data.polygons:
            if abs(p.normal.x)>.99999 or (ob.get('waterHalf') and abs(p.normal.y)>.99999):p.use_smooth=False
    print('WATER_PUMP_AUTHORED',len([o for o in bpy.data.objects if o.get('waterPump')]),flush=True)
