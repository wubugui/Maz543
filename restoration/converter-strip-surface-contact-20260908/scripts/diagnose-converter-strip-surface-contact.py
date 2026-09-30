"""Target the first deeper-compression failures with full ribbon/roller contact."""
from pathlib import Path
import json,math,numpy as np
from converter_strip_spring import rest_curve
from converter_strip_surface_contact import SurfaceContactStrip
ROOT=Path(__file__).resolve().parents[1];beam=SurfaceContactStrip(rest_curve(64,24));old=json.loads((ROOT/'work/freewheel-contact/strip-deep-domain.json').read_text());rows=[]
rho=.06225;alpha=math.radians(7)
for fraction,betas in [(0.,[-.1,-.105,-.11,-.115]),(.5,[-.08,-.085,-.09,-.095]),(1.,[-.1,-.105,-.11,-.115])]:
    seed=min((r for r in old['rows'] if r['radialClearanceFraction']==fraction and r['tipModelValid']),key=lambda r:abs(r['betaRad']-betas[0]))
    initial=seed['solution']
    for beta in betas:
        rmax=rho*math.cos(alpha)/math.cos(beta-alpha);R=rho+fraction*(rmax-rho);centre=R*np.array([math.cos(beta),math.sin(beta)])
        row={'radialClearanceFraction':fraction,'betaRad':beta,'centreM':centre.tolist()}
        try:
            result=beam.solve(centre,initial=initial);initial=result;row['solution']=result
            row['tipModelValid']=bool(result['minimumRollerSurfaceGapM']>=-1e-10 and result['minimumWedgePlaneGapM']>=-1e-10 and result['minimumConstrainedStiffnessNm']>0)
        except Exception as error:row.update({'tipModelValid':False,'failure':str(error)})
        rows.append(row)
        print(json.dumps({'fraction':fraction,'beta':beta,'valid':row['tipModelValid'],'failure':row.get('failure'),
          'contacts':[{k:c[k] for k in ['kind','node','side','forceN']} for c in row.get('solution',{}).get('rollerContacts',[])],
          'gapM':row.get('solution',{}).get('minimumRollerSurfaceGapM')},ensure_ascii=False),flush=True)
report={'fit':old['fit'],'rows':rows,'limits':'Targeted fitted strip contact candidates. Native self/race/body collision and derivative/load verification remain separate; no continuous-domain expansion or factory strength claim.'}
(ROOT/'work/freewheel-contact/strip-surface-domain.json').write_text(json.dumps(report,indent=2),encoding='utf8')
