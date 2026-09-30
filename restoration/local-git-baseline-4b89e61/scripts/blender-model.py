"""MAZ-543 family reference reconstruction in Blender 4.5 LTS.
Native mesh bodywork, window apertures, rounded seals, lathed wheel profiles,
curved tread meshes, authored surface materials, and named mechanical pivots.
The imported mechanism is a simplified kinematic demonstrator, not factory CAD.
"""
import bpy, bmesh, math, json, os, sys, random
from mathutils import Vector, Matrix
from math import sin, cos, pi, sqrt
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs'; OUT.mkdir(exist_ok=True)
TEX=ROOT/'public'/'models'/'textures'; TEX.mkdir(parents=True,exist_ok=True)
MANIFEST=json.loads((ROOT/'work'/'mechanical-manifest.json').read_text())
random.seed(543)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(ROOT/'work'/'mechanical-seed.glb'),loglevel=50)

def C(p): return Vector((p[0],-p[2],p[1]))
def to3(p): return (p.x,p.z,-p.y)
def parent_keep(obj,parent):
    if isinstance(parent,str): parent=bpy.data.objects[parent]
    world=obj.matrix_world.copy();obj.parent=parent;obj.matrix_world=world
    return obj
def clear_children(obj):
    for child in list(obj.children):
        clear_children(child);bpy.data.objects.remove(child,do_unlink=True)
def assign(obj,mat):
    obj.data.materials.clear();obj.data.materials.append(mat);return obj
def bevel(obj,width=.015,segments=3):
    mod=obj.modifiers.new('Manufactured edge radii','BEVEL');mod.width=width;mod.segments=segments;mod.limit_method='ANGLE'
    mod.affect='EDGES';mod.harden_normals=True
    normal=obj.modifiers.new('Weighted surface normals','WEIGHTED_NORMAL');normal.keep_sharp=True;normal.weight=40
    return obj
def mesh(name,verts,faces,mat,parent=None,edge=0,smooth=False):
    data=bpy.data.meshes.new(name+'_Topology');data.from_pydata([C(v) for v in verts],[],faces);data.update()
    obj=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(obj);assign(obj,mat)
    if smooth:
        for poly in data.polygons:poly.use_smooth=True
    if edge:bevel(obj,edge,3)
    uv=data.uv_layers.new(name='SurfaceUV')
    for poly in data.polygons:
        axis=max(range(3),key=lambda i:abs(poly.normal[i]))
        for li in poly.loop_indices:
            co=data.vertices[data.loops[li].vertex_index].co
            uv.data[li].uv=(co[(axis+1)%3],co[(axis+2)%3])
    if parent:parent_keep(obj,parent)
    return obj
def box(name,size,pos,mat,parent=None,edge=.01):
    dx,dy,dz=[v/2 for v in size];x,y,z=pos
    vs=[(x+sx*dx,y+sy*dy,z+sz*dz) for sx,sy,sz in [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]]
    return mesh(name,vs,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],mat,parent,edge)
def cylinder(name,r,length,pos,mat,parent=None,axis='y',segments=48,edge=.004):
    vs=[]
    for d in [-length/2,length/2]:
        for i in range(segments):
            a=i/segments*2*pi
            off=(d,r*cos(a),r*sin(a)) if axis=='x' else (r*cos(a),d,r*sin(a)) if axis=='y' else (r*cos(a),r*sin(a),d)
            vs.append(tuple(pos[j]+off[j] for j in range(3)))
    fs=[tuple(range(segments-1,-1,-1)),tuple(range(segments,segments*2))]
    fs += [(i,(i+1)%segments,(i+1)%segments+segments,i+segments) for i in range(segments)]
    return mesh(name,vs,fs,mat,parent,edge,True)
def rod(name,points,radius,mat,parent=None,cyclic=False):
    curve=bpy.data.curves.new(name+'_Curve','CURVE');curve.dimensions='3D';curve.resolution_u=2;curve.bevel_depth=radius;curve.bevel_resolution=2
    spline=curve.splines.new('POLY');spline.points.add(len(points)-1)
    for p,co in zip(spline.points,points):p.co=(*C(co),1)
    spline.use_cyclic_u=cyclic
    obj=bpy.data.objects.new(name,curve);bpy.context.collection.objects.link(obj);obj.data.materials.append(mat)
    if parent:parent_keep(obj,parent)
    return obj
def rounded_poly(points,radius=.08,steps=5):
    result=[]
    for i,p in enumerate(points):
        prev=Vector(points[(i-1)%len(points)]);cur=Vector(p);nxt=Vector(points[(i+1)%len(points)])
        f=min(radius,(cur-prev).length*.25,(cur-nxt).length*.25)
        a=cur+(prev-cur).normalized()*f;b=cur+(nxt-cur).normalized()*f
        for k in range(steps+1):
            t=k/steps;q=(1-t)**2*a+2*(1-t)*t*cur+t*t*b;result.append(tuple(q))
    return result
def polygon_prism(name,poly,mapfn,depth,mat,parent,edge=.005):
    n=len(poly);v=[mapfn(u,v,d) for d in [0,depth] for u,v in poly]
    f=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    return mesh(name,v,f,mat,parent,edge)
def aperture(name,outer,inner,mapfn,thickness,mat,parent):
    # Matched polygon control rings create a genuine opening, not a black decal.
    assert len(outer)==len(inner)
    n=len(outer);v=[mapfn(*p,d) for d in [0,thickness] for ring in [outer,inner] for p in ring];f=[]
    for i in range(n):
        j=(i+1)%n
        f.extend([(i,j,n+j,n+i),(2*n+j,2*n+i,3*n+i,3*n+j),(i,2*n+i,2*n+j,j),(n+j,3*n+j,3*n+i,n+i)])
    return mesh(name,v,f,mat,parent,.008)
