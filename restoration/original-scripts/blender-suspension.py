import bpy,bmesh,json,math,sys
from pathlib import Path
from mathutils import Vector
from math import sin,cos,pi,sqrt
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs'
POSES=json.loads((ROOT/'work/suspension-poses.json').read_text());SPEC=POSES['spec'];REG=[]
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
root=None
def C(p):return Vector((p[0],-p[2],p[1]))

def empty(name,parent=None,pos=(0,0,0),rx=0):
    ob=bpy.data.objects.new(name,None);bpy.context.collection.objects.link(ob)
    ob.parent=parent;ob.location=C(pos);ob.rotation_euler.x=rx;return ob

def mat(name,color,metal,rough):
    m=bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=(*color,1)
    b=m.node_tree.nodes.get('Principled BSDF');b.inputs['Base Color'].default_value=(*color,1)
    b.inputs['Metallic'].default_value=metal;b.inputs['Roughness'].default_value=rough
    # Physically small machining/casting texture; no baked occlusion on moving parts.
    n=m.node_tree.nodes.new('ShaderNodeTexNoise');n.inputs['Scale'].default_value=950
    coord=m.node_tree.nodes.new('ShaderNodeTexCoord');m.node_tree.links.new(coord.outputs['Object'],n.inputs['Vector'])
    bump=m.node_tree.nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.12;bump.inputs['Distance'].default_value=.00008
    m.node_tree.links.new(n.outputs['Fac'],bump.inputs['Height']);m.node_tree.links.new(bump.outputs['Normal'],b.inputs['Normal'])
    return m

def tag(o,part,source='MANUAL-1973-F90',role='internal',confidence='family architecture; dimensions reconstructed'):
    o['s543Part']=part;o['sourceId']=source;o['dimensionStatus']=confidence;o['s543Role']=role
    REG.append({'node':o.name,'part':part,'source':source,'role':role,'dimensions':confidence})
    return o

