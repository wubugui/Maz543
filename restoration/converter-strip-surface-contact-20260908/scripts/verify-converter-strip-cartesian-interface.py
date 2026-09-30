"""Check rotational covariance and stationary friction hold in Cartesian coordinates."""
from pathlib import Path
import json,math
import numpy as np
from converter_strip_spring import rest_curve
from converter_strip_surface_contact import SurfaceContactStrip
from converter_strip_cartesian_dynamics import CartesianStripFreewheel
ROOT=Path(__file__).resolve().parents[1]
props=json.loads((ROOT/'outputs/converter-strip-inertia.json').read_text())
seed=json.loads((ROOT/'outputs/converter-strip-surface-resumed-dynamics.json').read_text())['rows'][-1]
def system():return CartesianStripFreewheel(SurfaceContactStrip(rest_curve(64,24)),props['roller']['massKg'],props['roller']['axialInertiaKgM2'],props['outerInertiaKgM2'],minimum_beta=-.115)
results=[]
for rotation in [0.,.47,-1.23]:
    solver=system();q=np.asarray(seed['q']).copy();q[[1,3]]+=rotation;solver.spring_state=seed['strip']
    force,strip=solver.spring(q);old={**seed,'q':q,'v':np.asarray(seed['v']),'springGeneralized':force,'strip':strip}
    s=solver.step(old,10.,.00001);s['q'][[1,3]]-=rotation
    results.append(s)
checks=[]
for rotation,s in zip([.47,-1.23],results[1:]):
    r={'rotationRad':rotation,'poseDifference':float(np.max(np.abs(s['q']-results[0]['q']))),
       'speedDifference':float(np.max(np.abs(s['v']-results[0]['v']))),
       'energyDifferenceJ':abs(s['kinetic']+s['springEnergy']-results[0]['kinetic']-results[0]['springEnergy'])}
    assert r['poseDifference']<1e-10 and r['speedDifference']<1e-6 and r['energyDifferenceJ']<1e-7,r
    checks.append(r)
solver=system();s=solver.initial()
for i in range(10):s=solver.step(s,2.,.00025)
hold=float(np.max(np.abs(s['v'])));assert hold<1e-7
report={'rotationChecks':checks,'stationaryHoldMaximumSpeed':hold,'limits':'Interface invariants only. Large-step numerical dissipation and full trajectory accuracy remain unaccepted.'}
(ROOT/'outputs/converter-strip-cartesian-interface.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print(json.dumps(report,indent=2))
