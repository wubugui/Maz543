"""MAZ 1973 fig. 7–9 cam assemblies; runs in the engine's metric mesh namespace.
Counts/topology are documented. Sizes, tooth geometry and oil-port clocking are
reconstruction parameters. The bevel input train is not yet accepted.
"""
from mathutils import Matrix
CAM_PROFILES=json.loads((ROOT/'work/cam-profiles.json').read_text())

def cam_tag(ob,part,source='MAZ-1973-F9',role='internal'):
    ob['d12Part']=part;ob['sourceId']=source;ob['d12Role']=role;ob['camTrain']=True
    ob['camBank']=CAM_BANK
    ob['dimensionStatus']='MAZ topology/counts; dimensions and hole clocking reconstructed'
    return ob

def cam_section(name,data,x0,x1,parent,material=POLISH,outer_angle=0):
    points=data['vertices'];n=len(points);out=data['outer'];vs=[];fs=[]
    for x in [x0,x1]:
        for j,(y,z) in enumerate(points):
            a=outer_angle if j<out else 0
            vs.append((x,y*cos(a)-z*sin(a),y*sin(a)+z*cos(a)))
    for f in data['faces']:fs.extend([tuple(reversed(f)),tuple(i+n for i in f)])
    for lo,hi in [(0,out),(out,n)]:
        for j in range(lo,hi):k=lo+(j-lo+1)%(hi-lo);fs.append((j,k,k+n,j+n))
    ob=mesh(name,vs,fs,material,parent,source='MAZ-1973-F9')
    return cam_tag(ob,name)