def scale_poly(poly,f):
    center=sum((Vector(p) for p in poly),Vector((0,0)))/len(poly)
    return [tuple(center+(Vector(p)-center)*f) for p in poly]
def rivets(name,poly,mapfn,parent,spacing=.15,r=.009):
    verts=[];faces=[]
    for i,a in enumerate(poly):
        b=poly[(i+1)%len(poly)];av=Vector(a);bv=Vector(b);n=max(1,int((bv-av).length/spacing))
        for j in range(n):
            p=av.lerp(bv,(j+.5)/n);center=mapfn(*p,0);off=len(verts)
            # Low dome rivets have real silhouettes and tiny bevel highlights.
            for ring in range(3):
                rad=r*(1 if ring==0 else .85 if ring==1 else .2);d=ring*r*.33
                for k in range(8):
                    q=Vector(p)+Vector((cos(k*pi/4),sin(k*pi/4)))*rad;verts.append(mapfn(*q,d))
            for row in range(2):
                for k in range(8):faces.append((off+row*8+k,off+row*8+(k+1)%8,off+(row+1)*8+(k+1)%8,off+(row+1)*8+k))
            faces.append(tuple(off+16+k for k in range(8)))
    return mesh(name,verts,faces,PAINT,parent,0,True)
def material(name,color,metal=.0,rough=.75,noise=.12):
    mat=bpy.data.materials.new(name);mat.use_nodes=True;n=mat.node_tree.nodes;l=mat.node_tree.links;n.clear()
    out=n.new('ShaderNodeOutputMaterial');out.location=(700,0)
    bs=n.new('ShaderNodeBsdfPrincipled');bs.location=(430,0);bs.inputs['Base Color'].default_value=(*color,1);bs.inputs['Metallic'].default_value=metal;bs.inputs['Roughness'].default_value=rough;l.new(bs.outputs['BSDF'],out.inputs['Surface'])
    tex=n.new('ShaderNodeTexNoise');tex.location=(-600,100);tex.inputs['Scale'].default_value=35;tex.inputs['Detail'].default_value=5;tex.inputs['Roughness'].default_value=.7
    coords=n.new('ShaderNodeTexCoord');coords.location=(-850,0);l.new(coords.outputs['Generated'],tex.inputs['Vector'])
    ramp=n.new('ShaderNodeValToRGB');ramp.location=(-310,140);ramp.color_ramp.elements[0].position=.16;ramp.color_ramp.elements[0].color=(*(max(0,c*(1-noise)) for c in color),1);ramp.color_ramp.elements[1].position=.84;ramp.color_ramp.elements[1].color=(*(min(1,c*(1+noise)) for c in color),1);l.new(tex.outputs['Fac'],ramp.inputs['Fac']);l.new(ramp.outputs['Color'],bs.inputs['Base Color'])
    micro=n.new('ShaderNodeTexNoise');micro.location=(-580,-240);micro.inputs['Scale'].default_value=320;micro.inputs['Detail'].default_value=2;l.new(coords.outputs['Generated'],micro.inputs['Vector'])
    bump=n.new('ShaderNodeBump');bump.location=(180,-180);bump.inputs['Strength'].default_value=.18;bump.inputs['Distance'].default_value=.0006;l.new(micro.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs['Normal'],bs.inputs['Normal'])
    remap=n.new('ShaderNodeMapRange');remap.location=(-70,-20);remap.inputs['To Min'].default_value=rough-.12;remap.inputs['To Max'].default_value=min(1,rough+.12);l.new(tex.outputs['Fac'],remap.inputs['Value']);l.new(remap.outputs['Result'],bs.inputs['Roughness'])
    mat.diffuse_color=(*color,1);return mat

# Physically separate paint, iron, rubber, worn metal, upholstery and glazing.
PAINT=material('OD_green_aged_enamel',(.043,.061,.025),.08,.75,.32)
PAINT_DARK=material('OD_green_shadow',(.025,.039,.018),.1,.8,.25)
METAL=material('Phosphated_steel',(.09,.105,.095),.8,.46,.15)
SILVER=material('Worn_steel',(.38,.40,.37),.86,.36,.12)
RUBBER=material('Tyre_rubber',(.028,.031,.027),.0,.87,.35)
SEAL=material('Rubber_window_seals',(.012,.017,.014),.0,.73,.10)
RUST=material('Oxidised_edges',(.18,.092,.040),.3,.92,.30)
LEATHER=material('Worn_brown_vinyl',(.07,.047,.033),.0,.7,.2)
GLASS=material('Laminated_glass',(.32,.41,.36),0,.08,.015)
bs=next(n for n in GLASS.node_tree.nodes if n.type=='BSDF_PRINCIPLED');bs.inputs['Transmission Weight'].default_value=.75;bs.inputs['Alpha'].default_value=.33;bs.inputs['IOR'].default_value=1.5;GLASS.surface_render_method='DITHERED'
LAMP=material('Headlamp_prismatic_glass',(.68,.66,.52),.05,.19,.05)
AMBER=material('Amber_signal_glass',(.46,.12,.015),.1,.28,.04)
WHITE=material('Faded_stencil',(.62,.64,.52),0,.9,.12)
for obj in list(bpy.data.objects):
    if obj.type=='MESH':
        for slot in obj.material_slots:
            name=slot.material.name if slot.material else ''
            if name in ['olive','edge','engine']:slot.material=PAINT
            elif name in ['dark','black']:slot.material=METAL
            elif name in ['rubber','tread']:slot.material=RUBBER
            elif name in ['bright','steel']:slot.material=SILVER
            elif name=='seat':slot.material=LEATHER
            elif name=='glass':slot.material=GLASS
        obj['provenance']='Simplified mechanical reconstruction'

