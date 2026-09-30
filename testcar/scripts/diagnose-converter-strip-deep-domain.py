"""Inspect deeper compression before expanding the continuous solver's domain."""
from pathlib import Path
import json,math,numpy as np
from converter_strip_spring import rest_curve
from converter_strip_pocket import PocketStripSpring
ROOT=Path(__file__).resolve().parents[1];beam=PocketStripSpring(rest_curve(64,24));ri=.056;r=.00625;rho=ri+r;alpha=math.radians(7)
checkpoint=json.loads((ROOT/'work/freewheel-contact/strip-domain-exit-checkpoint.json').read_text());rows=[]
cases=[('rejected-dynamic-candidate',1.,checkpoint['exit']['beta'],np.array(checkpoint['exit']['localCentreM']))]
for fraction in [0.,.5,1.]:
    for beta in np.linspace(-.06,-.16,21):
        rmax=rho*math.cos(alpha)/math.cos(beta-alpha);R=rho+fraction*(rmax-rho)
        cases.append(('geometric-envelope',fraction,float(beta),R*np.array([math.cos(beta),math.sin(beta)])))
initial=None;previous_family=None
for label,fraction,beta,centre in cases:
    if previous_family!=(label,fraction):initial=None
    previous_family=(label,fraction)
    row={'kind':label,'radialClearanceFraction':fraction,'betaRad':beta,'centreM':centre.tolist(),
      'innerRollerGapM':float(np.linalg.norm(centre)-rho),'outerRollerGapM':float(rho*math.cos(alpha)-np.dot(centre,beam.plane_normal)),
      'rootCentrelineRollerGapM':float(np.linalg.norm(centre-beam.rest[0])-r)}
    if row['rootCentrelineRollerGapM']<0:
        row.update({'tipModelValid':False,'failure':'Fixed root centreline is inside the roller; this fitted seating cannot occupy the candidate geometry'});rows.append(row);continue
    try:
        result=beam.solve(centre,initial=initial);initial=result['angles'];row['solution']=result
        reasons=[]
        if result['minimumBeamCapsuleGapM']<-1e-8:reasons.append('roller intersects a non-tip part of the strip')
        if result['forceN']>0 and result['tipCapFacesRoller']<=0:reasons.append('contact leaves the outward-facing tip cap')
        if result['minimumConstrainedStiffnessNm']<=0:reasons.append('unstable constrained equilibrium')
        if result['minimumWedgePlaneGapM']<-1e-10:reasons.append('strip violates the wedge plane')
        row.update({'tipModelValid':not reasons,'invalidReasons':reasons})
    except Exception as error:row.update({'tipModelValid':False,'failure':str(error)})
    rows.append(row)
report={'fit':{'widthM':beam.width,'thicknessM':beam.thickness,'youngPa':beam.young,'rollerRadiusM':r,'segments':beam.n},
 'rows':rows,'limits':'Diagnostic candidates only, not an expanded operating domain. Fitted clamped seating and linear elastic constitutive law remain unaccepted. Native pocket, root and non-tip roller contact must be assessed.'}
(ROOT/'work/freewheel-contact/strip-deep-domain.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print(json.dumps({'points':len(rows),'solved':sum('solution' in x for x in rows),'tipModelValid':sum(x['tipModelValid'] for x in rows),
 'summary':[{'kind':x['kind'],'fraction':x['radialClearanceFraction'],'beta':x['betaRad'],'valid':x['tipModelValid'],
   'failure':x.get('failure',x.get('invalidReasons')),'bodyGapM':x.get('solution',{}).get('minimumBeamCapsuleGapM'),
   'wedgeContacts':len(x.get('solution',{}).get('wedgeContacts',[]))} for x in rows]},indent=2),flush=True)
