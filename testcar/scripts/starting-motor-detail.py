"""MN-1 stator surfaces visible in a user-identified disassembly specimen.

Executed in blender-starting.py's metric mesh namespace. Four pole shoes and
their two recesses are visible in that specimen, not a proved 1977 production
specification. Dimensions, hidden cores and lead routes are reconstruction fits.
No invented armature slot/brush/commutator or copper winding turn counts.
"""
import numpy as np

CLOTH=mat('MN1_field_coil_woven_insulation',(.022,.024,.023),0,.9)
POLE=mat('MN1_pole_lamination_stack',(.17,.18,.165),.82,.48)
INSULATOR=mat('MN1_phenolic_terminal_support',(.055,.025,.012),0,.62)

# Native and browser use the same repeatable, physical-scale weave normal map.
# These are synthetic material maps, not alterations of the evidence photos.
size=512;yy,xx=np.mgrid[0:size,0:size]/size
u=xx*48;v=yy*48;parity=(np.floor(u)+np.floor(v))%2
h=(np.cos(2*pi*(u%1))*(1-parity)+np.cos(2*pi*(v%1))*parity)*.000028
h+=.000004*np.sin(2*pi*u*4)*np.sin(2*pi*v*4)
dv,du=np.gradient(h,.02/size);normal=np.stack([-du,-dv,np.ones_like(h)],axis=-1)
normal/=np.linalg.norm(normal,axis=-1)[...,None]
rgba=np.ones((size,size,4),dtype=np.float32);rgba[:,:,:3]=normal*.5+.5
im=bpy.data.images.new('MN1_20mm_woven_insulation_normal',size,size);im.colorspace_settings.name='Non-Color'
im.pixels.foreach_set(rgba.ravel());im.filepath_raw=str(OUT/'MN1_insulation_normal.png');im.file_format='PNG';im.save();im.pack()
ns=CLOTH.node_tree.nodes;ls=CLOTH.node_tree.links;bs=ns.get('Principled BSDF')
tex=ns.new('ShaderNodeTexImage');tex.image=im;tex.extension='REPEAT'
nm=ns.new('ShaderNodeNormalMap');nm.inputs['Strength'].default_value=.72
ls.new(tex.outputs['Color'],nm.inputs['Color']);ls.new(nm.outputs['Normal'],bs.inputs['Normal'])

def sector(name,x0,x1,r0,r1,a0,a1,parent,material=POLE):
    n=40;vs=[]
    for x in [x0,x1]:
        for r in [r0,r1]:
            vs.extend((x,r*cos(a0+(a1-a0)*j/n),r*sin(a0+(a1-a0)*j/n)) for j in range(n+1))
    q=n+1;fs=[]
    for j in range(n):
        fs.extend([(j,j+1,q+j+1,q+j),(2*q+j,3*q+j,3*q+j+1,2*q+j+1),
                   (j,2*q+j,2*q+j+1,j+1),(q+j,q+j+1,3*q+j+1,3*q+j)])
    fs.extend([(0,q,3*q,2*q),(n,2*q+n,3*q+n,q+n)])
    return mesh(name,vs,fs,material,parent,source='MN1-DISASSEMBLY-2022')