# Empty hierarchy remains as a mechanically addressable rig. Exterior is replaced.
cab=bpy.data.objects['cab'];body=bpy.data.objects['body']
for name in ['cab_pivot_001','cab_pivot_005']:
    clear_children(bpy.data.objects[name])
for door in MANIFEST['doors']:clear_children(bpy.data.objects[door['name']])
clear_children(body)

print('BLENDER_MATERIALS_AND_RIG_READY',flush=True)

# Cabin shell: source-guided front glass silhouette and a continuous side skin.
for side,shell_name in [(-1,'cab_pivot_001'),(1,'cab_pivot_005')]:
    shell=bpy.data.objects[shell_name];zc=side*1.055
    # Front facade leans aft towards the roof. The inside lower windshield corner
    # is cut diagonally, characteristic of the MAZ-543 split cabin.
    def front(u,v,d=0):return (-5.45+max(0,v-1.94)*.40-d,v,side*(.535+u))
    outer=[(.08,2.66),(.85,2.66),(.97,2.53),(.99,1.29),(.88,1.17),(.02,1.17),(.02,1.90),(.04,2.30)]
    window=[(.16,2.54),(.80,2.54),(.86,2.45),(.90,2.07),(.83,2.015),(.32,2.015),(.13,2.23),(.13,2.43)]
    out=rounded_poly(outer,.065,6);inn=rounded_poly(window,.055,6)
    facade=aperture(f'BL_Cab_{side}_front_shell',out,inn,front,-.045,PAINT,shell);facade['surface']='exterior'
    gasket=aperture(f'BL_Cab_{side}_windscreen_gasket',scale_poly(inn,1.018),scale_poly(inn,.928),lambda u,v,d:front(u,v,.009+d),-.009,SEAL,shell)
    glass=polygon_prism(f'BL_Cab_{side}_windscreen',scale_poly(inn,.926),lambda u,v,d:front(u,v,-.006+d),-.008,GLASS,shell,0)
    # Real pressed recess beneath glass, with a single circular main light.
    hatch=rounded_poly([(.37,1.70),(.63,1.70),(.63,1.56),(.37,1.56)],.055,7)
    polygon_prism(f'BL_Cab_{side}_vent_seal',scale_poly(hatch,1.10),lambda u,v,d:front(u,v,.007+d),.004,SEAL,shell,.003)
    polygon_prism(f'BL_Cab_{side}_vent_cover',hatch,lambda u,v,d:front(u,v,.016+d),.012,PAINT,shell,.012)
    lamp_pos=front(.81,1.56,.036)
    cylinder(f'BL_Cab_{side}_headlamp_bucket',.121,.07,lamp_pos,PAINT_DARK,shell,'x',64,.009)
    cylinder(f'BL_Cab_{side}_headlamp_chrome',.104,.016,(lamp_pos[0]-.041,lamp_pos[1],lamp_pos[2]),SILVER,shell,'x',64,.004)
    cylinder(f'BL_Cab_{side}_headlamp_lens',.094,.016,(lamp_pos[0]-.053,lamp_pos[1],lamp_pos[2]),LAMP,shell,'x',64,.004)
    # Fresnel-like molded lens ribs provide close-range detail.
    for k in range(-8,9):
        z=lamp_pos[2]+k*.01;dy=sqrt(max(0,.085**2-(k*.01)**2))
        rod(f'BL_Lens_{side}_{k}',[(lamp_pos[0]-.064,lamp_pos[1]-dy,z),(lamp_pos[0]-.064,lamp_pos[1]+dy,z)],.0014,LAMP,shell)
    rod(f'BL_Cab_{side}_wiper_arm',[front(.45,2.53,.031),front(.54,2.11,.049)],.0075,METAL,shell)
    rod(f'BL_Cab_{side}_wiper_blade',[front(.47,2.35,.058),front(.57,2.04,.058)],.011,SEAL,shell)
    rivets(f'BL_Cab_{side}_nose_rivets',[(.07,1.23),(.9,1.23),(.96,1.88),(.1,1.9)],front,shell,.14,.008)

    # Side profile rises around the first wheel; the body has no solid window fill.
    side_outline=rounded_poly([(-5.43,1.39),(-5.38,2.02),(-5.18,2.66),(-2.93,2.66),(-2.89,1.77),(-3.49,1.12),(-4.98,1.12)],.08,5)
    def side_map(u,v,d=0):return (u,v,side*(1.51+d))
    side_skin=polygon_prism(f'BL_Cab_{side}_side_monocoque',side_outline,side_map,-.037,PAINT,shell,.022)
    # Doors are fitted into boolean-cut apertures in the outer monocoque.
    for n,(start,end,door_idx) in enumerate([(-4.91,-4.03,0),(-3.96,-3.01,1)]):
        door_ref=MANIFEST['doors'][(0 if side==-1 else 2)+door_idx]['name'];door=bpy.data.objects[door_ref]
        door_outline=rounded_poly([(start,2.55),(end-.07,2.55),(end,2.45),(end,1.60),(end-.31,1.28),(start,1.28)],.085,7)
        cutter=polygon_prism('TEMP_door_aperture',scale_poly(door_outline,1.008),lambda u,v,d:(u,v,side*(1.68+d)),-.4,PAINT,shell,0)
        bpy.context.view_layer.objects.active=side_skin;mod=side_skin.modifiers.new('Machined door opening','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cutter
        # Apply boolean before the skin bevel, to retain real thickness at openings.
        bpy.ops.object.modifier_move_up(modifier=mod.name)
        bpy.ops.object.modifier_move_up(modifier=mod.name)
        bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cutter,do_unlink=True)
        win=rounded_poly([(start+.10,2.48),(end-.16,2.48),(end-.08,2.40),(end-.08,2.07),(end-.18,1.99),(start+.10,1.99)],.085,7)
        # Both contours have six authored corners and are sampled consistently.
        dmesh=aperture(f'BL_Door_{side}_{n}_pressed_shell',door_outline,win,lambda u,v,d:side_map(u,v,.012+d),-.045,PAINT,door);dmesh['surface']='exterior'
        aperture(f'BL_Door_{side}_{n}_rubber_seal',scale_poly(win,1.045),scale_poly(win,.96),lambda u,v,d:side_map(u,v,.030+d),-.009,SEAL,door)
        polygon_prism(f'BL_Door_{side}_{n}_window',scale_poly(win,.952),lambda u,v,d:side_map(u,v,.022+d),-.007,GLASS,door,0)
        # Door gap, three rolled hinges, stamped handle recess and key cylinder.
        rod(f'BL_Door_{side}_{n}_gap',[side_map(u,v,.019) for u,v in door_outline],.005,SEAL,door,True)
        for h in [1.47,1.94,2.38]:
            cylinder(f'BL_Door_{side}_{n}_hinge_{h}',.018,.103,(start+.018,h,side*1.548),PAINT,door,'y',24,.004)
        cylinder(f'BL_Door_{side}_{n}_handle_recess',.056,.012,(end-.14,1.81,side*1.545),SEAL,door,'z',40,.003)
        rod(f'BL_Door_{side}_{n}_handle',[(end-.16,1.81,side*1.56),(end-.12,1.81,side*1.575)],.012,METAL,door)
        cylinder(f'BL_Door_{side}_{n}_lock',.013,.018,(end-.15,1.70,side*1.55),SILVER,door,'z',20,.001)
        rivets(f'BL_Door_{side}_{n}_fasteners',scale_poly(door_outline,.965),lambda u,v,d:side_map(u,v,.024+d),door,.2,.006)
    # Narrow quarterlight ahead of the first door.
    quarter=rounded_poly([(-5.16,2.57),(-4.96,2.53),(-4.96,2.09),(-5.32,1.98)],.035,7)
    cutter=polygon_prism('TEMP_quarterlight',quarter,lambda u,v,d:(u,v,side*(1.7+d)),-.4,PAINT,shell,0)
    bpy.context.view_layer.objects.active=side_skin;mod=side_skin.modifiers.new('Quarterlight aperture','BOOLEAN');mod.operation='DIFFERENCE';mod.object=cutter;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cutter,do_unlink=True)
    aperture(f'BL_Cab_{side}_quarterlight_frame',scale_poly(quarter,1.05),scale_poly(quarter,.91),lambda u,v,d:side_map(u,v,.008+d),-.009,SEAL,shell)
    polygon_prism(f'BL_Cab_{side}_quarterlight_glass',scale_poly(quarter,.9),lambda u,v,d:side_map(u,v,.002+d),-.007,GLASS,shell,0)
    rivets(f'BL_Cab_{side}_side_rivets',scale_poly(side_outline,.965),lambda u,v,d:side_map(u,v,.012+d),shell,.14,.008)
    # Crowned roof skin uses a quad grid and subdivision; not a rectangular slab.
    roof_verts=[];roof_faces=[];nx=14;nz=10
    for i in range(nx+1):
        x=-5.17+i/nx*2.26
        for j in range(nz+1):
            z=side*(.56+j/nz*.95);y=2.65+.018*sin(pi*j/nz)+.012*sin(pi*i/nx);roof_verts.append((x,y,z))
    for i in range(nx):
        for j in range(nz):a=i*(nz+1)+j;roof_faces.append((a,a+1,a+nz+2,a+nz+1))
    roof=mesh(f'BL_Cab_{side}_crowned_roof',roof_verts,roof_faces,PAINT,shell,0,True)
    sub=roof.modifiers.new('Roof curvature subdivision','SUBSURF');sub.levels=1;sub.render_levels=2
    sol=roof.modifiers.new('Glass fibre wall thickness','SOLIDIFY');sol.thickness=.03
    rod(f'BL_Cab_{side}_rain_gutter',[(-5.17,2.647,side*1.518),(-4.9,2.655,side*1.518),(-2.91,2.647,side*1.518)],.014,PAINT_DARK,shell)
    # Inner wall, rear bulkhead and sloped sill maintain an actual hollow cabin.
    box(f'BL_Cab_{side}_rear_bulkhead',[.045,1.18,.95],[-2.91,2.07,side*1.035],PAINT,shell,.018)
    inner_panel=polygon_prism(f'BL_Cab_{side}_inner_wall',rounded_poly([(-5.35,1.31),(-5.15,2.62),(-2.93,2.62),(-2.93,1.53),(-3.49,1.18)],.045,5),lambda u,v,d:(u,v,side*(.555+d)),.028,PAINT,shell,.012)
    rod(f'BL_Cab_{side}_step',[(-4.80,1.12,side*1.48),(-4.80,.95,side*1.48),(-4.7,.90,side*1.52),(-3.63,.90,side*1.52),(-3.55,1.13,side*1.48)],.023,METAL,cab)
    for j in range(20):box(f'BL_Step_{side}_{j}',[.025,.009,.12],[-4.68+j*.052,.928,side*1.52],SILVER,cab,.003)
    # Standoff mirror and reflector, with a metal back, thin reflective face.
    rod(f'BL_Cab_{side}_mirror_stalk',[(-5.12,2.42,side*1.52),(-5.10,2.33,side*1.66),(-4.94,2.20,side*1.68)],.012,METAL,shell)
    box(f'BL_Cab_{side}_mirror_back',[.105,.22,.05],[-4.96,2.22,side*1.68],PAINT_DARK,shell,.023)
    box(f'BL_Cab_{side}_mirror_face',[.089,.19,.008],[-4.96,2.22,side*1.711],SILVER,shell,.015)
    rod(f'BL_Cab_{side}_roof_handles',[(-3.66,2.68,side*1.18),(-3.66,2.735,side*1.18),(-3.37,2.735,side*1.18),(-3.37,2.68,side*1.18)],.011,METAL,shell)
    if side==-1:
        cylinder('BL_Searchlight_stand',.035,.15,(-3.42,2.74,side*1.03),METAL,shell,'y',32,.006)
        cylinder('BL_Searchlight_housing',.12,.18,(-3.42,2.875,side*1.03),PAINT,shell,'x',64,.012)
        cylinder('BL_Searchlight_lens',.103,.01,(-3.522,2.875,side*1.03),LAMP,shell,'x',64,.003)
