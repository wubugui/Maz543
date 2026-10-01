"""Independent VA180 front-form study from inspected photographs, not metrology."""
import bpy,math,json,hashlib,argparse,sys,shutil
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=ROOT/'outputs/cloud-va180-face-study-20261001')
args=p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []);OUT=args.output.resolve();OUT.mkdir(parents=True,exist_ok=True);assert not (OUT/'study.blend').exists()
reference=json.loads((ROOT/'reference/va180-face-source-20261001.json').read_text())
bpy.ops.wm.read_factory_settings(use_empty=True);sc=bpy.context.scene;sc.unit_settings.system='METRIC';sc.unit_settings.length_unit='MILLIMETERS'
sc['status']='INDEPENDENT PARTIAL PHOTO-FORM STUDY; FITTED DIMENSIONS; ALL16 OPEN'
sc['source_pixels_loaded']=False;sc['electrical_simulation']=False
def collection(name):
 c=bpy.data.collections.new(name);sc.collection.children.link(c);return c
PARTS=collection('01 PHYSICAL FRONT STUDY');INK=collection('02 READABLE MARKS — incomplete calibration');CUT=collection('90 NATIVE BOOLEAN TOOLS — hidden');SRC=collection('91 EDITABLE CONTOURS — hidden');REVIEW=collection('99 REVIEW CAMERA LIGHTS')
solids=[];marks=[];sources=[]
def put(o,c):
 for x in list(o.users_collection):x.objects.unlink(o)
 c.objects.link(o);return o
def tag(o,role,c=PARTS,solid=True):
 put(o,c);o['role']=role;o['dimension_status']='FITTED, not manufacturer dimensions';o['installed_in_vehicle']=False
 if solid:solids.append(o.name)
 return o
def material(name,color,metal=0,rough=.4,trans=0):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True;n=m.node_tree.nodes['Principled BSDF'];n.inputs['Base Color'].default_value=(*color,1);n.inputs['Metallic'].default_value=metal;n.inputs['Roughness'].default_value=rough;n.inputs['Transmission Weight'].default_value=trans;m['status']='FITTED photograph appearance, no material metrology';return m
GRAY=material('FITTED gray-green casing',(.17,.20,.17),.45,.42);DARK=material('FITTED dark display',(.006,.01,.008),0,.58);METAL=material('FITTED correction metal',(.09,.105,.09),.7,.3);IVORY=material('Observed light marks, fitted pigment',(.75,.82,.59),0,.55);YELLOW=material('Observed button instruction, fitted pigment',(.78,.62,.04),0,.6);GLASS=material('FITTED clear flat window',(.92,.98,.95),0,.06,1)
def bevel(o,w=.00025):
 m=o.modifiers.new('Native edge bevel','BEVEL');m.width=w;m.segments=3
def cylinder(name,r,depth,loc,mat,c=PARTS,solid=True,edge=.0002):
 bpy.ops.mesh.primitive_cylinder_add(vertices=96,radius=r,depth=depth,location=loc);o=bpy.context.object;o.name=name;tag(o,name,c,solid);o.data.materials.append(mat)
 for face in o.data.polygons:face.use_smooth=abs(face.normal.z)<.9
 o['side_shading']='Smooth cylindrical side faces; flat end caps; no coordinate/topology change'
 if edge:bevel(o,edge)
 return o
def cube(name,size,loc,mat,c=PARTS,solid=True,edge=.00008):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.dimensions=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);tag(o,name,c,solid);o.data.materials.append(mat)
 if edge:bevel(o,edge)
 return o
def hidden(o):o.hide_render=True;o.hide_set(True)
def difference(o,cutter,name):
 m=o.modifiers.new(name,'BOOLEAN');m.operation='DIFFERENCE';m.solver='EXACT';m.object=cutter;hidden(cutter);return m