def mesh(name,vs,fs,material,parent=root,edge=0,smooth=False,part=None,source='MANUAL-1973-F90',role='internal'):
    data=bpy.data.meshes.new(name+'_mesh');data.from_pydata([C(v) for v in vs],[],fs);data.update()
    bm=bmesh.new();bm.from_mesh(data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(data);bm.free()
    ob=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(ob);ob.parent=parent;data.materials.append(material)
    if smooth:
        for p in data.polygons:p.use_smooth=True
    if edge:
        mod=ob.modifiers.new('Machined edge radius','BEVEL');mod.width=edge;mod.segments=2
        mod=ob.modifiers.new('Weighted machining normals','WEIGHTED_NORMAL');mod.keep_sharp=True
    uv=data.uv_layers.new(name='MetricUV')
    for p in data.polygons:
        axis=max(range(3),key=lambda i:abs(p.normal[i]))
        for li in p.loop_indices:
            v=data.vertices[data.loops[li].vertex_index].co;uv.data[li].uv=(v[(axis+1)%3]*3,v[(axis+2)%3]*3)
    return tag(ob,part or name,source,role)

def prism(name,poly,lo,hi,material,parent=root,axis='x',edge=.001,**kw):
    def point(d,u,v):return (d,u,v) if axis=='x' else (u,d,v) if axis=='y' else (u,v,d)
    n=len(poly);vs=[point(d,*p) for d in [lo,hi] for p in poly]
    fs=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    return mesh(name,vs,fs,material,parent,edge,**kw)

def box(name,size,pos,material,parent=root,edge=.003,**kw):
    x,y,z=pos;a,b,c=[d/2 for d in size]
    return prism(name,[(y-b,z-c),(y+b,z-c),(y+b,z+c),(y-b,z+c)],x-a,x+a,material,parent,edge=edge,**kw)

def lathe(name,profile,pos,material,parent=root,axis='x',n=48,closed=False,**kw):
    # Profile is (axial distance, radius); supports machined recesses, open bores,
    # ring grooves, sealing lands and genuine annular end faces.
    vs=[]
    for d,r in profile:
        for j in range(n):
            a=j/n*2*pi;v=(d,r*cos(a),r*sin(a)) if axis=='x' else (r*cos(a),d,r*sin(a)) if axis=='y' else (r*cos(a),r*sin(a),d)
            vs.append(tuple(v[k]+pos[k] for k in range(3)))
    fs=[]
    for k in range(len(profile)-1+(1 if closed else 0)):
        k1=(k+1)%len(profile)
        fs += [(k*n+j,k*n+(j+1)%n,k1*n+(j+1)%n,k1*n+j) for j in range(n)]
    return mesh(name,vs,fs,material,parent,edge=.0006,smooth=True,**kw)

def cylinder(name,r,length,pos,material,parent=root,axis='x',n=40,**kw):
    return lathe(name,[(-length/2,0),(-length/2,r),(length/2,r),(length/2,0)],pos,material,parent,axis,n,**kw)

def ring(name,r,inside,length,pos,material,parent=root,axis='x',n=48,**kw):
    return lathe(name,[(-length/2,inside),(-length/2,r),(length/2,r),(length/2,inside)],pos,material,parent,axis,n,True,**kw)

def pipe(name,pts,r,material,parent=root,**kw):
    # Smooth bend with round cross section; export as an editable mesh later.
    curve=bpy.data.curves.new(name+'_path','CURVE');curve.dimensions='3D';curve.resolution_u=8;curve.bevel_depth=r;curve.bevel_resolution=2
    if len(pts)>32:
        curve.bevel_resolution=1;sp=curve.splines.new('POLY');sp.points.add(len(pts)-1)
        for p,v in zip(sp.points,pts):p.co=(*C(v),1)
    else:
        sp=curve.splines.new('BEZIER');sp.bezier_points.add(len(pts)-1)
        for p,v in zip(sp.bezier_points,pts):p.co=C(v);p.handle_left_type='AUTO';p.handle_right_type='AUTO'
    ob=bpy.data.objects.new(name,curve);bpy.context.collection.objects.link(ob);ob.parent=parent;curve.materials.append(material)
    return tag(ob,kw.get('part',name),kw.get('source','PHOTO-035'),kw.get('role','internal'))

def bolt(name,pos,parent=root,axis='y',r=.008,role='internal'):
    ring(name+'_washer',r*1.4,r*.63,.0025,pos,POLISH,parent,axis,24,part='washer',source='PHOTO-035',role=role)
    ob=cylinder(name+'_hex',r,.009,pos,STEEL,parent,axis,6,part='hexagonal fastener',source='PHOTO-035',role=role)
    return ob

root=empty('S543_SUSPENSION');root['partId']='suspension'
root['damper_clearance_revision']=1
root['scope']='543/543A double-torsion topology; hardpoints, dimensions and four-axle installation remain reconstruction parameters'
PAINT=mat('S543_cast_olive',(.075,.095,.065),.18,.62)
STEEL=mat('S543_forged_steel',(.10,.12,.115),.84,.43)
POLISH=mat('S543_machined_steel',(.40,.43,.42),.93,.23)
BRONZE=mat('S543_bronze_bush',(.27,.18,.07),.76,.36)
RUBBER=mat('S543_rubber',(.012,.015,.012),0,.87)

# Small, repeatable cast surface maps are baked by Blender and embedded in glTF.
# They describe surface microgeometry, not an unlicensed photographic texture.
surface=mat('S543_surface_bake',(.06,.08,.052),.15,.66)
nodes=surface.node_tree.nodes;links=surface.node_tree.links;b=nodes.get('Principled BSDF')
noise=next(n for n in nodes if n.type=='TEX_NOISE');noise.inputs['Scale'].default_value=215;noise.inputs['Detail'].default_value=2
bump=next(n for n in nodes if n.type=='BUMP');bump.inputs['Strength'].default_value=.32;bump.inputs['Distance'].default_value=.00025
ramp=nodes.new('ShaderNodeMapRange');ramp.inputs['From Min'].default_value=0;ramp.inputs['From Max'].default_value=1;ramp.inputs['To Min'].default_value=.48;ramp.inputs['To Max'].default_value=.79
links.new(noise.outputs['Fac'],ramp.inputs['Value']);links.new(ramp.outputs['Result'],b.inputs['Roughness'])
bpy.ops.mesh.primitive_plane_add(size=1/3);bake_plane=bpy.context.object;bake_plane.name='S543_BAKE_PLANE';bake_plane.data.materials.append(surface)
bpy.context.scene.render.engine='CYCLES';bpy.context.scene.cycles.samples=4
maps={}
for label,kind in [('CastNormal','NORMAL'),('CastRoughness','ROUGHNESS')]:
    im=bpy.data.images.new('S543_'+label,512,512);im.colorspace_settings.name='Non-Color'
    target=nodes.new('ShaderNodeTexImage');target.image=im;nodes.active=target
    bpy.ops.object.bake(type=kind,margin=8);im.filepath_raw=str(OUT/('S543_'+label+'.png'));im.file_format='PNG';im.save();im.pack();maps[label]=im
bpy.data.objects.remove(bake_plane,do_unlink=True)
for material in [PAINT,STEEL,BRONZE]:
    ns=material.node_tree.nodes;ls=material.node_tree.links;bs=ns.get('Principled BSDF')
    tex=ns.new('ShaderNodeTexImage');tex.image=maps['CastNormal'];tex.extension='REPEAT'
    nm=ns.new('ShaderNodeNormalMap');nm.inputs['Strength'].default_value=.65 if material==PAINT else .22;ls.new(tex.outputs['Color'],nm.inputs['Color']);ls.new(nm.outputs['Normal'],bs.inputs['Normal'])
    rough=ns.new('ShaderNodeTexImage');rough.image=maps['CastRoughness'];rough.extension='REPEAT';ls.new(rough.outputs['Color'],bs.inputs['Roughness'])

def branch(name,stations,parent,side):
    # Variable-section cast fork: curved planform, broad bosses, narrow web.
    vs=[]
    for x,y,z,width,thick in stations:
        for dx,dy in [(-1,-.55),(-.7,-1),(.7,-1),(1,-.55),(1,.55),(.7,1),(-.7,1),(-1,.55)]:
            vs.append((x+dx*width/2,y+dy*thick/2,side*z))
    fs=[tuple(range(7,-1,-1)),tuple(range((len(stations)-1)*8,len(stations)*8))]
    for k in range(len(stations)-1):
        for j in range(8):fs.append((k*8+j,k*8+(j+1)%8,(k+1)*8+(j+1)%8,(k+1)*8+j))
    return mesh(name,vs,fs,PAINT,parent,.004,True,part='cast fork branch with changing section',source='PHOTO-035',role='arm')

def spline(name,r,inside,length,pos,parent,side=1):
    # Reconstructed 24-spline pattern. Tooth count is explicitly unconfirmed.
    vs=[];n=96
    for d,outer in [(-length/2,True),(length/2,True),(length/2,False),(-length/2,False)]:
        for j in range(n):
            a=j/n*2*pi;rr=(r if j%4 in [1,2] else r*.88) if outer else inside
            vs.append((pos[0]+d,pos[1]+rr*cos(a),pos[2]+rr*sin(a)))
    fs=[(k*n+j,k*n+(j+1)%n,((k+1)%4)*n+(j+1)%n,((k+1)%4)*n+j) for k in range(4) for j in range(n)]
    return mesh(name,vs,fs,POLISH,parent,part='splined shaft end; tooth count reconstructed',role='internal')

TORSIONS=[]
for i in range(8):
    x=SPEC['axles'][i//2];s=1 if i%2 else -1;name=f'S543_{i}';direction=SPEC['anchorDirection'][i//2]
    station=empty(name+'_fixed',root);station['wheelStation']=i
    for kind in ['lower','upper']:
        y,z=SPEC[kind];ey,ez=SPEC[kind+'End'];dy=ey-y;reach=ez-z
        arm=empty(name+'_'+kind,root,(x,y,s*z));arm['jointType']='longitudinal revolute fork and sleeve'
        ring(name+'_'+kind+'_axis_sleeve',.063,.030,.58,(0,0,0),PAINT,arm,n=48,part='hollow arm pivot sleeve',role='arm')
        for v in [-1,1]:
            stations=[(v*.27,0,0,.16,.072),(v*.26,dy*.20,reach*.18,.145,.060),(v*.20,dy*.50-.014,reach*.50,.11,.038),(v*.12,dy*.8-.008,reach*.80,.105,.043),(v*.078,dy,reach,.15,.073)]
            branch(name+f'_{kind}_fork_{v}',stations,arm,s)
            # Raised flange/rib follows the photographed casting profile.
            rib=[(a,b+c*.40,zr,w*.26,c*.42) for a,b,zr,w,c in stations[1:-1]]
            branch(name+f'_{kind}_rib_{v}',rib,arm,s)
            ring(name+f'_{kind}_outer_boss_{v}',.073,.027,.087,(v*.078,dy,s*reach),PAINT,arm,n=48,part='outer longitudinal pin boss',role='arm')
            ring(name+f'_{kind}_outer_bush_{v}',.027,.023,.089,(v*.078,dy,s*reach),BRONZE,arm,part='outer pivot bushing',role='internal')
            cylinder(name+f'_{kind}_pin_cap_{v}',.060,.010,(v*.128,dy,s*reach),PAINT,arm,part='outer pin end cover',role='cover')
            for k in range(4):
                a=k/4*2*pi;bolt(name+f'_{kind}_cap_fastener_{v}_{k}',(v*.137,dy+.043*cos(a),s*reach+.043*sin(a)),arm,'x',.006,role='arm')
            # Split clamping ears at the inner sleeve, with retaining bolt.
            box(name+f'_{kind}_clamp_ear_{v}',(.066,.061,.045),(v*.253,-.045,s*.054),PAINT,arm,.005,part='split arm clamp',source='PHOTO-035',role='arm')
            bolt(name+f'_{kind}_clamp_bolt_{v}',(v*.253,-.046,s*.079),arm,'z',.010,role='arm')
        for v in [-1,1]:
            ring(name+f'_{kind}_bronze_frame_bush_{v}',.071,.064,.065,(x+v*.18,y,s*z),BRONZE,station,part='frame sleeve bronze bearing',role='internal')
            ring(name+f'_{kind}_bearing_carrier_{v}',.092,.072,.075,(x+v*.18,y,s*z),PAINT,station,part='frame-side bearing boss',role='frame')
            ring(name+f'_{kind}_dust_seal_{v}',.077,.063,.007,(x+v*.221,y,s*z),RUBBER,station,part='sleeve dust seal',role='internal')
        bar_end=empty(name+'_'+kind+'_spline',root,(x,y,s*z))
        spline(name+'_'+kind+'_driven_spline',.031,.017,.086,(direction*.26,0,0),bar_end)
        fixed=x+direction*SPEC['barLength'];diameter=SPEC[kind+'Diameter'];length=SPEC['barLength']-.30
        # Separate protective tube; do not mistake its outer diameter for the bar.
        ring(name+'_'+kind+'_guard_tube',.036,.032,length-.07,((x+direction*.30+fixed)/2,y,s*z),PAINT,station,n=32,part='torsion shaft protective tube',role='cover')
        anchor=empty(name+'_'+kind+'_anchor',station,(fixed,y,s*z))
        ring(name+'_'+kind+'_anchor_boss',.068,.031,.13,(0,0,0),PAINT,anchor,part='fixed splined anchor',role='frame')
        spline(name+'_'+kind+'_fixed_spline',.031,.016,.09,(0,0,0),anchor)
        box(name+'_'+kind+'_anchor_foot',(.16,.04,.19),(0,.076,0),PAINT,anchor,.008,part='torsion anchor bracket',role='frame')
        for ax in [-.057,.057]:
            for az in [-.073,.073]:bolt(name+f'_{kind}_anchor_bolt_{ax}_{az}',(ax,.1,az),anchor,'y',.008,role='frame')
        cylinder(name+'_'+kind+'_retainer',.042,.009,(direction*.082,0,0),STEEL,anchor,part='anchor end lock plate',role='internal')
        bolt(name+'_'+kind+'_retaining_bolt',(direction*.092,0,0),anchor,'x',.010)
        # Longitudinally sampled editable bar, fixed anchor to rotating sleeve.
        vs=[];segments=24;n=32
        for k in range(segments+1):
            u=k/segments;xx=fixed+(x+direction*.30-fixed)*u
            for j in range(n):
                a=j/n*2*pi;rr=diameter/2*(.988 if j in [0,1] else 1)
                vs.append((xx,y+rr*cos(a),s*z+rr*sin(a)))
        fs=[(k*n+j,k*n+(j+1)%n,(k+1)*n+(j+1)%n,(k+1)*n+j) for k in range(segments) for j in range(n)]
        bar=mesh(name+'_'+kind+'_torsion_bar',vs,fs,STEEL,station,smooth=True,part='elastic torsion shaft',role='torsion')
        bar['torsionStation']=i;bar['torsionArm']=kind;bar['torsionAnchorX']=fixed;bar['torsionDrivenX']=x+direction*.30;bar['torsionY']=y;bar['torsionZ']=s*z
        # Native shape keys evaluated from the same twist field as the web mesh.
        bar.shape_key_add(name='Basis');TORSIONS.append((bar,i,kind,vs))
    # Open, ribbed vertical frame bracket and genuine circular sleeve apertures.
    for xx in [-.22,.22]:
        poly=[(.51,s*.505),(.50,s*.435),(1.13,s*.445),(1.16,s*.58),(1.10,s*.62),(.98,s*.55),(.65,s*.51)]
        prism(name+f'_frame_web_{xx}',poly,x+xx-.017,x+xx+.017,PAINT,station,edge=.006,part='ribbed frame-side suspension bracket',source='PHOTO-035',role='frame')
    box(name+'_frame_spine',(.47,.57,.055),(x,.805,s*.449),PAINT,station,.007,part='frame bracket inner web',role='frame')
    for yy in [.565,.73,.93,1.085]:
        for xx in [-.165,.165]:bolt(name+f'_frame_bolt_{yy}_{xx}',(x+xx,yy,s*.482),station,'z',.012,role='frame')
    # Wheels use longitudinal end pins; front pair additionally has steering kingpin.
    upright=empty(name+'_upright',root,(x,*[SPEC['lowerEnd'][0],s*SPEC['lowerEnd'][1]]))
    h=SPEC['upperEnd'][0]-SPEC['lowerEnd'][0];dz=SPEC['upperEnd'][1]-SPEC['lowerEnd'][1]
    poly=[(-.035,-.050),(.03,-.075),(h-.015,s*dz-.055),(h+.05,s*dz), (h+.03,s*dz+.055),(.24,.075),(.08,.075)]
    prism(name+'_upright_casting',poly,-.061,.061,PAINT,upright,edge=.01,part='steering support' if i<4 else 'non-steering wheel support',source='MANUAL-1973-F90',role='upright')
    for yy,zz in [(0,0),(h,s*dz)]:
        cylinder(name+f'_upright_pin_{yy}',.023,.27,(0,yy,zz),POLISH,upright,part='longitudinal outer hinge pin',role='internal')
        for xx in [-.057,.057]:bolt(name+f'_wedge_retainer_{yy}_{xx}',(xx,yy+.035,zz),upright,'y',.006)
    # Vertical kingpin is a reconstruction hardpoint; inclination awaits drawing.
    if i<4:
        cylinder(name+'_steering_kingpin',.030,.29,(0,.15,s*.061),POLISH,upright,'y',48,part='front steering kingpin',role='internal')
        for yy in [.03,.27]:ring(name+f'_kingpin_seal_{yy}',.052,.031,.02,(0,yy,s*.061),RUBBER,upright,'y',32,part='kingpin seal',role='internal')
    # Damper mounting tower with lightening opening and replaceable bump stop.
    ty,tz=SPEC['damperTop']
    for dx in [-.036,.036]:
        poly=[(1.02,s*.59),(1.05,s*.67),(ty+.02,s*(tz+.03)),(ty+.09,s*tz),(1.32,s*.67),(1.17,s*.57)]
        prism(name+f'_damper_tower_{dx}',poly,x-.15+dx-.010,x-.15+dx+.010,PAINT,station,edge=.007,part='damper upper mounting bracket; installation reconstructed',role='frame')
    cylinder(name+'_upper_damper_pin',.018,.14,(x-.15,ty,s*tz),POLISH,station,part='damper upper eye pin',role='internal')
    # Buffer contacts upper arm during compression; lower threaded bolt limits droop.
    box(name+'_buffer_bracket',(.15,.025,.16),(x+.16,1.31,s*.82),PAINT,station,.004,part='compression buffer bracket',role='frame')
    for dx in [-.052,.052]:
        prism(name+f'_buffer_support_gusset_{dx}',[(1.32,s*.48),(1.10,s*.48),(1.295,s*.90),(1.32,s*.90)],x+.16+dx-.009,x+.16+dx+.009,PAINT,station,edge=.003,part='buffer bracket frame gusset; installation reconstructed',role='frame')
    cylinder(name+'_rubber_bump_stop',.056,.075,(x+.16,1.265,s*.82),RUBBER,station,'y',32,part='rubber compression buffer',role='internal')
    cylinder(name+'_droop_limit_bolt',.013,.14,(x+.16,.685,s*.69),STEEL,station,'y',24,part='threaded droop limit bolt',role='internal')
    cylinder(name+'_droop_locknut',.022,.018,(x+.16,.707,s*.69),STEEL,station,'y',6,part='droop stop locknut',role='internal')
    # Double-tube damper. Lower cylinder and upper rod/guard move as rigid parts.
    body=empty(name+'_damper_body',root);rod=empty(name+'_damper_rod',root)
    for parent,label in [(body,'lower'),(rod,'upper')]:
        ring(name+f'_damper_{label}_eye',.057,.027,.06,(0,0,0),PAINT,parent,part='forged damper mounting eye',source='MANUAL-1973-F91',role='damper')
        ring(name+f'_damper_{label}_spherical_bearing',.027,.018,.063,(0,0,0),POLISH,parent,part='damper eye spherical bearing',source='MANUAL-1973-F90',role='internal')
    ring(name+'_damper_outer_reservoir',.053,.048,.445,(0,.2925,0),PAINT,body,'y',48,part='outer damper reservoir',source='MANUAL-1973-F91',role='cover')
    ring(name+'_damper_working_cylinder',.039,.035,.410,(0,.297,0),POLISH,body,'y',48,part='damper working cylinder',source='MANUAL-1973-F91',role='cover')
    cylinder(name+'_damper_base_valve',.035,.024,(0,.101,0),STEEL,body,'y',32,part='base compensation valve assembly',source='MANUAL-1973-F91')
    for yy in [.088,.506]:ring(name+f'_damper_end_cap_{yy}',.054,.012,.025,(0,yy,0),PAINT,body,'y',48,part='reservoir end closure',source='MANUAL-1973-F91',role='damper')
    ring(name+'_damper_rod_guide',.04,.013,.03,(0,.479,0),BRONZE,body,'y',40,part='rod guide and sealing gland',source='MANUAL-1973-F91')
    ring(name+'_damper_gland_seal',.027,.012,.008,(0,.499,0),RUBBER,body,'y',32,part='rod oil seal',source='MANUAL-1973-F91')
    cylinder(name+'_damper_piston_rod',.012,.425,(0,-.2475,0),POLISH,rod,'y',40,part='damper piston rod',source='MANUAL-1973-F91')
    cylinder(name+'_damper_piston',.0345,.027,(0,-.440,0),STEEL,rod,'y',48,part='damper piston and high pressure valve carrier',source='MANUAL-1973-F91')
    for yy in [-.453,-.427]:ring(name+f'_damper_piston_seal_{yy}',.035,.028,.004,(0,yy,0),RUBBER,rod,'y',40,part='piston sealing ring',source='MANUAL-1973-F91')
    for k in range(6):
        a=k/6*2*pi;ring(name+f'_damper_valve_port_{k}',.0038,.0024,.029,(.022*cos(a),-.440,.022*sin(a)),BRONZE,rod,'y',16,part='piston metering passage liner',source='MANUAL-1973-F91')
    ring(name+'_damper_external_guard',.058,.055,.39,(0,-.245,0),PAINT,rod,'y',48,part='telescoping outer dust guard',source='MANUAL-1973-F91',role='cover')
    # Lower eye clevis is rigidly attached to the lower fork.
    arm=bpy.data.objects[name+'_lower'];rz=(SPEC['lowerEnd'][1]-SPEC['lower'][1])*SPEC['damperFraction']
    for dx in [-.049,.049]:ring(name+f'_damper_lower_clevis_{dx}',.045,.018,.023,(-.15+dx,0,s*rz),PAINT,arm,part='lower fork damper clevis',role='arm')
    cylinder(name+'_lower_damper_pin',.018,.15,(-.15,0,s*rz),POLISH,arm,part='lower damper spherical-eye pin',role='internal')
    # Two real forked universal-joint yokes and a sliding male/female halfshaft.
    # Joint angle and spline overlap respond to suspension travel; torque phase
    # and the wheel's internal steering CV mechanism are still separate work.
    for end,sign in [('inner',1),('outer',-1)]:
        shaft=empty(name+'_shaft_'+end,root)
        ring(name+'_shaft_'+end+'_flange',.073,.026,.027,(0,0,0),STEEL,shaft,'y',48,part='halfshaft flange and fork base',source='PHOTO-035',role='shaft')
        for v in [-1,1]:
            box(name+f'_shaft_{end}_yoke_{v}',(.032,.077,.075),(v*.044,sign*.057,0),STEEL,shaft,.009,part='universal joint fork',source='PHOTO-035',role='shaft')
            ring(name+f'_shaft_{end}_needle_cap_{v}',.027,.021,.025,(v*.05,sign*.070,0),POLISH,shaft,part='universal cross needle bearing cup',source='PHOTO-035',role='shaft')
        cylinder(name+'_shaft_'+end+'_cross_x',.015,.116,(0,sign*.07,0),POLISH,shaft,part='universal cross trunnion',source='PHOTO-035',role='shaft')
        cylinder(name+'_shaft_'+end+'_cross_z',.015,.110,(0,sign*.07,0),POLISH,shaft,'z',32,part='universal cross trunnion',source='PHOTO-035',role='shaft')
        for v in [-1,1]:
            box(name+f'_shaft_{end}_tube_yoke_{v}',(.060,.074,.023),(0,sign*.106,v*.043),STEEL,shaft,.007,part='tube-side universal joint fork',source='PHOTO-035',role='shaft')
        if end=='inner':
            cylinder(name+'_halfshaft_male',.024,.405,(0,.325,0),POLISH,shaft,'y',40,part='sliding male halfshaft',source='PHOTO-035',role='shaft')
            for k in range(16):
                a=k/16*2*pi;box(name+f'_halfshaft_spline_{k}',(.006,.17,.006),(.025*cos(a),.445,.025*sin(a)),STEEL,shaft,.001,part='halfshaft sliding spline tooth; count reconstructed',role='internal')
        else:
            ring(name+'_halfshaft_female',.038,.029,.37,(0,-.315,0),STEEL,shaft,'y',40,part='hollow female sliding halfshaft',source='PHOTO-035',role='shaft')
            profile=[(-.535,.030),(-.520,.030)]
            for k in range(9):profile.extend([(-.52+k*.014,.044),(-.513+k*.014,.036)])
            profile.extend([(-.388,.036),(-.388,.030)])
            lathe(name+'_halfshaft_bellows',profile,(0,0,0),RUBBER,shaft,'y',48,closed=True,part='pleated sliding-joint dust boot',source='PHOTO-035',role='shaft')
    # Semantic wheel marker is consumed by the browser wheel carrier.
    empty(name+'_wheel',root)

print('S543_AUTHORED',len(REG),flush=True)
for name,pose in POSES['rest'].items():
    ob=bpy.data.objects.get(name)
    if ob:ob.location=C(pose['p']);ob.rotation_euler.x=pose['rx']
for f in POSES['frames']:
    for name,pose in f['pose'].items():
        ob=bpy.data.objects.get(name)
        if ob:
            ob.location=C(pose['p']);ob.rotation_euler.x=pose['rx']
            ob.keyframe_insert('location',frame=f['frame']);ob.keyframe_insert('rotation_euler',frame=f['frame'])
# Twist keys at angular samples; bar is fixed at the anchor and follows arm at sleeve.
for ob,i,kind,vs in TORSIONS:
    for sign in [-1,1]:
        key=ob.shape_key_add(name='Twist_'+str(sign));angle=sign*.60
        for k,(vx,vy,vz) in enumerate(vs):
            u=(vx-ob['torsionAnchorX'])/(ob['torsionDrivenX']-ob['torsionAnchorX']);a=angle*u;y=vy-ob['torsionY'];z=vz-ob['torsionZ']
            key.data[k].co=C((vx,ob['torsionY']+y*cos(a)-z*sin(a),ob['torsionZ']+y*sin(a)+z*cos(a)))
        for f in POSES['frames']:
            rx=f['pose'][f'S543_{i}_{kind}']['rx'];key.value=max(0,sign*rx/.6);key.keyframe_insert('value',frame=f['frame'])
scene=bpy.context.scene;scene.frame_start=0;scene.frame_end=241;scene.render.fps=30
scene.frame_set(0)
# Neutral exported/rest state, independent of the native articulation preview keys.
for name,pose in POSES['rest'].items():
    ob=bpy.data.objects.get(name)
    if ob:
        ob.location=C(pose['p']);ob.rotation_euler.x=pose['rx'];ob.keyframe_insert('location',frame=0);ob.keyframe_insert('rotation_euler',frame=0)
for ob,*_ in TORSIONS:
    for key in list(ob.data.shape_keys.key_blocks)[1:]:key.value=0;key.keyframe_insert('value',frame=0)
scene.unit_settings.system='METRIC';scene.render.engine='CYCLES';scene.cycles.samples=32;scene.cycles.use_denoising=True
try:
    prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices()
    for d in prefs.devices:d.use=d.type!='CPU'
    scene.cycles.device='GPU'
except:pass
scene.render.resolution_x=1500;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast'
scene.view_settings.exposure=-.45
world=bpy.data.worlds.new('Suspension workshop');world.use_nodes=True;world.node_tree.nodes['Background'].inputs['Strength'].default_value=.25;scene.world=world
for name,pos,power,size in [('S543_KEY',(-4,5,3),1500,5),('S543_RIM',(4,4,-4),2200,5),('S543_FILL',(-6,2,-2),900,4)]:
    data=bpy.data.lights.new(name,'AREA');data.energy=power;data.size=size;ob=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(ob);ob.location=C(pos);ob.rotation_euler=(C((.4,.8,0))-ob.location).to_track_quat('-Z','Y').to_euler()
camera=bpy.data.objects.new('S543_CAMERA',bpy.data.cameras.new('S543_CAMERA'));bpy.context.collection.objects.link(camera)
camera.location=C((-7.5,3.9,7.8));camera.rotation_euler=(C((.5,.85,0))-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.lens=46;scene.camera=camera
text=bpy.data.texts.new('S543_REFERENCE_REGISTER');text.write((ROOT/'docs/SUSPENSION_REFERENCE_REGISTER.md').read_text(encoding='utf-8'))
def descendants(o):
    result=[]
    for c in o.children:result.append(c);result+=descendants(c)
    return result
collection=bpy.data.collections.new('S543_SUSPENSION');scene.collection.children.link(collection)
for ob in [root]+descendants(root):
    for c in list(ob.users_collection):c.objects.unlink(ob)
    collection.objects.link(ob)
refs=bpy.data.collections.new('S543_REFERENCES');scene.collection.children.link(refs)
for path in [Path('D:/maz543-references/suspension/1973-fig90-suspension.jpg'),Path('D:/maz543-references/suspension/1973-fig91-damper.jpg'),Path('D:/maz543-references/suspension/candidates/maz-543_scud_b_tel_035_of_192.jpg')]:
    im=bpy.data.images.load(str(path));im.pack();ob=bpy.data.objects.new('S543_REF_'+path.stem,None);refs.objects.link(ob);ob.empty_display_type='IMAGE';ob.data=im;ob.hide_render=True;ob.hide_viewport=True
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'MAZ543A_Suspension_Master.blend'),compress=True)
scene.render.filepath=str(OUT/'maz543a-suspension.png');bpy.ops.render.render(write_still=True)
# Close view of wheel station 1, retaining authored details in the native master.
for ob in [root]+descendants(root):
    if ob.name.startswith('S543_') and len(ob.name)>5 and ob.name[5].isdigit():ob.hide_render=not ob.name.startswith('S543_1_')
camera.location=C((-4.4,1.7,2.35));camera.rotation_euler=(C((-2.7,.9,.76))-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.lens=58
scene.render.filepath=str(OUT/'maz543a-suspension-detail.png');bpy.ops.render.render(write_still=True)
for ob in descendants(root):ob.hide_render=False
sys.path.insert(0,str(ROOT/'scripts'))
from suspension_asset import export_suspension
export_suspension(root)
(OUT/'suspension-parts-register.json').write_text(json.dumps(REG,indent=2),encoding='utf-8')
print('S543_COMPLETE',len(REG),flush=True)