print('BLENDER_CABIN_TOPOLOGY_READY',flush=True)

# Central nose radiator and its protective grille (a defining front-view detail).
box('BL_Radiator_core',[.20,.62,1.13],[-5.42,1.54,0],METAL,body,.013)
for z in [-.638,.638]:box(f'BL_Radiator_side_{z}',[.29,.74,.06],[-5.47,1.56,z],PAINT,body,.012)
for y in [1.185,1.925]:box(f'BL_Radiator_horizontal_{y}',[.29,.06,1.31],[-5.47,y,0],PAINT,body,.012)
for j in range(35):box(f'BL_Radiator_fins_{j}',[.07,.65,.009],[-5.59,1.55,-.59+j*.0347],PAINT_DARK,body,.003)
for y in [1.33,1.76]:rod(f'BL_Radiator_guard_{y}',[(-5.66,y,-.62),(-5.66,y,.62)],.017,METAL,body)
for z in [-.44,0,.44]:rod(f'BL_Radiator_vertical_{z}',[(-5.66,1.27,z),(-5.66,1.84,z)],.013,METAL,body)
box('BL_Radiator_top_hatch',[.43,.045,1.21],[-5.35,1.982,0],PAINT,body,.02)
for z in [-.43,.43]:rod(f'BL_Radiator_latch_{z}',[(-5.42,2.01,z-.07),(-5.45,2.04,z-.07),(-5.45,2.04,z+.07),(-5.42,2.01,z+.07)],.009,METAL,body)