def contour(name,coords,depth,z,mat,c=PARTS,solid=True,keep=True):
 # Native 2D Bézier authoring and conversion, never manual mesh construction.
 area=sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(coords,coords[1:]+coords[:1]))
 if area<0:coords=list(reversed(coords))
 cu=bpy.data.curves.new(name+' source','CURVE');cu.dimensions='2D';cu.fill_mode='BOTH';cu.resolution_u=16;s=cu.splines.new('BEZIER');s.bezier_points.add(len(coords)-1)
 for p,(x,y) in zip(s.bezier_points,coords):p.co=(x,y,0);p.handle_left_type='AUTO';p.handle_right_type='AUTO'
 s.use_cyclic_u=True;o=bpy.data.objects.new(name,cu);c.objects.link(o);o.location.z=z
 if keep:
  src=o.copy();src.data=cu.copy();src.name=name+' EDITABLE SOURCE';SRC.objects.link(src);hidden(src);src['status']='FITTED contour from oblique photograph';sources.append(src.name)
 bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.convert(target='MESH');o=bpy.context.object;tag(o,name,c,solid);o.data.materials.append(mat)
 m=o.modifiers.new('Native sheet thickness','SOLIDIFY');m.thickness=depth;m.offset=0
 return o
window=[(-.037,.005),(-.035,.021),(-.025,.033),(-.01,.039),(.008,.039),(.026,.032),(.036,.017),(.037,.001),(.029,-.008),(.017,-.002),(0,.001),(-.016,-.002),(-.03,-.009)]
body=cylinder('CASE — fitted hollow cylindrical envelope',.042,.047,(0,0,-.025),GRAY,edge=0)
inner=cylinder('CASE bore tool',.040,.048,(0,0,-.023),DARK,CUT,False,0);difference(body,inner,'Native case cavity — no invented internals');bevel(body)
front=cylinder('FRONT — opaque lower mask and upper opening',.044,.003,(0,0,0),GRAY,edge=0)
wc=contour('WINDOW through-cut tool',window,.014,0,DARK,CUT,False);difference(front,wc,'Native real display opening')
button_xy=(.0104,-.033);screw_xy=(-.004,-.025)
bc=cylinder('BUTTON aperture tool',.00465,.018,(*button_xy,0),DARK,CUT,False,0);difference(front,bc,'Native button aperture')
zc=cylinder('ZERO screw aperture tool',.00185,.018,(*screw_xy,0),DARK,CUT,False,0);difference(front,zc,'Native correction-screw aperture');bevel(front,.00022)
glass=contour('GLASS — separate fitted flat cover',[(x*.985,y*.985) for x,y in window],.0007,.0022,GLASS);bevel(glass,.00008)
dial=contour('DIAL — backing beneath real window',[(x*1.015,y*1.015) for x,y in window],.0006,-.0032,DARK);dial['role']='Visible dial backing study surface only; hidden internal plate geometry unknown'
fit=cylinder('DIAL radial fit tool',.0396,.014,(0,0,-.0032),DARK,CUT,False,0);m=difference(dial,fit,'Native fitted backing/case radial clearance');m.operation='INTERSECT';bevel(dial,.00008);dial['clearance_status']='0.4mm radial gap to fitted40mm case bore, not factory metrology'
screw=cylinder('ZERO CORRECTOR — slotted front head',.003,.0014,(*screw_xy,.0024),METAL,edge=0)
slot=cube('ZERO slot cutter',(.004,.00065,.002),(*screw_xy,.003),DARK,CUT,False,0);slot.rotation_euler.z=.3;difference(screw,slot,'Native screwdriver slot');bevel(screw,.0001)
cylinder('ZERO CORRECTOR — retained separate shank',.0016,.010,(*screw_xy,-.003),METAL)
bush=cylinder('BUTTON — stationary hollow sleeve',.0045,.006,(*button_xy,.0015),METAL,edge=0)
bore=cylinder('BUTTON sleeve bore tool',.0023,.018,(*button_xy,.002),DARK,CUT,False,0);difference(bush,bore,'Native button stem bore');bevel(bush,.00012)
button=bpy.data.objects.new('BUTTON PRESS REVIEW — travel is fitted',None);PARTS.objects.link(button);button['press_mm']=0.0;button['travel_status']='0 to1mm review only, not factory stroke';button['source_function']='pressed: voltage; released: current, per1977 manual';button['electrical_simulation']=False
stem=cylinder('BUTTON — movable stem',.002,.014,(*button_xy,.001),METAL)
cap=cylinder('BUTTON — movable cap',.0034,.004,(*button_xy,.009),GRAY)
for o in [stem,cap]:o.parent=button
drv=button.driver_add('location',2).driver;v=drv.variables.new();v.name='p';v.type='SINGLE_PROP';v.targets[0].id=button;v.targets[0].data_path='["press_mm"]';drv.expression='-p/1000.0'
pointer=cube('POINTER — fitted photo pose, not a measured value',(.00065,.038,.00025),(-.0045,.011,-.0021),IVORY,edge=.00006);pointer.rotation_euler.z=.235
# Pivot hardware is obscured in the source; do not invent it in this front-only study.
font_path=Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf');font=bpy.data.fonts.load(str(font_path));font.pack();assert font.packed_file
license_text=Path('/usr/share/doc/fonts-dejavu-core/copyright').read_text();bpy.data.texts.new('PACKED FONT LICENSE — DejaVu').write(license_text);(OUT/'FONT-LICENSE.txt').write_text(license_text)
def text(name,body,loc,size,mat):
 cu=bpy.data.curves.new(name,'FONT');cu.body=body;cu.font=font;cu.size=size;cu.align_x='CENTER';cu.align_y='CENTER';cu.extrude=.00002;cu.resolution_u=8;o=bpy.data.objects.new(name,cu);INK.objects.link(o);o.location=loc;o.data.materials.append(mat);o['evidence']='Readable photographic characters; positions/font FITTED; incomplete scale';marks.append({'object':name,'text':body,'location':list(loc)});return o
