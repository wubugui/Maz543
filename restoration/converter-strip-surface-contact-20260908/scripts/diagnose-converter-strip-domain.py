"""Probe the fitted strip across the roller's geometric pocket clearance.
This is a domain audit, not a material-strength or factory-part acceptance.
"""
from pathlib import Path
import json,math,numpy as np
from converter_strip_spring import StripSpring,rest_curve
ROOT=Path(__file__).resolve().parents[1];beam=StripSpring(rest_curve(128,48))
ri=.056;r=.00625;rho=ri+r;alpha=math.radians(7);rows=[]
for fraction in [0.,.5,1.]:
    initial=None
    for beta in np.linspace(0,-.06,13):
        rmax=rho*math.cos(alpha)/math.cos(beta-alpha);R=rho+fraction*(rmax-rho)
        centre=R*np.array([math.cos(beta),math.sin(beta)])
        entry={'radialClearanceFraction':fraction,'betaRad':float(beta),'centreM':centre.tolist(),
          'innerRollerGapM':float(R-rho),'outerRollerGapM':float(rho*math.cos(alpha)-R*math.cos(beta-alpha))}
        try:
            result=beam.solve(centre,initial=initial);initial=result['angles']
            entry['solution']=result;entry['tipModelValid']=bool(result['minimumBeamCapsuleGapM']>=-1e-8 and
              (result['forceN']==0 or result['tipCapFacesRoller']>0) and result['minimumConstrainedStiffnessNm']>0)
        except Exception as error:entry.update({'tipModelValid':False,'failure':str(error)})
        rows.append(entry)
report={'fit':{'widthM':beam.width,'thicknessM':beam.thickness,'youngPa':beam.young,'rollerRadiusM':r},'rows':rows,
  'limits':'Fitted pocket/free curve/clamped seat. Wider geometric envelope is not an operating specification. Native race collision audit is separate; material and strength remain unknown.'}
(ROOT/'work/freewheel-contact/strip-domain.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print(json.dumps({'points':len(rows),'solved':sum('solution' in r for r in rows),'tipModelValid':sum(r['tipModelValid'] for r in rows),
  'invalid':[{'beta':r['betaRad'],'radial':r['radialClearanceFraction'],'failure':r.get('failure'),
    'clearance':r.get('solution',{}).get('minimumBeamCapsuleGapM'),'capFacing':r.get('solution',{}).get('tipCapFacesRoller')} for r in rows if not r['tipModelValid']]},indent=2),flush=True)