# Front beam has stamped ends, towing eyes, amber lamps and tubular marker stalks.
bumper_profile=rounded_poly([(-1.515,1.18),(1.515,1.18),(1.515,.92),(1.35,.86),(-1.35,.86),(-1.515,.92)],.025,4)
polygon_prism('BL_Front_crossmember',bumper_profile,lambda z,y,d:(-5.58+d,y,z),.21,METAL,'frame',.014)
for s in [-1,1]:
    cylinder(f'BL_Bumper_signal_rim_{s}',.085,.015,(-5.60,1.065,s*1.35),SEAL,'frame','x',48,.003)
    cylinder(f'BL_Bumper_signal_{s}',.065,.018,(-5.611,1.065,s*1.35),AMBER,'frame','x',48,.004)
    rod(f'BL_Width_marker_{s}',[(-5.52,1.19,s*1.44),(-5.50,1.4,s*1.65),(-5.50,1.52,s*1.65)],.014,PAINT,'frame')
    cylinder(f'BL_Width_marker_cap_{s}',.028,.045,(-5.50,1.535,s*1.65),PAINT,'frame','y',24,.007)
    rod(f'BL_Tow_shackle_{s}',[(-5.70,.975,s*.68),(-5.74,.88,s*.68),(-5.72,.82,s*.68),(-5.65,.84,s*.68),(-5.63,.96,s*.68)],.027,METAL,'frame')

