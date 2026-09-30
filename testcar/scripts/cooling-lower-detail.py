"""543-1308509: original section, exploded catalog and inspected part photograph.
Nominal 310/307 bearing envelopes are sourced; tooth counts and casting dimensions
are fitted. Execute within the Blender cooling builder's helper namespace.
"""
def build_lower_drive():
    from cooling_interfaces import build_flange, SOURCE, STATUS
    data=json.loads((ROOT/'work/cooling-lower-bevel.json').read_text())
    for o in list(bpy.data.objects):
        if o.name in ['COOL_lower_drive_housing','COOL_crank_torsion'] or o.name.startswith('COOL_lower_mount_'):bpy.data.objects.remove(o,do_unlink=True)
    assembly=E('COOL_lower_drive',root,S['lowerOrigin'])
    paint=mat('COOL_lower_black_storage_enamel',(.008,.011,.010),.12,.37)
    paint.node_tree.nodes.get('Noise Texture').inputs['Scale'].default_value=620
    paint.node_tree.nodes.get('Bump').inputs['Strength'].default_value=.65
    paint.node_tree.nodes.get('Bump').inputs['Distance'].default_value=.00055
    def tag(o,part,role='lower-internal'):
        ct(o,part,role,'MAZ-1973-F30 / MAZ-catalog-13.9');o['lowerDrive']=True
        o['dimensionStatus']='Bearing nominal envelopes catalogued; casting, shafts and gear 32/20 teeth fitted. Not original CAD.'
        return o
    def L(name,profile,pos=(0,0,0),material=POLISH,parent=assembly,role='lower-internal'):
        return tag(lathe('COOL_lower_'+name,profile,pos,material,parent,n=64,closed=True),name,role)
    def ring_local(name,r,inside,length,p,material=POLISH,parent=assembly,role='lower-internal'):
        return tag(ring('COOL_lower_'+name,r,inside,length,p,material,parent,n=64),name,role)
    def bolt(name,p,parent=assembly,size=.005,role='lower-hardware'):
        tag(cylinder('COOL_lower_'+name+'_head',size,.006,p,STEEL,parent,n=6),name,role)
        ring_local(name+'_washer',size*1.35,size*.6,.0015,p,POLISH,parent,role)
    def mount(name,u,v):
        u=Vector(u).normalized();v=Vector(v).normalized();w=u.cross(v)
        ob=E(name,assembly);ob.rotation_mode='QUATERNION';ob.rotation_quaternion=Matrix((C(u),-C(w),C(v))).transposed().to_quaternion();ob['lowerDrive']=True;return ob
    mounts={'input':mount('COOL_lower_input_mount',(-1,0,0),(0,math.sqrt(.5),math.sqrt(.5)))}
    joints={'input':E('COOL_lower_input',mounts['input'])}
    for i,s in enumerate([1,-1]):
        mounts[f'output_{i}']=mount(f'COOL_lower_output_mount_{i}',(0,math.sqrt(.5),s*math.sqrt(.5)),(1,0,0));joints[f'output_{i}']=E(f'COOL_lower_output_{i}',mounts[f'output_{i}'])
    # The two driven pitch cones are smaller than 45 degrees: a pair of equal
    # miter gears here would intersect each other between the two output axes.
    for shaft,member,bore,phase in [('input','A',.025,0),('output_0','B',.0175,pi-pi/20),('output_1','B',.0175,pi-pi/20)]:
        outline=data[member];n=len(outline);vs=[];fs=[];delta=data['delta' if member=='A' else 'Delta']
        for scale in [data['innerScale'],1]:
            rr=data['R']*scale
            for y,z in outline:
                v=Vector((1,y,z)).normalized()*rr;vs.append((v.x,v.y*cos(phase)-v.z*sin(phase),v.y*sin(phase)+v.z*cos(phase)))
            for j in range(96):a=j*2*pi/96+phase;vs.append((rr*cos(delta),bore*cos(a),bore*sin(a)))
        count=n+96;fs.extend(tuple(reversed(f)) for f in data['caps'][member][0]);fs.extend(tuple(k+count for k in f) for f in data['caps'][member][1])
        for lo,hi in [(0,n),(n,count)]:
            for j in range(lo,hi):k=lo+(j-lo+1)%(hi-lo);fs.append((j,k,k+count,j+count))
        ob=tag(mesh('COOL_lower_bevel_'+shaft,vs,fs,POLISH,joints[shaft]),'543-1308522' if shaft=='input' else '543-1308558')
        ob['fittedToothCount']=32 if shaft=='input' else 20;ob['toothGeometry']='Spherical involute, swept conjugate root relief; counts unverified'
    # Hollow leading shaft carries the through torsion shaft; output journals
    # follow the 35 mm bearing bore and 44 mm seal land in the parts catalog.
    L('leading_hollow_shaft',[(.026,.012),(.026,.028),(.051,.028),(.059,.025),(.168,.025),(.168,.012)],parent=joints['input'])
    tag(cylinder('COOL_lower_torsion_bar',.009,.235,(.0375,0,0),STEEL,joints['input'],n=48),'543-1308657-10')
    for x in [-.078,.158]:
        ring_local('torsion_spline_hub_'+str(x),.0125,.009,.018,(x,0,0),STEEL,joints['input'])
        for j in range(12):
            a=j*pi/6;o=tag(box(f'COOL_lower_torsion_spline_{x}_{j}',(.017,.002,.003),(x,.0127,0),STEEL,joints['input'],edge=.0003),'Fitted spline, original count unknown');o.rotation_euler.x=a
    for i in range(2):
        key=f'output_{i}';joint=joints[key];fixed=mounts[key]
        L('output_shaft_'+str(i),[(.047,.009),(.047,.020),(.067,.020),(.077,.0175),(.148,.0175),(.152,.022),(.175,.022),(.179,.009),(.194,.009),(.194,.007)],parent=joint)
        # Separate machined bearing cup, adjusting shims and seal cover.
        L('output_cup_'+str(i),[(.067,.040),(.067,.047),(.075,.047),(.075,.055),(.084,.055),(.084,.047),(.152,.047),(.159,.055),(.166,.055),(.166,.033),(.151,.033),(.151,.040)],material=paint,parent=fixed,role='housing')
        ring_local('output_shim_'+str(i),.055,.040,.0007,(.079,0,0),GASKET,fixed,'lower-gasket')
        ring_local('seal_44_65_'+str(i),.0325,.022,.008,(.161,0,0),RUBBER,fixed)
        flange=tag(build_flange('COOL_lower_cardan_flange_'+str(i),joint,STEEL,.174,.184,.011),'543-1308548')
        flange['sourceId']=SOURCE;flange['dimensionStatus']=STATUS
        tag(cylinder('COOL_lower_output_nut_'+str(i),.016,.010,(.19,0,0),STEEL,joint,n=6),'M18x1.5 nut')
        for j in range(6):a=j*pi/3;bolt(f'output_cup_bolt_{i}_{j}',(.165,.049*cos(a),.049*sin(a)),fixed)
    # Nominal bearing envelopes: input 310 (50x110x27), outputs 307 (35x80x21).
    for b,spec in enumerate(S['lowerBearings']):
        fixed=mounts[spec['shaft']];shaft=joints[spec['shaft']];x=spec['x'];rp=spec['pitch'];br=spec['ball'];w=spec['width'];g=br+.00003
        curve=[((j/32*2-1)*br*.75,rp-math.sqrt(g*g-((j/32*2-1)*br*.75)**2)) for j in range(33)]
        profile=[(x-w/2,spec['bore']),(x-w/2,rp-br*.6)]+[(x+d,r) for d,r in curve]+[(x+w/2,rp-br*.6),(x+w/2,spec['bore'])]
        L('bearing_inner_'+str(b),profile,parent=shaft)
        L('bearing_outer_'+str(b),[(x-w/2,spec['outer']),(x+w/2,spec['outer']),(x+w/2,rp+br*.6)]+[(x+d,2*rp-r) for d,r in reversed(curve)]+[(x-w/2,rp+br*.6)],parent=fixed,role='bearing-cover')
        cage=E('COOL_lower_cage_'+str(b),fixed);cage['lowerDrive']=True
        for side in [-1,1]:ring_local(f'cage_rail_{b}_{side}',rp+.0015,rp-.0015,.0006,(x+side*(br+.0006),0,0),BRONZE,cage)
        for j in range(8):
            a=j*pi/4;ball=E(f'COOL_lower_ball_{b}_{j}',cage,(x,rp*cos(a),rp*sin(a)));ball['lowerDrive']=True
            bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=12,radius=br);ob=bpy.context.object;ob.name=f'COOL_lower_ball_mesh_{b}_{j}';ob.parent=ball;ob.location=(0,0,0);ob.data.materials.append(POLISH)
            for face in ob.data.polygons:face.use_smooth=True
            tag(ob,'Bearing rolling element; internal dimensions/count fitted')
            a+=pi/8;tag(cylinder(f'COOL_lower_cage_rivet_{b}_{j}',.001,2*(br+.0006),(x,rp*cos(a),rp*sin(a)),BRONZE,cage,n=16),'Cage rivet')
    # Fuse a curved casting, then remove the connected gear cavity, sump and
    # bearing passages. Separate machined cups conceal these apertures assembled.
    poly=[(-.172,-.075),(-.16,-.101),(-.045,-.107),(.010,-.101),(.073,-.122),(.115,-.093),(.095,-.025),(.105,0),(.095,.025),(.115,.093),(.073,.122),(.010,.101),(-.045,.107),(-.16,.101),(-.172,.075)]
    shell=tag(prism('COOL_lower_cast_case',poly,-.155,.035,paint,assembly,edge=.018),'543-1308516','housing');outer=[shell]
    for i in range(2):outer.append(cylinder('COOL_lower_cast_branch_'+str(i),.051,.10,(.10,0,0),paint,mounts[f'output_{i}'],n=64))
    def fuse(objects,name,voxel=.0015):
        bpy.ops.object.select_all(action='DESELECT')
        for o in objects:o.select_set(True)
        bpy.context.view_layer.objects.active=objects[0];bpy.ops.object.convert(target='MESH');bpy.ops.object.join();ob=bpy.context.object;ob.name=name
        mod=ob.modifiers.new('Continuous cast skin','REMESH');mod.mode='VOXEL';mod.voxel_size=voxel;mod.use_smooth_shade=True;bpy.ops.object.modifier_apply(modifier=mod.name)
        mod=ob.modifiers.new('Cast fillets','SMOOTH');mod.factor=.55;mod.iterations=3;bpy.ops.object.modifier_apply(modifier=mod.name);return ob
    shell=fuse(outer,'COOL_lower_cast_case')
    cutters=[box('lower_sump_void',(.145,.128,.157),(-.055,-.084,0),STEEL,assembly,edge=.012),cylinder('lower_main_void',.064,.25,(-.066,0,0),STEEL,assembly,n=64)]
    for i in range(2):
        cutters.append(cylinder('lower_branch_void_'+str(i),.0402,.205,(.087,0,0),STEEL,mounts[f'output_{i}'],n=64))
        cutters.append(cylinder('lower_branch_gear_void_'+str(i),.0445,.055,(.042,0,0),STEEL,mounts[f'output_{i}'],n=64))
    cavity=fuse(cutters,'LOWER_CASTING_CORE',.0012)
    bpy.context.view_layer.objects.active=shell;mod=shell.modifiers.new('Hollow connected oil chamber','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cavity;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cavity,do_unlink=True)
    tag(shell,'543-1308516 continuous cast housing','housing')
    L('input_bearing_cup',[(.061,.055),(.061,.063),(.077,.063),(.077,.071),(.087,.071),(.087,.063),(.168,.063),(.174,.071),(.181,.071),(.181,.027),(.165,.027),(.165,.055)],material=paint,parent=mounts['input'],role='housing')
    ring_local('input_cup_shim',.071,.055,.0007,(.083,0,0),GASKET,mounts['input'],'lower-gasket')
    for j in range(8):a=j*pi/4;bolt(f'input_cup_bolt_{j}',(.180,.066*cos(a),.066*sin(a)),mounts['input'])
    # Original cup has axial cast ribs / stud lands, visible in the exploded view.
    for j in range(8):
        a=j*pi/4
        tag(cylinder(f'COOL_lower_input_cup_land_{j}',.0075,.076,(.125,.061*cos(a),.061*sin(a)),paint,mounts['input'],n=32),'543-1308534','housing')
    L('engine_adapter',[(.031,.030),(.031,.067),(.045,.067),(.045,.091),(.065,.091),(.065,.030)],material=paint,role='housing')
    for j in range(8):a=j*pi/4;bolt(f'engine_mount_{j}',(.066,.083*cos(a),.083*sin(a)))
    # Front oil pump: two fitted involute gears, shaft seals, a true two-lobe
    # cavity and a separate cover. Hydraulic map remains unmeasured.
    pumpdata=json.loads((ROOT/'work/mzn-gear-profile.json').read_text());scale=.04/.034
    for name in ['drive','driven']:
        joint=E('COOL_lower_pump_'+name,assembly);joint['lowerDrive']=True
        vs=[(x,y*scale,z*scale) for x in [-.006,.006] for y,z in pumpdata['sectionVertices']];n=len(pumpdata['sectionVertices']);out=pumpdata['outerCount'];fs=[]
        for f in pumpdata['capTriangles']:fs.extend([tuple(reversed(f)),tuple(k+n for k in f)])
        for lo,hi in [(0,out),(out,n)]:
            for j in range(lo,hi):k=lo+(j-lo+1)%(hi-lo);fs.append((j,k,k+n,j+n))
        ob=tag(mesh('COOL_lower_oil_gear_'+name,vs,fs,POLISH,joint),'Fitted 12-tooth oil pump gear');ob['fittedToothCount']=12
        ring_local('oil_gear_shaft_'+name,.0094,.0035,.027,(0,0,0),POLISH,joint)
    # Shaft coupling engages the hollow input nose; it does not end in free air.
    ring_local('oil_drive_coupling',.0115,.0035,.028,(.176,0,0),POLISH,joints['input'])
    def pump_skin(name,lo,hi):
        bits=[cylinder(name,.029,hi-lo,((lo+hi)/2,y,0),paint,assembly,n=64) for y in [0,-.04]]
        for y,z in [(.020,.020),(.020,-.020),(-.060,.020),(-.060,-.020)]:bits.append(cylinder(name+'_lug',.010,hi-lo,((lo+hi)/2,y,z),paint,assembly,n=32))
        ob=fuse(bits,name,.0007);return tag(ob,'543-1308714','housing')
    pumpbody=pump_skin('COOL_lower_oil_pump_body',-.2155,-.1805)
    for y in [0,-.04]:
        cut=cylinder('pump_working_chamber',.024,.055,(-.198,y,0),STEEL,assembly,n=64)
        bpy.context.view_layer.objects.active=pumpbody;mod=pumpbody.modifiers.new('Pump gear pocket','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cut;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cut,do_unlink=True)
    pump_skin('COOL_lower_oil_pump_cover',-.2245,-.2155)
    tag(cylinder('COOL_lower_pump_front_boss',.013,.008,(-.228,0,0),paint,assembly,n=64),'Oil pump cover shaft boss','housing')
    tag(cylinder('COOL_lower_pump_top_cross',.0085,.069,(-.225,.021,0),paint,assembly,axis='z',n=48),'Oil pump cover oil connection','housing')
    for y,z in [(.020,.019),(.020,-.019),(-.06,.019),(-.06,-.019)]:bolt(f'oil_cover_{y}_{z}',(-.226,y,z))
    # Suction strainer, sump drain, fill plug and two original oil tees.
    tag(pipe('COOL_lower_suction_pipe',[(-.184,-.042,0),(-.13,-.142,0),(-.005,-.142,0)],.008,STEEL,assembly),'547-1315650')
    for j in range(18):tag(cylinder(f'COOL_lower_strainer_mesh_{j}',.00045,.040,(-.045+j*.0025,-.144,0),STEEL,assembly,axis='z',n=8),'547-1315660 mesh screen')
    tag(cylinder('COOL_lower_sump_drain',.012,.017,(-.015,-.179,0),STEEL,assembly,axis='y',n=6),'Drain plug','lower-hardware')
    tag(cylinder('COOL_lower_fill_plug',.018,.010,(-.035,-.01,.116),STEEL,assembly,axis='z',n=6),'Fill plug M33x2','lower-hardware')
    for k,x in enumerate([-.035,-.060]):
        tag(cylinder(f'COOL_lower_tee_stem_{k}',.009,.080,(x,.116,0),paint,assembly,axis='y',n=48),'543-1308890' if k==0 else '379594')
        tag(pipe(f'COOL_lower_tee_branches_{k}',[(x,.145,-.062),(x,.13,0),(x,.145,.062)],.006,paint,assembly),'Oil supply / return tee')
        tag(cylinder(f'COOL_lower_tee_hex_cap_{k}',.011,.008,(x,.159,0),STEEL,assembly,axis='y',n=6),'Tee closure plug','lower-hardware')
    print('COOLING_LOWER_AUTHORED',len([o for o in bpy.data.objects if o.get('lowerDrive')]),flush=True)
build_lower_drive()
