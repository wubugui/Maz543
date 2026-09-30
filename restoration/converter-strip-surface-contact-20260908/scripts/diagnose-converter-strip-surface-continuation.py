"""Track difficult static loading branches with explicit accepted increments."""
from pathlib import Path
import json,math,numpy as np
from converter_strip_spring import rest_curve
from converter_strip_surface_contact import SurfaceContactStrip
ROOT=Path(__file__).resolve().parents[1];beam=SurfaceContactStrip(rest_curve(64,24));source=json.loads((ROOT/'work/freewheel-contact/strip-surface-domain.json').read_text());rho=.06225;alpha=math.radians(7)
reports=[]
for fraction,start_beta,end_beta in [(0.,-.11,-.115),(.5,-.085,-.09),(1.,-.11,-.115)]:
    seed=next(r for r in source['rows'] if r['radialClearanceFraction']==fraction and r['betaRad']==start_beta and r['tipModelValid']);state=seed['solution'];rows=[];failure=None
    for beta in np.linspace(start_beta,end_beta,11)[1:]:
        rmax=rho*math.cos(alpha)/math.cos(beta-alpha);R=rho+fraction*(rmax-rho);centre=R*np.array([math.cos(beta),math.sin(beta)])
        try:
            state=beam.solve(centre,initial=state)
            if state['minimumConstrainedStiffnessNm']<=0:raise RuntimeError('Unstable static branch')
            rows.append({'betaRad':float(beta),'centreM':centre.tolist(),'solution':state,'tipModelValid':True,'radialClearanceFraction':fraction})
        except Exception as error:failure={'betaRad':float(beta),'error':str(error)};break
    reports.append({'fraction':fraction,'startBeta':start_beta,'targetBeta':end_beta,'accepted':rows,'failure':failure})
    print(json.dumps({'fraction':fraction,'acceptedSteps':len(rows),'failure':failure,'lastContacts':[{k:c[k] for k in ['kind','node','forceN']} for c in state.get('rollerContacts',[])]}),flush=True)
report={'fit':source['fit'],'branches':reports,'limits':'Explicit static load increments, not a time trajectory. Failed targets remain incomplete; no operating-domain extension.'}
(ROOT/'work/freewheel-contact/strip-surface-continuation.json').write_text(json.dumps(report,indent=2),encoding='utf8')