# A-series engine enclosure, authored with rolled corners and service apertures.
hood_poly=rounded_poly([(-2.88,1.65),(-2.88,2.61),(-2.60,2.67),(-.49,2.67),(-.40,2.50),(-.40,1.65)],.05,5)
for s in [-1,1]:
    polygon_prism(f'BL_Power_bay_side_{s}',hood_poly,lambda x,y,d:(x,y,s*(1.36+d)),-.035,PAINT,body,.016)
    # Long stamped louver bank, and a smaller forward inspection lid.
    box(f'BL_Louver_recess_{s}',[1.40,.41,.018],[-1.18,2.20,s*1.389],SEAL,body,.016)
    for k in range(11):
        y=2.025+k*.035
        blade=box(f'BL_Louver_blade_{s}_{k}',[1.36,.018,.035],[-1.18,y,s*1.412],PAINT,body,.006)
    lid=rounded_poly([(-2.68,1.81),(-2.68,2.48),(-2.02,2.48),(-2.02,1.81)],.04,5)
    polygon_prism(f'BL_Bay_door_gasket_{s}',scale_poly(lid,1.027),lambda x,y,d:(x,y,s*(1.383+d)),.007,SEAL,body,.003)
    polygon_prism(f'BL_Bay_door_{s}',lid,lambda x,y,d:(x,y,s*(1.395+d)),.015,PAINT,body,.015)
    for x in [-2.60,-2.12]:
        box(f'BL_Bay_hinge_{s}_{x}',[.07,.09,.028],[x,2.47,s*1.425],METAL,body,.009)
    rod(f'BL_Bay_handle_{s}',[(-2.43,1.99,s*1.422),(-2.43,2.03,s*1.45),(-2.27,2.03,s*1.45),(-2.27,1.99,s*1.422)],.009,METAL,body)
    for x in [-2.85,-.47]:
        for y in [1.72,2.52]:cylinder(f'BL_Bay_bolt_{s}_{x}_{y}',.014,.014,(x,y,s*1.40),SILVER,body,'z',6,.002)
    # Real sheet-metal mudguards follow the shoulder of the two front wheels.
    for x in [-3.08,-.88]:
        points=[(x-.84,1.13),(x-.74,1.56),(x-.53,1.62),(x+.54,1.62),(x+.77,1.5),(x+.86,1.08)]
        vs=[];fs=[]
        for zz in [s*.87,s*1.49]:
            for xx,yy in points:vs.append((xx,yy,zz))
        for k in range(len(points)-1):fs.append((k,k+1,k+1+len(points),k+len(points)))
        fender=mesh(f'BL_Fender_{s}_{x}',vs,fs,PAINT,body,.008);sol=fender.modifiers.new('Pressed sheet thickness','SOLIDIFY');sol.thickness=.014
        for zz in [s*.88,s*1.48]:rod(f'BL_Fender_rolled_edge_{s}_{x}_{zz}',[(xx,yy,zz) for xx,yy in points],.012,PAINT,body)
        box(f'BL_Mudflap_{s}_{x}',[.017,.49,.6],[x+.85,.96,s*1.19],RUBBER,body,.009)
    # Rear toolbox with fold lines and mechanical latches.
    box(f'BL_Rear_box_{s}',[.57,.43,.61],[5.09,1.41,s*.98],PAINT,body,.022)
    box(f'BL_Rear_box_lid_{s}',[.585,.035,.625],[5.09,1.647,s*.98],PAINT,body,.015)
    for x in [4.94,5.24]:box(f'BL_Rear_box_latch_{s}_{x}',[.039,.085,.027],[x,1.56,s*1.298],METAL,body,.008)
    for x in [4.79,5.40]:cylinder(f'BL_Rear_marker_{s}_{x}',.041,.032,(x,1.19,s*1.17),AMBER,body,'x',32,.003)
# Compound hood crown; actual quad skin with shaped end caps.
v=[];f=[]
cross=[(-1.36,2.57),(-1.26,2.65),(-.86,2.695),(0,2.705),(.86,2.695),(1.26,2.65),(1.36,2.57)]
for x in [-2.88,-2.80,-.50,-.40]:
    for z,y in cross:v.append((x,y,z))
for i in range(3):
    for j in range(6):a=i*7+j;f.append((a,a+7,a+8,a+1))
hood=mesh('BL_Power_bay_crown',v,f,PAINT,body,.015,True);sol=hood.modifiers.new('Panel gauge','SOLIDIFY');sol.thickness=.025
for x in [-2.6,-1.9,-1.2]:
    for s in [-1,1]:
        box(f'BL_Hood_access_{s}_{x}',[.46,.025,.50],[x,2.732,s*.71],PAINT,body,.025)
        rod(f'BL_Hood_handle_{s}_{x}',[(x-.06,2.75,s*.71),(x-.06,2.79,s*.71),(x+.06,2.79,s*.71),(x+.06,2.75,s*.71)],.009,METAL,body)
print('BLENDER_BODYWORK_READY',flush=True)

# Rear axles of the reference bare chassis are exposed. Retain rear splash
# curtains, and add the tall cast final-drive housings visible above the rails.
for s in [-1,1]:box(f'BL_Rear_splash_curtain_{s}',[.022,.54,.62],[5.46,.96,s*1.19],RUBBER,body,.009)
for ai,x in enumerate([-3.08,-.88,2.42,4.62]):
    profile=[(-.34,.77),(-.31,1.02),(-.20,1.21),(-.11,1.44),(.08,1.49),(.23,1.31),(.32,1.04),(.32,.77)]
    # Each longitudinal section varies in width to form a cast, ribbed casing.
    vs=[];fs=[]
    for z,scale in [(-.30,.83),(-.26,.96),(-.18,1),(0,1),(.18,1),(.26,.96),(.30,.83)]:
        for dx,y in profile:vs.append((x+dx*scale,.78+(y-.78)*scale,z))
    for row in range(6):
        for j in range(8):fs.append((row*8+j,row*8+(j+1)%8,(row+1)*8+(j+1)%8,(row+1)*8+j))
    fs.extend([tuple(range(7,-1,-1)),tuple(range(48,56))])
    casing=mesh(f'BL_Final_drive_{ai}_cast_housing',vs,fs,PAINT_DARK,'drive',.021,True);casing['surface']='exterior'
    for z in [-.31,.31]:
        ring=[(x+.245*cos(k/32*2*pi),1.045+.245*sin(k/32*2*pi),z) for k in range(32)];rod(f'BL_Final_drive_{ai}_cover_seam_{z}',ring,.012,METAL,'drive',True)
        for k in range(10):
            a=k/10*2*pi;cylinder(f'BL_Final_drive_{ai}_cover_bolt_{z}_{k}',.014,.020,(x+.22*cos(a),1.045+.22*sin(a),z),METAL,'drive','z',6,.002)
    for dx in [-.2,.05,.22]:rod(f'BL_Final_drive_{ai}_casting_rib_{dx}',[(x+dx,.85,-.31),(x+dx,1.22,-.24),(x+dx,1.37,0),(x+dx,1.22,.24),(x+dx,.85,.31)],.016,PAINT_DARK,'drive')

