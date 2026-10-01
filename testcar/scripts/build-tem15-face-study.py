"""Partial 1978 TEM15 photographed face, not factory dimensions or vehicle install."""
import bpy,math,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs/cloud-tem15-face-study-20261001';OUT.mkdir(exist_ok=True)
assert not (OUT/'study.blend').exists()
ref=json.loads((ROOT/'reference/tem15-face-source-20261001.json').read_text());assert ref['old_photo']['pixels_inspected']
bpy.ops.wm.read_factory_settings(use_empty=True);sc=bpy.context.scene;sc.unit_settings.system='METRIC';sc['status']='PARTIAL PHOTO FORM; ALL DIMENSIONS/ANGLE FITTED; ALL16 OPEN';sc['source_image_pixels_loaded']=False
solids=[];marks=[]
def mat(name,c,metal=0,rough=.4,trans=0):
 m=bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=(*c,1);n=m.node_tree.nodes['Principled BSDF'];n.inputs['Base Color'].default_value=(*c,1);n.inputs['Metallic'].default_value=metal;n.inputs['Roughness'].default_value=rough;n.inputs['Transmission Weight'].default_value=trans;return m
black=mat('FITTED black painted rim',(.012,.014,.014),.15,.4);dialmat=mat('FITTED matte black dial',(.006,.007,.008),0,.7);white=mat('Observed ivory face marks, fitted pigment',(.78,.79,.69),0,.6);glassmat=mat('FITTED flat clear glass',(.98,.99,1),0,.025,1)
def cyl(name,r,d,z,material,edge=0,physical=True):
 bpy.ops.mesh.primitive_cylinder_add(vertices=128,radius=r,depth=d,location=(0,0,z));o=bpy.context.object;o.name=name;o.data.materials.append(material);o['dimension_status']='ALL_FITTED';o['installed_in_vehicle']=False
 for f in o.data.polygons:f.use_smooth=abs(f.normal.z)<.9
 if edge:m=o.modifiers.new('Native bevel','BEVEL');m.width=edge;m.segments=3
 if physical:solids.append(name)
 return o
case=cyl('CASE FRONT ENVELOPE — no rear hardware or internals',.044,.022,-.009,black)
cut=cyl('HIDDEN native case cavity tool',.0403,.024,-.006,black,physical=False);cut.hide_render=True;cut.hide_set(True)
b=case.modifiers.new('Native Boolean open front cavity','BOOLEAN');b.operation='DIFFERENCE';b.solver='EXACT';b.object=cut
b=case.modifiers.new('Native rim bevel','BEVEL');b.width=.00035;b.segments=3
cyl('GLASS — separate fitted flat disc',.04005,.0007,.0002,glassmat,.00008)
cyl('DIAL — fitted front backing only',.0399,.0006,-.003,dialmat,.00008)
# Needle uses an editable native 2D curve with VECTOR handles, never manual mesh data.
cu=bpy.data.curves.new('POINTER editable outline','CURVE');cu.dimensions='2D';cu.fill_mode='BOTH';cu.extrude=.0001
s=cu.splines.new('BEZIER');s.bezier_points.add(2)
for p,xy in zip(s.bezier_points,[(-.001,-.008),(.001,-.006),(-.031,.008)]):p.co=(*xy,0);p.handle_left_type='VECTOR';p.handle_right_type='VECTOR'
s.use_cyclic_u=True;o=bpy.data.objects.new('POINTER — fitted uncalibrated photo pose',cu);sc.collection.objects.link(o);o.location.z=-.00165;o.data.materials.append(white);o['dimension_status']='FITTED';solids.append(o.name)
font=bpy.data.fonts.load('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf');font.pack();license=Path('/usr/share/doc/fonts-dejavu-core/copyright').read_text();bpy.data.texts.new('FONT LICENSE').write(license);(OUT/'FONT-LICENSE.txt').write_text(license)
def text(name,body,x,y,size):
 c=bpy.data.curves.new(name,'FONT');c.body=body;c.font=font;c.size=size;c.align_x='CENTER';c.align_y='CENTER';c.extrude=.000015;c.resolution_u=8;o=bpy.data.objects.new(name,c);sc.collection.objects.link(o);o.location=(x,y,-.00262);o.data.materials.append(white);o['placement_status']='FITTED from oblique photo; not calibrated';marks.append({'object':name,'text':body})
angles=[165,115,65,15]
for label,deg in zip(['0','5','10','15'],angles):
 a=math.radians(deg);text('OBSERVED scale '+label,label,.027*math.cos(a),.027*math.sin(a),.0062)
 bpy.ops.mesh.primitive_cube_add(size=1,location=(.034*math.cos(a),.034*math.sin(a),-.00258));o=bpy.context.object;o.name='OBSERVED major mark '+label;o.dimensions=(.0012,.004,.00012);o.rotation_euler.z=a-math.pi/2;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(white);o['status']='Observed major mark, fitted angle; minor marks omitted';solids.append(o.name)
text('OBSERVED unit numerator','КГ',0,-.014,.006);text('OBSERVED unit denominator','СМ²',0,-.020,.006)
bpy.ops.mesh.primitive_cube_add(size=1,location=(0,-.017,-.00258));o=bpy.context.object;o.name='OBSERVED unit separator';o.dimensions=(.012,.0005,.0001);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(white);solids.append(o.name)
sc['variant_note']='Old kg/cm² face from photograph with1978 passport. Separate MPa×0.1 photo not mixed.'
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'study.blend'),compress=True)
r={'status':'INDEPENDENT_PARTIAL_TEM15_FACE_STUDY','model_sha256':hashlib.sha256((OUT/'study.blend').read_bytes()).hexdigest(),'physical_solids':solids,'solid_count_note':'Includes5 painted-mark solids; not an original manufacturer component count','observed_text':marks,'reference_registry':'reference/tem15-face-source-20261001.json','source_images_packed':False,'fitted_face_radius_m':.044,'major_mark_angles_deg':angles,'limits':['1978 product specimen is not proof of target1977 installation batch','All dimensions, depth, glass section, font and label angles fitted','Minor ticks omitted because exact positions/count not resolved from oblique image','No sensor, hose, rear connector, clamp or internal mechanism modeled','No electrical response or calibrated pressure-to-angle function','Not installed, no original-hole claim'],'whole_vehicle_acceptance':'16 OPEN'};(OUT/'build.json').write_text(json.dumps(r,indent=2,ensure_ascii=False)+'\n');print('TEM15_PARTIAL_FACE_BUILT',len(solids),len(marks),flush=True)