def bundle(name,parent):
    # Rounded rectangular bundle wraps around the radial field core; the visible
    # outer object is insulation, not a solid block pretending to be copper turns.
    path=[];halfX=.048;halfZ=.014;corner=.009
    for x,z,a0 in [(halfX-corner,halfZ-corner,0),(halfX-corner,-halfZ+corner,pi/2),
                    (-halfX+corner,-halfZ+corner,pi),(-halfX+corner,halfZ-corner,3*pi/2)]:
        for j in range(17):
            a=a0+j*pi/32;px=x+corner*sin(a);pz=z+corner*cos(a)
            path.append(Vector((-.14+px,.0455*cos(pz/.0455),.0455*sin(pz/.0455))))
    # Resample straight sides too, so cross sections follow the tangent smoothly.
    path.append(path[0]);arc=[0.]
    for j in range(1,len(path)):arc.append(arc[-1]+(path[j]-path[j-1]).length)
    sampled=[];segment=0
    for j in range(192):
        s=arc[-1]*j/192
        while arc[segment+1]<s:segment+=1
        p=path[segment].lerp(path[segment+1],(s-arc[segment])/(arc[segment+1]-arc[segment]))
        radial=sqrt(p.y*p.y+p.z*p.z);p.y*=.0455/radial;p.z*=.0455/radial;sampled.append(p)
    path=sampled
    # A circular cross-section normal and local tangent preserve the curved bore.
    vs=[];fs=[];distance=[0.]
    for j in range(1,len(path)):distance.append(distance[-1]+(path[j]-path[j-1]).length)
    total=distance[-1]+(path[0]-path[-1]).length;cross=16
    for i,p in enumerate(path):
        tangent=(path[(i+1)%len(path)]-path[(i-1)%len(path)]).normalized()
        radial=Vector((0,p.y,p.z)).normalized();side=radial.cross(tangent).normalized()
        for j in range(cross):
            a=TAU*j/cross;lap=((distance[i]/.010-j/cross+.5)%1)-.5
            ridge=.00012*math.exp(-(lap/.08)**2)
            vs.append(tuple(p+radial*((.0034+ridge)*cos(a))+side*((.0036+ridge)*sin(a))))
    for i in range(len(path)):
        for j in range(cross):fs.append((i*cross+j,((i+1)%len(path))*cross+j,((i+1)%len(path))*cross+(j+1)%cross,i*cross+(j+1)%cross))
    ob=mesh(name,vs,fs,CLOTH,parent,smooth=True,source='MN1-DISASSEMBLY-2022')
    uv=ob.data.uv_layers.active
    for f in ob.data.polygons:
        first=f.vertices[0]//cross
        for li in f.loop_indices:
            index=ob.data.loops[li].vertex_index;i=index//cross;j=index%cross
            along=total if first==len(path)-1 and i==0 else distance[i]
            around=cross if f.vertices[0]%cross==cross-1 and j==0 else j
            uv.data[li].uv=(along/.02,around/cross*(TAU*.0035)/.02)
    ob['visibleSurface']='cloth insulation only; conductor turns underneath not reconstructed'
    return ob

TAU=2*pi
for i in range(4):
    pole=empty('MN1_field_pole_'+str(i+1),pump,rx=i*pi/2+pi/4)
    pole['sourceId']='MN1-DISASSEMBLY-2022';pole['dimensionStatus']='unmeasured specimen and installation fit'
    core=sector('MN1_field_core_fit_'+str(i+1),-.181,-.099,.0393,.0495,-.16,.16,pole)
    core['dimensionStatus']='hidden core continuity inferred; dimensions fitted'
    shoe=sector('MN1_curved_pole_shoe_'+str(i+1),-.188,-.092,.0362,.0398,-.59,.59,pole)
    # Two actual recessed fastener bores per visible pole, not painted dark dots.
    for x in [-.164,-.116]:
        cut=cylinder('MN1_pole_recess_tool',.0023,.016,(x,.039,0),POLE,pole,axis='y',n=32)
        bpy.context.view_layer.update();bpy.context.view_layer.objects.active=shoe
        mod=shoe.modifiers.new('Radial pole fastening recess','BOOLEAN');mod.object=cut;mod.operation='DIFFERENCE';bpy.ops.object.modifier_apply(modifier=mod.name)
        bpy.data.objects.remove(cut,do_unlink=True)
        cylinder('MN1_recessed_pole_fastener_'+str((i,x)),.0018,.001,(x,.0392,0),STEEL,pole,'y',n=32,source='MN1-DISASSEMBLY-2022')
    bevel=shoe.modifiers.new('Pole edge easing','BEVEL');bevel.width=.00035;bevel.segments=2
    bevel=shoe.modifiers.new('Pole weighted normals','WEIGHTED_NORMAL');bevel.keep_sharp=True
    bundle('MN1_insulated_field_bundle_'+str(i+1),pole)
    # Exiting field leads/eyelets are shown by the dismantled stator photograph.
    # Exact in-service routing and circuit pairing are not established by it.
    pipe('MN1_field_lead_'+str(i+1),[(-.190,.044,.012),(-.205,.046,.013),(-.219,.043,.008),(-.231,.041,.006)],.0018,CLOTH,pole,source='MN1-DISASSEMBLY-2022')
    ring('MN1_field_eyelet_'+str(i+1),.0042,.0021,.0011,(-.237,.041,.006),COPPER,pole,'z',n=32,source='MN1-DISASSEMBLY-2022')
    box('MN1_field_crimp_'+str(i+1),(.007,.003,.002),(-.231,.041,.006),COPPER,pole,.0006,source='MN1-DISASSEMBLY-2022')

# An insulating end support is visible in the specimen; its exact contour is fit.
ring('MN1_terminal_phenolic_ring',.049,.0368,.0025,(-.205,0,0),INSULATOR,pump,n=64,source='MN1-DISASSEMBLY-2022')
