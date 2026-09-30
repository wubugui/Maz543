"""Fitted large-clutch pusher/guide reconstruction, run inside the builder.
Catalogue establishes two pushers, two bushings and a retaining pin per spring.
The telescoping fit and casting bosses below are functional reconstruction;
they are not factory dimensions or a verified manufacturing arrangement.
"""
from mathutils import Quaternion
from clutch_spring_hardware_geometry import retaining_pin_points

templates={}
def keep(key,ob):
    bm=bmesh.new();bm.from_mesh(ob.data)
    bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-8)
    bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=1e-12)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    assert all(e.is_manifold for e in bm.edges),ob.name
    bm.to_mesh(ob.data);bm.free();templates[key]=ob;return ob

rod=keep('rod',lathe('TX_spring_template_rod',[(-.0125,0),(-.0125,.0028),(-.0112,.0028),(-.0112,.0012),(.037,.0012),(.037,0)],(0,0,0),STEEL,None,n=48))
# Actual transverse pin hole, made once in the shared rod master.
bore_tx(rod,drill_cutter(.008,.00035,(.0353,0,0),axis='y'))
keep('rod',rod)
keep('sleeve',ring('TX_spring_template_sleeve',.002,.0013,.036,(.007,0,0),STEEL,None,n=48))
keep('bush',ring('TX_spring_template_bush',.0031,.0021,.003,(0,0,0),STEEL,None,n=48))
keep('moving_seat',ring('TX_spring_template_moving_seat',.005,.002,.0015,(.0016,0,0),STEEL,None,n=48))
keep('fixed_seat',ring('TX_spring_template_fixed_seat',.005,.0021,.0015,(.0224,0,0),STEEL,None,n=48))
boss=[(-.004,.0031),(-.004,.00605),(.035,.00605),(.035,.0013),(.0335,.0013),(.0335,.0021),(.02615,.0021),(.02615,.0031),(.02315,.0031),(.02315,.00505),(-.0007,.00505),(-.0007,.0031)]
boss_ob=keep('boss',lathe('TX_spring_template_boss',boss,(0,0,0),FORGED,None,n=64,closed=True))
# The radial piston tab needs an actual opening in the inboard boss wall.
bore_tx(boss_ob,box('TX_rotary_bore_cutter',(.0087,.0036,.003),(.00425,-.0055,0),STEEL,None,edge=0))
keep('boss',boss_ob)
anchor=keep('anchor',box('TX_spring_template_anchor',(.002,.019,.003),(.024,.0095,0),FORGED,None,edge=0))
axial_hole(anchor,.0225,.0255,.0032,0)
keep('anchor',anchor)
# A through-pin with a short bent stop at one end. Its fitted wire section is
# kept clear of the rod hole; the stop sits outside the hole opening.
pin=pipe('TX_spring_template_pin',retaining_pin_points(),.00025,STEEL,None)
pin.data.use_fill_caps=True
bpy.ops.object.select_all(action='DESELECT');pin.select_set(True);bpy.context.view_layer.objects.active=pin;bpy.ops.object.convert(target='MESH')
keep('pin',pin)

def instance(key,name,parent,part=None,position=(0,0,0)):
    template=templates[key];ob=template.copy();ob.data=template.data;ob.name=name;bpy.context.collection.objects.link(ob);ob.parent=parent;ob.location=C(position)
    tag(ob,name);ob['springHardware']=key
    ob['dimensionStatus']='Catalogue component count; fitted telescoping profiles, boss and clearances, not factory manufacturing geometry.'
    if part:ob['cataloguePart']=part
    return ob

for name in ['first','reverse']:
    pack=DATA['clutches'][name];direction=pack['direction'];x=pack['start']-direction*.005;r=pack['springMountRadius']
    for j in range(pack['springCount']):
        a=j*2*pi/pack['springCount'];position=(x,r*cos(a),r*sin(a))
        # Permit bounded template revisions in the temporary saved assembly.
        for kind in ['fixed','moving']:
            previous=bpy.data.objects.get(f'TX_{name}_spring_hardware_{kind}_{j}')
            if previous:
                for child in list(previous.children_recursive):remove_tx(child.name)
                remove_tx(previous.name)
        fixed=empty(f'TX_{name}_spring_hardware_fixed_{j}',root,position)
        moving=empty(f'TX_{name}_spring_hardware_moving_{j}',bpy.data.objects['TX_piston_'+name],position)
        rotation=Quaternion((1,0,0),a) @ Quaternion((0,0,1),pi if direction<0 else 0)
        for mount in [fixed,moving]:mount.rotation_mode='QUATERNION';mount.rotation_quaternion=rotation
        for suffix in ['spring_guide','moving_spring_seat','fixed_spring_seat','anchor']:remove_tx(f'TX_{name}_{suffix}_{j}')
        instance('rod',f'TX_{name}_spring_guide_{j}',fixed,'535A-1511244-01')
        instance('sleeve',f'TX_{name}_pusher_sleeve_{j}',moving,'535A-1511248-10')
        instance('moving_seat',f'TX_{name}_moving_spring_seat_{j}',moving)
        instance('fixed_seat',f'TX_{name}_fixed_spring_seat_{j}',fixed)
        instance('boss',f'TX_{name}_spring_guide_boss_{j}',fixed)
        instance('anchor',f'TX_{name}_anchor_{j}',fixed)
        for k,u in enumerate([-.0022,.02465]):instance('bush',f'TX_{name}_pusher_bush_{j}_{k}',fixed,'535A-1511252',(u,0,0))
        instance('pin',f'TX_{name}_pusher_pin_{j}',fixed,'535A-1511254')
for ob in templates.values():remove_tx(ob.name)
