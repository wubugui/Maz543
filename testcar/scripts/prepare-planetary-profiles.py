"""Run with workspace Python 3.12; Blender 3.11 reads the resulting mesh data."""
from pathlib import Path
import json,math
from planetary_geometry import outline,annulus_data,circle
from shapely.affinity import rotate,translate
ROOT=Path(__file__).resolve().parents[1]
D=json.loads((ROOT/'work/transmission/poses.json').read_text());S=D['spec'];profiles={};polys={}
for key,bore,internal in [('sun41',.027,False),('sun21',.032,False),('long43',.013,False),('short20',.013,False),('ring40',0,True),('ring18',0,True)]:
    p=outline(S[key],S['module'],internal);polys[key]=p
    outer,inner=(circle(S['module']*S[key]/2+.010,256),p) if internal else (p,circle(bore))
    pts,caps,n=annulus_data(outer,inner)
    profiles[key]={'points':pts,'caps':caps,'outerCount':n}
worst=0.;checks=0
for pose in D['meshSamples']:
    world={key:rotate(polys[key],pose['TX_'+key]['rx'],origin=(0,0),use_radians=True) for key in ['sun41','sun21','ring40','ring18']}
    for j in range(3):
        for key,r,phi in [('long43',S['longRadius'],j*2*math.pi/3),('short20',S['shortRadius'],j*2*math.pi/3+S['planetOffset'])]:
            p=rotate(polys[key],pose[f'TX_{key}_{j}']['rx'],origin=(0,0),use_radians=True)
            world[key]=translate(p,xoff=r*math.cos(phi),yoff=r*math.sin(phi))
        for a,b,internal in [('sun41','long43',False),('sun21','short20',False),('long43','short20',False),('ring40','long43',True),('ring18','short20',True)]:
            area=world[b].difference(world[a]).area if internal else world[a].intersection(world[b]).area
            worst=max(worst,area);checks+=1
report={'samples':len(D['meshSamples']),'pairChecks':checks,'maximumIntersectionMM2':worst*1e6,'toleranceMM2':1e-6,'limits':'Planar involute material overlap only; no assembly, hydraulic, load or factory-dimensional acceptance.'}
(ROOT/'outputs/planetary-gear-clearance.json').write_text(json.dumps(report,indent=2));print(report,flush=True)
assert worst<1e-12, 'gear surface interference'
(ROOT/'work/transmission/profiles.json').write_text(json.dumps(profiles))