def lathe(name,profile,center,mat,parent,segments=128):
    vs=[];fs=[]
    for z,r in profile:
        for i in range(segments):
            a=i/segments*2*pi;vs.append((center[0]+r*cos(a),center[1]+r*sin(a),center[2]+z))
    for row in range(len(profile)-1):
        for i in range(segments):j=(i+1)%segments;fs.append((row*segments+i,row*segments+j,(row+1)*segments+j,(row+1)*segments+i))
    obj=mesh(name,vs,fs,mat,parent,0,True)
    uv=obj.data.uv_layers.active
    for poly in obj.data.polygons:
        for li in poly.loop_indices:
            vi=obj.data.loops[li].vertex_index;uv.data[li].uv=(vi%segments/segments,vi//segments/(len(profile)-1))
    return obj
for wi,w in enumerate(MANIFEST['wheels']):
    spin=bpy.data.objects[w['spin']];clear_children(spin);x=w['x'];side=w['side'];zc=side*1.1875;center=(x,.75,zc)
    bpy.data.objects[w['hub']].location.y=-side*.18
    profile=[(-.248,.322),(-.260,.34),(-.282,.41),(-.301,.50),(-.303,.58),(-.290,.64),(-.262,.683),(-.23,.709),(-.17,.723),(-.10,.727),(0,.729),(.10,.727),(.17,.723),(.23,.709),(.262,.683),(.290,.64),(.303,.58),(.301,.50),(.282,.41),(.260,.34),(.248,.322)]
    tire=lathe(f'BL_Tyre_{wi}_VI203_profile',profile,center,RUBBER,spin,128)
    # 32 circumferential rows with three curved, separated blocks on each half.
    # Lug polygons conform to the crown and wrap onto the shoulder, unlike box treads.
    vs=[];fs=[]
    for row in range(32):
        for s in [-1,1]:
            for band in range(3):
                z0=.008+band*.083;z1=z0+.073
                offset=.20*s*(band*.085+.044)
                base=row/32*2*pi+offset+(0 if s<0 else .018)
                poly=[(-.030,z0),(.027,z0),(.042,z1),(-.013,z1)]
                poly=rounded_poly(poly,.007,3);n=len(poly);start=len(vs)
                for layer in [0,1]:
                    for a,z in poly:
                        theta=base+a+z*.68*s
                        radius=.729-(z/.31)**4*.058+layer*.025
                        zz=s*z;vs.append((x+radius*cos(theta),.75+radius*sin(theta),zc+zz))
                fs.extend([tuple(start+i for i in range(n-1,-1,-1)),tuple(start+n+i for i in range(n))])
                fs.extend([(start+i,start+(i+1)%n,start+(i+1)%n+n,start+i+n) for i in range(n)])
    tread=mesh(f'BL_Tyre_{wi}_curved_tread_blocks',vs,fs,RUBBER,spin,.0025)
    # Mold seams, bead protectors and radial sidewall vents.
    for s in [-1,1]:
        for r,z,thick in [(.343,.267,.005),(.38,.280,.0035),(.49,.304,.0018),(.635,.287,.0022)]:
            rod(f'BL_Tyre_{wi}_mould_ring_{s}_{r}',[(x+r*cos(i/128*2*pi),.75+r*sin(i/128*2*pi),zc+s*z) for i in range(128)],thick,RUBBER,spin,True)
        for k in range(40):
            a=k/40*2*pi
            rod(f'BL_Tyre_{wi}_vent_{s}_{k}',[(x+.56*cos(a),.75+.56*sin(a),zc+s*.307),(x+.62*cos(a+.004),.75+.62*sin(a+.004),zc+s*.295)],.0018,RUBBER,spin)
    # Recessed steel wheel: lathed cross-section, detachable bead ring and dish.
    rim_profile=[(-.25,.319),(-.256,.342),(-.235,.357),(-.215,.336),(-.17,.315),(.13,.315),(.22,.334),(.249,.355),(.267,.357),(.279,.346),(.265,.33),(.235,.317),(.217,.297),(.18,.27),(.11,.23),(.11,.16),(.13,.12)]
    rim_profile=[(z*side,r) for z,r in rim_profile]
    lathe(f'BL_Rim_{wi}_pressed_dish',rim_profile,center,PAINT,spin,96)
    lathe(f'BL_Rim_{wi}_bead_lock',[(side*.252,.35),(side*.273,.36),(side*.289,.359),(side*.295,.346),(side*.279,.335)],center,PAINT_DARK,spin,96)
    cylinder(f'BL_Hub_{wi}_planetary_case',.193,.18,(x,.75,zc+side*.18),PAINT_DARK,spin,'z',64,.014)
    cylinder(f'BL_Hub_{wi}_cover',.184,.035,(x,.75,zc+side*.287),PAINT,spin,'z',64,.008)
    cylinder(f'BL_Hub_{wi}_oil_plug',.025,.017,(x,.75,zc+side*.317),METAL,spin,'z',6,.003)
    for count,r,z,rad in [(12,.26,.197,.022),(16,.343,.292,.012),(8,.152,.313,.011)]:
        for k in range(count):
            a=k/count*2*pi;xx=x+r*cos(a);yy=.75+r*sin(a)
            cylinder(f'BL_Wheel_{wi}_washer_{r}_{k}',rad*1.35,.009,(xx,yy,zc+side*(z-.008)),METAL,spin,'z',24,.002)
            cylinder(f'BL_Wheel_{wi}_nut_{r}_{k}',rad,.019,(xx,yy,zc+side*z),METAL,spin,'z',6,.002)
    rod(f'BL_Wheel_{wi}_inflation_line',[(x+.025,.77,zc+side*.33),(x+.15,.91,zc+side*.329),(x+.252,.905,zc+side*.238)],.006,METAL,spin)
    # Raised tire size characters around the sidewall, native font-to-mesh conversion later.
    legend='1500x600-635  VI-203'
    for ci,ch in enumerate(legend):
        if ch==' ':continue
        a=.40+ci*.050
        curve=bpy.data.curves.new(f'Tyre_marking_{wi}_{ci}','FONT');curve.body=ch;curve.size=.040;curve.extrude=.0006;curve.bevel_depth=.0002;curve.align_x='CENTER';curve.align_y='CENTER'
        obj=bpy.data.objects.new(f'BL_Tyre_{wi}_emboss_{ci}',curve);bpy.context.collection.objects.link(obj);curve.materials.append(RUBBER)
        obj.location=C((x+.525*cos(a),.75+.525*sin(a),zc+side*.307))
        # Text local X tangent, local Y radial, normal towards outer sidewall.
        tx=C((-sin(a),cos(a),0));ty=C((cos(a),sin(a),0));normal=tx.cross(ty)
        if side<0:tx=-tx;normal=tx.cross(ty)
        obj.rotation_euler=Matrix((tx,ty,normal)).transposed().to_euler();parent_keep(obj,spin)
    tire['tyre_spec']='VI-203 product sheet: OD 1500 mm / width 610 mm / rim 635 mm / tread 25 mm'
print('BLENDER_WHEELS_READY',flush=True)

# Save references in the native project as non-rendering image empties.
refs=bpy.data.collections.new('00_REFERENCE_PHOTOGRAPHS');bpy.context.scene.collection.children.link(refs)
for i,filename in enumerate(['factory-543a-profile.jpg','museum-front.jpg','museum-front-oblique.jpg','maz543a-5.jpg','maz543-1.gif']):
    path=Path('D:/maz543-references')/filename
    if not path.exists() or path.suffix=='.gif':continue
    obj=bpy.data.objects.new('REFERENCE_'+filename,None);refs.objects.link(obj);obj.empty_display_type='IMAGE';obj.data=bpy.data.images.load(str(path));obj.empty_display_size=6;obj.location=(0,8+i*.02,3);obj.rotation_euler=(pi/2,0,0);obj.hide_render=True;obj.hide_viewport=True
text=bpy.data.texts.new('READ_ME__MODEL_SCOPE');text.write('MAZ-543A reference reconstruction. Exterior authored in Blender from multiple photographs. Mechanical interior is simplified, imported from a parameterized kinematic rig and retained as editable meshes. Nominal reference measurements are not factory tolerances. VI-203 tire geometry references BELSHINA: OD1500, width610, bead635mm. Images remain reference-only. Blender model contains editable topology and modifiers. No full multibody, fluid, thermal, tire contact, or stress solution is claimed.')

# Convert curve details, keep moving assemblies and meaningful sub-meshes separate.
for obj in list(bpy.data.objects):
    if obj.name.startswith('BL_'):
        obj['provenance']='Authored in Blender with photographic reference'
        anc=obj.parent
        while anc:
            if anc.name in ['cab_pivot_001','cab_pivot_005','cab_pivot_002','cab_pivot_003','cab_pivot_006','cab_pivot_007','body']:
                obj['surface']='exterior';break
            anc=anc.parent

scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
scene.render.engine='CYCLES';scene.cycles.samples=48;scene.cycles.use_denoising=True
try:
    prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices()
    for device in prefs.devices:device.use=device.type!='CPU'
    scene.cycles.device='GPU'
except Exception as err:print('Cycles device fallback:',err,flush=True)
scene.render.resolution_x=1600;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.film_transparent=False
scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast';scene.view_settings.exposure=0
world=bpy.data.worlds.new('Neutral industrial studio');scene.world=world;world.use_nodes=True
world.node_tree.nodes['Background'].inputs['Color'].default_value=(.20,.23,.25,1);world.node_tree.nodes['Background'].inputs['Strength'].default_value=.35
floor_mat=material('Concrete_studio',(.13,.145,.14),0,.92,.16)
floor=box('STUDIO_FLOOR',[100,.08,100],[0,-.04,0],floor_mat,None,0)
studio=bpy.data.collections.new('99_RENDER_STUDIO');scene.collection.children.link(studio)
for col in list(floor.users_collection):col.objects.unlink(floor)
studio.objects.link(floor)
def area(name,location,power,size,color,target=(0,1,0)):
    data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='DISK';data.size=size;data.color=color
    ob=bpy.data.objects.new(name,data);studio.objects.link(ob);ob.location=C(location);ob.rotation_euler=(C(target)-ob.location).to_track_quat('-Z','Y').to_euler();return ob
area('Large overhead softbox',(-4,8,3),1400,7,(1,.96,.88))
area('Cool rim softbox',(3,6,-5),2100,6,(.82,.88,1))
area('Front fill',(-9,3,-2),480,5,(1,.98,.94))
area('Side fill',(2,4,7),800,7,(.91,.94,1))
camera_data=bpy.data.cameras.new('Reference inspection camera');camera=bpy.data.objects.new('CAMERA_BEAUTY',camera_data);studio.objects.link(camera)
camera.location=C((-11.7,6.8,12));target=C((-.3,1.25,0));camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler();camera_data.lens=48;camera_data.clip_end=300;scene.camera=camera
scene.render.filepath=str(OUT/'maz543a-blender-preview.png')
scene['variant']='MAZ-543A photographic reconstruction';scene['accuracy']='Reference model, not dimensionally certified factory CAD'
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'MAZ543A_Master.blend'))
print('BLENDER_NATIVE_SAVED',flush=True)
bpy.ops.render.render(write_still=True)
print('BLENDER_PREVIEW_RENDERED',flush=True)
