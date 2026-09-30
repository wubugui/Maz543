"""Original MAZ tooth counts; reconstructed 3 mm module and 20 degree form."""
exec(compile((__import__('pathlib').Path(__file__).resolve().parent/'prepare-cam-profiles.py').read_text().split('module=2*S')[0],__file__,'exec'))
from shapely.geometry import Point
counts=[20,23,36];module=.003
raw={n:Polygon(spur(n,module)) for n in counts};cuts={n:[] for n in counts}
pairs=[(23,36),(36,20),(23,23)]
for n,N in pairs:
 for aN,bN in [(n,N),(N,n)]:
  A,B=raw[aN],raw[bN];distance=(aN+bN)*module/2
  root=Point(0,0).buffer(aN*module/2*cos(pi/9),quad_segs=256)
  for j in range(361):
   a=j/360*2*pi/aN;b=pi-pi/bN-a*aN/bN
   mate=rotate(translate(rotate(B,b,origin=(0,0),use_radians=True),xoff=distance),-a,origin=(0,0),use_radians=True)
   hit=A.intersection(mate).intersection(root)
   if not hit.is_empty:cuts[aN].append(hit)
profiles={}
for n in counts:
 p=raw[n]
 if cuts[n]:
  cut=unary_union(cuts[n]);cut=unary_union([rotate(cut,k*2*pi/n,origin=(0,0),use_radians=True) for k in range(n)])
  p=p.difference(cut.buffer(.000008)).simplify(.000001,preserve_topology=True)
 assert p.geom_type=='Polygon' and p.is_valid
 profiles[n]=p
checks=[]
for n,N in pairs:
 worst=0
 for j in range(721):
  a=j/720*2*pi/n;b=pi-pi/N-a*n/N
  A=rotate(profiles[n],a,origin=(0,0),use_radians=True)
  B=translate(rotate(profiles[N],b,origin=(0,0),use_radians=True),xoff=(n+N)*module/2)
  worst=max(worst,A.intersection(B).area)
 assert worst<1e-13,(n,N,worst)
 checks.append({'teeth':[n,N],'samples':721,'overlap':worst})
sections={}
for name,n,bore in [('lower23',23,.010),('oil36',36,.010),('oil20',20,.009),('fuel23',23,.008)]:
 hole=[(bore*cos(j*2*pi/96),bore*sin(j*2*pi/96)) for j in range(96)]
 sections[name]=section(list(profiles[n].exterior.coords)[:-1],hole)
(ROOT/'work/timing-spurs.json').write_text(json.dumps({'sections':sections,'checks':checks,'module':module}))
print('TIMING_SPURS_OK',checks,flush=True)