def drill(ob,name,r,length,pos,parent,axis='x',angle=None):
    tool=cylinder(name,r,length,pos,POLISH,parent,axis,n=20,source='MAZ-1973-F9')
    if angle is not None:
        # radial drill starts as a +Y cylinder, rotated about the cam axis.
        tool.rotation_euler.x=angle
    bpy.context.view_layer.update();bpy.context.view_layer.objects.active=ob
    mod=ob.modifiers.new(name,'BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=tool
    bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(tool,do_unlink=True)

def cam_ring(name,r,bore,width,x,parent,material=POLISH):
    return cam_tag(ring(name,r,bore,width,(x,0,0),material,parent,n=64,source='MAZ-1973-F9'),name)

def circlip(name,x,r,parent):
    pts=[(x,r*cos(.22+j/96*(2*pi-.44)),r*sin(.22+j/96*(2*pi-.44))) for j in range(97)]
    return cam_tag(pipe(name,pts,.00065,STEEL,parent,source='MAZ-1973-F9'),name)

def bevel24(name,parent):
    # Tredgold back-cone involute approximation; standard geometry, not the
    # original cutter/profile. Count 24 is MAZ fig. 7; 3 mm module is fitted.
    n=24;module=.003;delta=math.atan2(24,12);rp=n*module/2;rv=rp/cos(delta)
    rb=rv*cos(pi/9);inv=math.tan(pi/9)-pi/9;rr=rv-1.25*module;ra=rv+module
    outer=[]
    for k in range(n):
        samples=[(-1,rr,-pi/n)]
        for sign,indices in [(-1,range(13)),(1,range(12,-1,-1))]:
            for j in indices:
                r=max(rr,rb)+(ra-max(rr,rb))*j/12;t=math.acos(min(1,rb/r))
                a=sign*(pi*cos(delta)/(2*n)-.000055/rv+inv-(math.tan(t)-t))/cos(delta)
                samples.append((sign,r,a))
        for _,r,a in samples:
            q=k*2*pi/n+a;rad=rp+(r-rv)*cos(delta);x=rp/math.tan(delta)-(r-rv)*sin(delta)
            outer.append((x,rad*cos(q),rad*sin(q),q))
    vs=[];fs=[];count=len(outer);apex=-.665
    for f in [.72,1.]:
        for x,y,z,a in outer:vs.append((apex+x*f,y*f,z*f))
        for x,y,z,a in outer:vs.append((apex+rp/math.tan(delta)*f,.0212*cos(a),.0212*sin(a)))
    for j in range(count):
        k=(j+1)%count
        fs.extend([(j,k,count+k,count+j),(2*count+j,3*count+j,3*count+k,2*count+k),
                   (j,2*count+j,2*count+k,k),(count+j,count+k,3*count+k,3*count+j)])
    ob=mesh(name,vs,fs,POLISH,parent,source='MAZ-1973-F7')
    ob['toothCount']=24;ob['toothGeometry']='Tredgold approximation; unmeasured module/pressure angle; mating bevel train pending'
    return cam_tag(ob,'intake compound gear / bevel portion','MAZ-1973-F7')

def cap_pair(bank,s,head,index):
    # Fig. 9 shows one paired pedestal and one removable cap with two bores.
    x=-.54+index*.18;y=SPEC['camY'];z=SPEC['valveOffset'];width=.022
    for label,upper in [('pedestal',False),('cap',True)]:
        if upper:
            poly=[(y,-.064),(y,.064),(y+.009,.064),(y+.014,.055),(y+.026,.052),(y+.030,.042),(y+.030,.022),(y+.019,0),(y+.030,-.022),(y+.030,-.042),(y+.026,-.052),(y+.014,-.055),(y+.009,-.064)]
        else:poly=[(y-.048,-.064),(y-.048,.064),(y-.025,.064),(y-.018,.052),(y,.052),(y,-.052),(y-.018,-.052),(y-.025,-.064)]
        ob=prism(f'D12_cam_{label}_{bank}_{index+1}',poly,x-width/2,x+width/2,CAST,head,edge=0,source='MAZ-1973-F9')
        for cz in [-z,z]:drill(ob,'Journal bearing bore',.02115,.04,(x,y,cz),head)
        for cz in [-.056,.056]:drill(ob,'Through stud bore',.00315,.12,(x,y-.01,cz),head,'y')
        bevel=ob.modifiers.new('Cast edge radii','BEVEL');bevel.width=.0007;bevel.segments=2
        cam_tag(ob,'paired cam bearing '+label)
    for cz in [-.056,.056]:
        ob=cylinder(f'D12_cam_bearing_stud_{bank}_{index}_{cz}',.0029,.065,(x,y-.009,cz),STEEL,head,'y',24,source='MAZ-1973-F9');cam_tag(ob,'cam bearing stud')
        ob=ring(f'D12_cam_bearing_washer_{bank}_{index}_{cz}',.006,.0031,.0015,(x,y+.011,cz),POLISH,head,'y',32,source='MAZ-1973-F9');cam_tag(ob,'bearing washer')
        ob=cylinder(f'D12_cam_bearing_nut_{bank}_{index}_{cz}',.0052,.005,(x,y+.014,cz),STEEL,head,'y',6,source='MAZ-1973-F9');cam_tag(ob,'bearing nut')

def build_cam_bank(bank,s,head):
    global CAM_BANK
    CAM_BANK=bank
    for kind in ['intake','exhaust']:
        sign=1 if kind=='intake' else -1
        p=POSES['frames'][0]['pose'][f'D12_cam_{bank}_{kind}']['p']
        cam=empty(f'D12_cam_{bank}_{kind}',root,p);cam['camTrain']=True
        # Continuous through-bore. Journals/lobes have matching open axial bores.
        shaft=cam_ring(f'D12_camshaft_{bank}_{kind}',.016,.008,1.2,0,cam)
        for i in range(6):
            x=(i-2.5)*SPEC['pitch']
            op=SPEC['intakeOpenDeg'] if sign==1 else SPEC['exhaustOpenDeg']
            cl=SPEC['intakeCloseDeg'] if sign==1 else SPEC['exhaustCloseDeg']
            center=(op+cl)*pi/360+POSES['firePhases'][f'{bank}{i+1}'];half=(cl-op)*pi/720
            for j in range(2):
                vx=x+(-1 if j==0 else 1)*SPEC['valveOffset'];poly=[]
                for k in range(384):
                    a=k/384*2*pi;delta=(sign*(s*BETA+pi-a)-center/2+pi)%(2*pi)-pi;u=delta/half
                    lift=SPEC['valveLift']*(1-u*u)**2 if abs(u)<1 else 0
                    deriv=sign*4*SPEC['valveLift']*u*(1-u*u)/half if abs(u)<1 else 0;r=SPEC['camBaseRadius']+lift
                    poly.append((r*cos(a)-deriv*sin(a),r*sin(a)+deriv*cos(a)))
                ob=prism(f'D12_cam_lobe_{bank}{i+1}_{kind}_{j}',poly,vx-.012,vx+.012,STEEL,cam,edge=0,source='MAZ-1973-F9')
                drill(ob,'Lobe axial oil gallery',.008,.03,(vx,0,0),cam)
                # Source establishes a radial hole per lobe, ahead of contact;
                # its exact diameter and angular drilling datum are unmeasured.
                a=s*BETA+pi-sign*(center/2-half*.65)
                for target in [ob,shaft]:drill(target,'Cam radial oil feed',.0012,.043,(vx,.020,0),cam,'y',a)
                bevel=ob.modifiers.new('Lobe edge easing','BEVEL');bevel.width=.00018;bevel.segments=2
                cam_tag(ob,'cam lobe with radial oil bore')
        for i in range(7):
            x=-.54+i*.18
            ob=cam_ring(f'D12_cam_journal_{bank}_{kind}_{i}',.021,.008,.024,x,cam)
            for target in [ob,shaft]:drill(target,'Journal radial oil feed',.0012,.028,(x,.013,0),cam,'y',s*BETA)
        # The ten rectangular shaft splines mate with the adjustable sleeve;
        # its 41 triangular exterior splines engage the gear bore.
        cam_section(f'D12_cam_10_spline_{bank}_{kind}',CAM_PROFILES['sections']['shaftSpline'],-.674,-.6,cam)
        cam_ring(f'D12_cam_thrust_shoulder_{bank}_{kind}',.022,.008,.007,-.604,cam)
        cam_ring(f'D12_cam_adjustment_shim_{bank}_{kind}',.0215,.0157,.0008,-.610,cam)
        sleeve=cam_section(f'D12_cam_41_10_sleeve_{bank}_{kind}',CAM_PROFILES['sections']['sleeve'],-.657,-.615,cam)
        sleeve['externalSplines']=41;sleeve['internalSplines']=10
        for a in [0,pi]:drill(sleeve,'Sleeve spring release hole',.0017,.056,(-.650,0,0),cam,'y',a)
        # Choose tooth-to-space assembly phases for the actual 64 mm separation.
        z=(1 if kind=='intake' else -1)*(-s)*SPEC['valveOffset']
        other=POSES['frames'][0]['pose'][f'D12_cam_{bank}_{"exhaust" if kind=="intake" else "intake"}']['p']
        phi=math.atan2(other[2]-p[2],other[1]-p[1]);phase=phi if kind=='intake' else phi-pi/22
        gear=cam_section(f'D12_cam_22_spur_{bank}_{kind}',CAM_PROFILES['sections'][f'spur_{bank}_{kind}'],-.636,-.622,cam)
        gear['toothCount']=22;gear['sourceId']='MAZ-1973-F7';gear['moduleStatus']='64 mm centre distance / 22 teeth; fit, not drawing'
        if kind=='intake':
            bevel24(f'D12_cam_24_bevel_{bank}',cam)
            cam_ring(f'D12_cam_compound_hub_{bank}',.026,.0212,.016,-.641,cam)
        circlip(f'D12_cam_sleeve_lock_ring_{bank}_{kind}',-.659,.0175,cam)
        ret=cam_ring(f'D12_cam_threaded_retainer_{bank}_{kind}',.0173,.0065,.016,-.675,cam)
        ret['threadHand']='LEFT' if kind=='intake' else 'RIGHT'
        # Fine helical thread on the threaded retainers, handed as original.
        hand=-1 if kind=='intake' else 1
        pts=[(-.684+j/240*.016,.01735*cos(hand*j/240*8*2*pi),.01735*sin(hand*j/240*8*2*pi)) for j in range(241)]
        cam_tag(pipe(f'D12_cam_retainer_thread_{bank}_{kind}',pts,.00033,STEEL,cam,source='MAZ-1973-F9'),'handed retainer thread')
        for k in range(6):
            a=k*2*pi/6;drill(ret,'Retainer wrench notch',.002,.024,(-.675,.017*cos(a),.017*sin(a)),cam)
        circlip(f'D12_cam_retainer_lock_{bank}_{kind}',-.671,.0183,cam)
        plug=cylinder(f'D12_cam_rear_plug_{bank}_{kind}',.0079,.011,(.594,0,0),POLISH,cam,n=48,source='MAZ-1973-F9');cam_tag(plug,'threaded rear oil-gallery plug');plug['threadHand']='RIGHT'
        face=cylinder(f'D12_cam_rear_plug_face_{bank}_{kind}',.009,.002,(.601,0,0),POLISH,cam,n=48,source='MAZ-1973-F9');cam_tag(face,'rear plug face')
        cut=box('Rear plug screwdriver slot',(.0014,.002,.015),(.602,0,0),STEEL,cam,edge=0)
        bpy.context.view_layer.update();bpy.context.view_layer.objects.active=face
        mod=face.modifiers.new('Screwdriver slot recess','BOOLEAN');mod.operation='DIFFERENCE';mod.object=cut;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cut,do_unlink=True)
        circlip(f'D12_cam_rear_circlip_{bank}_{kind}',.6025,.010,cam)
    for i in range(7):cap_pair(bank,s,head,i)
    exec(compile((ROOT/'scripts/d12-cam-finish.py').read_text(encoding='utf-8'),str(ROOT/'scripts/d12-cam-finish.py'),'exec'))
