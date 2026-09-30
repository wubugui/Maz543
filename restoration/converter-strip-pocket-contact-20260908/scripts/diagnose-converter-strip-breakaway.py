"""Static contact-cone load boundary, independent of time integration."""
from pathlib import Path
import json,math,numpy as np
from converter_strip_spring import rest_curve
from converter_strip_pocket import PocketStripSpring
from converter_strip_dynamics import StripFreewheel
ROOT=Path(__file__).resolve().parents[1];p=json.loads((ROOT/'outputs/converter-strip-inertia.json').read_text())
system=StripFreewheel(PocketStripSpring(rest_curve(64,24)),p['roller']['massKg'],p['roller']['axialInertiaKgM2'],p['outerInertiaKgM2'])
state=system.initial();R=state['q'][0];r=system.r;c=math.cos(system.alpha);s=-math.sin(system.alpha)
J=np.array([[1,0,0,0],[-c,R*s,0,-R*s],[0,R,-r,0],[s,R*c,r,-(R*c+r)]])
base=np.linalg.solve(J.T,-state['springGeneralized']);slope=np.linalg.solve(J.T,-np.array([0,0,0,1.]))
lower=-math.inf;upper=math.inf;bounds=[]
for contact in range(2):
    for label,v in [('normal',np.eye(4)[contact]),('positive-friction',system.mu*np.eye(4)[contact]+np.eye(4)[contact+2]),('negative-friction',system.mu*np.eye(4)[contact]-np.eye(4)[contact+2])]:
        a=float(v@slope);b=float(v@base)
        if a>1e-12:lower=max(lower,-b/a)
        elif a< -1e-12:upper=min(upper,-b/a)
        bounds.append({'contact':contact,'constraint':label,'coefficient':a,'constant':b,'boundaryNm':-b/a if abs(a)>1e-12 else None})
assert lower<2<upper<6
report={'staticTorqueIntervalNm':[lower if math.isfinite(lower) else None,upper if math.isfinite(upper) else None],
 'bounds':bounds,'initialForceN':state['strip']['forceN'],
 'limits':'Fitted initial geometry, spring and friction. Null lower means unbounded negative torque only in this rigid Coulomb abstraction, not actual strength. A 6 Nm follow-up is an external test load above the computed 4.50 Nm breakaway, not a factory reactor torque or a tuned spring.'}
(ROOT/'outputs/converter-strip-static-torque-domain.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps(report,indent=2))