for i,(label,x,y) in enumerate([('60',-.028,.009),('0',-.012,.024),('60',.005,.021),('120',.019,.015),('180',.029,.006)]):text('OBSERVED A scale label '+str(i),label,(x,y,-.00275),.0051,IVORY)
text('OBSERVED current unit','A',(.001,.010,-.00275),.0048,IVORY)
text('OBSERVED push instruction','Нажать',(.013,-.023,.0017),.0032,YELLOW)
# Minor ticks and upper voltage marks are deliberately unresolved, not guessed.
bpy.context.view_layer.update();button['press_mm']=1.0;button.update_tag();bpy.context.view_layer.update();pressed=[list(stem.matrix_world.translation),list(cap.matrix_world.translation)];button['press_mm']=0.0;button.update_tag();bpy.context.view_layer.update();assert abs(pressed[1][2]-(cap.matrix_world.translation.z-.001))<1e-7
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'study.blend'))
report={'status':'INDEPENDENT_PARTIAL_PHOTO_FORM_STUDY','model_sha256':hashlib.sha256((OUT/'study.blend').read_bytes()).hexdigest(),'reference_registry':'reference/va180-face-source-20261001.json','closed_solids':solids,'editable_contours':sources,'readable_marks':marks,'omitted_uncertain_marks':['all minor tick counts/positions','upper voltage numerals/ticks','unreadable signs and manufacturer details'],'button_review_travel_mm':[0,1],'button_pressed_centres':pressed,'physical_dimensions':'ALL_FITTED','packed_font':'DejaVu Sans, fitted typography; full license embedded and adjacent','source_pixels_loaded':False,'factory_match':'UNVERIFIED','installed_in_vehicle':False,'limits':['Not complete VA180 marking/calibration reproduction','No coils, springs, shunt, rear connector or clamp modeled','Flat glass and casing envelope are fitted','Button review travel is not original mechanism stroke'],'all16VehicleGates':'OPEN'}
(OUT/'build.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print('VA180_FACE_STUDY_SAVED',len(solids),len(marks),flush=True)
