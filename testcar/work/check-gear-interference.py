import sys,math,json
sys.path.insert(0,'work/pythonlibs')
from shapely.geometry import Polygon
from shapely.ops import unary_union
from shapely.affinity import rotate,translate
from math import pi,cos,sin
D=json.load(open('work/starting-poses.json'));S=D['spec'];phi=math.atan2(S['starterPosition'][2],S['starterPosition'][1]-.07)
def gear(n,m,thin=0):
 rp=m*n/2;rb=rp*cos(math.radians(20));ra=rp+m;rr=rp-1.25*m;iv=math.tan(math.radians(20))-math.radians(20);p=[]
 for k in range(n):
  a=k*2*pi/n;half=pi/(2*n)-thin/rp;p.append((rr*cos(a-pi/n),rr*sin(a-pi/n)))
  for sign,rs in [(-1,[max(rr,rb),rb+(ra-rb)*.25,rb+(ra-rb)*.5,rb+(ra-rb)*.75,ra]),(1,[ra,rb+(ra-rb)*.75,rb+(ra-rb)*.5,rb+(ra-rb)*.25,max(rr,rb)])]:
   for r in rs:
    t=math.acos(min(1,rb/r));iv2=math.tan(t)-t;ang=a+sign*(half+iv-iv2);p.append((r*cos(ang),r*sin(ang)))
  p.append((rr*cos(a+pi/n),rr*sin(a+pi/n)))
 return Polygon(p).buffer(0)
for thin in [0,.000025,.00005,.0001,.00015]:
 pin=gear(11,S['module'],thin);ring=gear(132,S['module'],thin);areas=[]
 for f in D['frames']:
  if not f.get('mesh'):continue
  p=f['pose'];r=rotate(ring,p['C5_FLYWHEEL_RING']['rx'],origin=(0,0),use_radians=True);q=translate(rotate(pin,p['C5_pinion']['rx'],origin=(0,0),use_radians=True),yoff=S['starterPosition'][2],xoff=S['starterPosition'][1]-.07);inter=r.intersection(q);areas.append(inter.area)
 print('thin',thin,'max area mm2',max(areas)*1e6,'interfering frames',sum(a>1e-15 for a in areas))
