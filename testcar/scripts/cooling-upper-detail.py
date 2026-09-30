"""Upper fan gearboxes from 1973 fig.31 and original catalog exploded fig.13.6.
Nominal bearing envelopes are sourced; tooth counts and installed positions fit.
"""
def build_upper_drives():
    from cooling_interfaces import build_flange, SOURCE, STATUS
    data=json.loads((ROOT/'work/cooling-upper-bevel.json').read_text())
    oldmat=bpy.data.materials.get('COOL_upper_cast_alloy')
    if oldmat:bpy.data.materials.remove(oldmat,do_unlink=True)
    uppercast=mat('COOL_upper_cast_alloy',(.14,.16,.15),.65,.48)
    uppercast.node_tree.nodes.get('Noise Texture').inputs['Scale'].default_value=700
    uppercast.node_tree.nodes.get('Bump').inputs['Strength'].default_value=.35
    uppercast.node_tree.nodes.get('Bump').inputs['Distance'].default_value=.00025
    for i in range(2):
        for o in list(bpy.data.objects):
            if o.name in [f'COOL_output_shaft_{i}',f'COOL_gearcase_{i}',f'COOL_rear_cover_{i}',f'COOL_support_leg_{i}'] or o.name.startswith((f'COOL_output_bearing_{i}_',f'COOL_cover_bolt_{i}_')):bpy.data.objects.remove(o,do_unlink=True)
        fanmount=bpy.data.objects[f'COOL_fan_mount_{i}'];assembly=E(f'COOL_upper_drive_{i}',fanmount,(S['upperApex'],0,0))
        def tag(o,part,role='upper-internal'):
            ct(o,part,role,'MAZ-1973-F31 / MAZ-catalog-13.6');o['upperGearbox']=True;o['upperSide']=i
            o['dimensionStatus']='207 / 304 nominal bearing envelope; remaining geometry, 20:32 teeth and installation fitted.';return o
        def M(name,vs,fs,material=POLISH,parent=assembly,edge=0):return tag(mesh(f'COOL_upper_{name}_{i}',vs,fs,material,parent,edge=edge),name)
        def L(name,profile,parent=assembly,material=POLISH,role='upper-internal'):
            return tag(lathe(f'COOL_upper_{name}_{i}',profile,(0,0,0),material,parent,n=64,closed=True),name,role)
        def R(name,r,inner,length,p,parent=assembly,material=POLISH,role='upper-internal',axis='x'):
            return tag(ring(f'COOL_upper_{name}_{i}',r,inner,length,p,material,parent,axis,n=64),name,role)
        def bolt(name,p,parent=assembly,axis='x',radius=.005,role='upper-hardware'):
            tag(cylinder(f'COOL_upper_{name}_{i}',radius,.006,p,STEEL,parent,axis,n=6),name,role);R(name+'_washer',radius*1.3,radius*.6,.0015,p,parent,role=role,axis=axis)
        fixed={};joints={}
        for shaft,u,v in [('output',(-1,0,0),(0,-1,0)),('input',(0,-1,0),(1,0,0))]:
            u=Vector(u);v=Vector(v);w=u.cross(v);mount=E(f'COOL_upper_{shaft}_mount_{i}',assembly);mount.rotation_mode='QUATERNION';mount.rotation_quaternion=Matrix((C(u),-C(w),C(v))).transposed().to_quaternion();fixed[shaft]=mount
            joints[shaft]=E(f'COOL_upper_{shaft}_{i}',mount)
        for shaft,member,phase in [('output','A',0),('input','B',pi-pi/20)]:
            outline=data[member];n=len(outline);vs=[];fs=[];delta=data['delta' if member=='A' else 'Delta']
            for scale in [data['innerScale'],1]:
                rr=data['R']*scale
                for y,z in outline:
                    v=Vector((1,y,z)).normalized()*rr;vs.append((v.x,v.y*cos(phase)-v.z*sin(phase),v.y*sin(phase)+v.z*cos(phase)))
                for j in range(96):a=j*2*pi/96+phase;vs.append((rr*cos(delta),.0175*cos(a),.0175*sin(a)))
            count=n+96;fs.extend(tuple(reversed(f)) for f in data['caps'][member][0]);fs.extend(tuple(k+count for k in f) for f in data['caps'][member][1])
            for lo,hi in [(0,n),(n,count)]:
                for j in range(lo,hi):k=lo+(j-lo+1)%(hi-lo);fs.append((j,k,k+count,j+count))
            gear=M('bevel_'+shaft,vs,fs,parent=joints[shaft]);gear['fittedToothCount']=32 if member=='A' else 20
        L('output_stepped_shaft',[(-.103,0),(-.103,.008),(-.081,.01),(-.060,.01),(-.047,.015),(.024,.015),(.025,.0175),(.121,.0175),(.131,.018),(.213,.018),(.213,0)],joints['output'])
        L('input_stepped_shaft',[(.050,.006),(.050,.020),(.072,.020),(.079,.0175),(.140,.0175),(.146,.022),(.160,.022),(.167,.009),(.185,.009),(.185,.006)],joints['input'])
        # Front 207 output support; rear 304 support; two 207 input supports.
        for b,spec in enumerate(S['upperBearings']):
            x=spec['x'];rp=spec['pitch'];br=spec['ball'];w=spec['width'];g=br+.00003;shaft=spec['shaft'];parent=joints[shaft]
            curve=[((j/32*2-1)*br*.75,rp-math.sqrt(g*g-((j/32*2-1)*br*.75)**2)) for j in range(33)]
            L('bearing_inner_'+str(b),[(x-w/2,spec['bore']),(x-w/2,rp-br*.6)]+[(x+d,r) for d,r in curve]+[(x+w/2,rp-br*.6),(x+w/2,spec['bore'])],parent)
            L('bearing_outer_'+str(b),[(x-w/2,spec['outer']),(x+w/2,spec['outer']),(x+w/2,rp+br*.6)]+[(x+d,2*rp-r) for d,r in reversed(curve)]+[(x-w/2,rp+br*.6)],fixed[shaft],role='bearing-cover')
            cage=E(f'COOL_upper_cage_{i}_{b}',fixed[shaft])
            for side in [-1,1]:R(f'cage_rail_{b}_{side}',rp+.0012,rp-.0012,.0005,(x+side*(br+.0005),0,0),cage,BRONZE)
            for j in range(8):
                a=j*pi/4;ball=E(f'COOL_upper_ball_{i}_{b}_{j}',cage,(x,rp*cos(a),rp*sin(a)))
                bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=12,radius=br);o=bpy.context.object;o.name=f'COOL_upper_ball_mesh_{i}_{b}_{j}';o.parent=ball;o.location=(0,0,0);o.data.materials.append(POLISH);tag(o,'Fitted bearing ball')
                for face in o.data.polygons:face.use_smooth=True
                a+=pi/8;tag(cylinder(f'COOL_upper_cage_rivet_{i}_{b}_{j}',.0008,2*(br+.0005),(x,rp*cos(a),rp*sin(a)),BRONZE,cage,n=16),'Fitted cage rivet')
        # Cast shell has a true gear cavity, input throat and unequal output seats.
        case=tag(box(f'COOL_upper_case_{i}',(.155,.153,.153),(0,.006,0),uppercast,assembly,edge=.008),'543-1308214 / 543-1308215','housing')
        bpy.ops.object.select_all(action='DESELECT');case.select_set(True);bpy.context.view_layer.objects.active=case;bpy.ops.object.convert(target='MESH')
        cuts=[box('upper_gear_void',(.135,.134,.134),(0,.006,0),STEEL,assembly,edge=.006),cylinder('upper_front_throat',.063,.11,(-.067,0,0),STEEL,assembly,n=64),cylinder('upper_rear_seat',.026,.12,(.073,0,0),STEEL,assembly,n=64),cylinder('upper_input_throat',.040,.18,(0,-.10,0),STEEL,assembly,axis='y',n=64)]
        for cut in cuts:
            bpy.context.view_layer.update();bpy.context.view_layer.objects.active=case;mod=case.modifiers.new('Machined housing passage','BOOLEAN');mod.operation='DIFFERENCE';mod.object=cut;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cut,do_unlink=True)
        L('front_support_cup',[(.070,.036),(.070,.060),(.079,.060),(.079,.068),(.088,.068),(.088,.043),(.119,.043),(.126,.050),(.132,.050),(.132,.026),(.115,.026),(.115,.036)],fixed['output'],uppercast,'housing')
        L('rear_support',[(.060,.026),(.060,.035),(.069,.035),(.069,.044),(.087,.044),(.087,.009),(.082,.009),(.082,.026)],assembly,uppercast,'housing')
        L('input_bearing_cup',[(.071,.036),(.071,.047),(.080,.047),(.080,.0415),(.142,.0415),(.147,.048),(.156,.048),(.156,.033),(.143,.033),(.143,.036)],fixed['input'],uppercast,'housing')
        R('input_seal_44_65',.0325,.022,.008,(.150,0,0),fixed['input'],RUBBER)
        R('input_adjusting_shim',.047,.036,.0006,(.076,0,0),fixed['input'],GASKET)
        flange=tag(build_flange(f'COOL_upper_input_flange_{i}',joints['input'],STEEL,.166,.175,.009),'543-1308549')
        flange['sourceId']=SOURCE;flange['dimensionStatus']=STATUS
        bolt('input_M18_nut',(.182,0,0),joints['input'],radius=.016)
        for j in range(6):
            a=j*pi/3;bolt('input_cup_bolt_'+str(j),(.156,.043*cos(a),.043*sin(a)),fixed['input']);bolt('output_cup_bolt_'+str(j),(.091,.060*cos(a),.060*sin(a)),fixed['output'])
        for y in [-.033,.033]:
            for z in [-.033,.033]:bolt('rear_cover_bolt_'+str(y)+'_'+str(z),(.089,y,z))
        # Separate spring-loaded end brush / insulated holder, original fig.31 item17.
        oldbrush=bpy.data.objects.get(f'COOL_ground_brush_{i}')
        if oldbrush:bpy.data.objects.remove(oldbrush,do_unlink=True)
        R('end_brush_holder',.014,.008,.035,(.108,0,0),assembly,resin)
        tag(cylinder(f'COOL_upper_end_brush_{i}',.0075,.012,(.109,0,0),RUBBER,assembly,n=32),'0000-1308688 brush')
        spring=[(.116+t/80*.014,.007*cos(t/80*8*pi),.007*sin(t/80*8*pi)) for t in range(81)];tag(pipe(f'COOL_upper_end_brush_spring_{i}',spring,.00065,STEEL,assembly),'537-2402416')
        R('brush_protective_cover',.023,.016,.048,(.107,0,0),assembly,uppercast,'housing')
        tag(pipe(f'COOL_upper_oil_inlet_{i}',[(.021,.080,0),(.021,.105,0),(.041,.112,0)],.006,STEEL,assembly),'379051 oil elbow')
        tag(cylinder(f'COOL_upper_oil_inlet_hex_{i}',.0105,.009,(.021,.087,0),STEEL,assembly,axis='y',n=6),'Oil elbow threaded body')
        # Cast mounting feet and a tapered pedestal from installation fig.13.1.
        for z in [-.057,.057]:
            tag(box(f'COOL_upper_mount_foot_{i}_{z}',(.09,.013,.028),(.022,-.078,z),uppercast,assembly,edge=.003),'Gearbox mounting foot','support')
            for x in [-.010,.055]:bolt(f'mount_bolt_{x}_{z}',(x,-.066,z),axis='y',role='support')
        pedestal=tag(lathe(f'COOL_upper_pedestal_{i}',[(0,.065),(.014,.065),(.045,.036),(.245,.032),(.258,.053),(.270,.053),(.270,.023),(0,.023)],(.022,-.355,0),uppercast,assembly,axis='y',n=64,closed=True),'Cast pedestal; dimensions fitted','support')
        tag(box(f'COOL_upper_pedestal_base_{i}',(.15,.017,.15),(.022,-.359,0),uppercast,assembly,edge=.008),'Pedestal base','support')
        for x in [-.034,.078]:
            for z in [-.056,.056]:bolt(f'pedestal_anchor_{x}_{z}',(x,-.346,z),axis='y',radius=.007,role='support')
    print('COOLING_UPPER_AUTHORED',len([o for o in bpy.data.objects if o.get('upperGearbox')]),flush=True)
build_upper_drives()
