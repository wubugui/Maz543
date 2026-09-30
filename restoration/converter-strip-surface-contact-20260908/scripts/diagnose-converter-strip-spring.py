"""Nonlinear strip contact sweep and independent energy-gradient check."""
from pathlib import Path
import json,math,numpy as np
from converter_strip_spring import StripSpring,rest_curve
ROOT=Path(__file__).resolve().parents[1];spring=StripSpring(rest_curve(128,48));rows=[];initial=None;failures=[]
for beta in np.linspace(0,-.025,26):
    centre=.06225*np.array([math.cos(beta),math.sin(beta)])
    try:
        row=spring.solve(centre,initial=initial);initial=row['angles'];row['beta']=float(beta);row['centre']=centre.tolist();rows.append(row)
        assert row['minimumBeamCapsuleGapM']>-1e-8 and row['tipCapFacesRoller']>0 and row['minimumConstrainedStiffnessNm']>0,row
    except Exception as error:failures.append({'beta':float(beta),'error':str(error)});break
gradient=[]
for row in rows[::5]:
    c=np.array(row['centre']);eps=1e-7
    for axis in [0,1]:
        d=np.zeros(2);d[axis]=eps
        before=spring.solve(c-d,initial=row['angles']);after=spring.solve(c+d,initial=row['angles'])
        force=-(after['energyJ']-before['energyJ'])/(2*eps);error=abs(force-row['forceOnRollerN'][axis])
        gradient.append({'beta':row['beta'],'axis':axis,'forceFromEnergyN':force,'contactForceN':row['forceOnRollerN'][axis],'errorN':error})
        assert error<1e-4,(row['beta'],axis,error)
report={'fit':{'widthM':spring.width,'thicknessM':spring.thickness,'youngPa':spring.young,'rollerRadiusM':.00625,'rollerLengthM':.022,'segments':spring.n},'restPoints':spring.rest.tolist(),'rows':rows,'failures':failures,'energyGradient':gradient,
 'limits':'Source-guided curved strip, fitted free curvature and clamped seat. Tip contact only: whole-strip clearance and stable equilibrium must pass before installing. No factory stiffness, material, seating or strength acceptance.'}
(ROOT/'work/freewheel-contact/strip-spring-study.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print(json.dumps({'states':len(rows),'failures':failures,'maxEnergyForceErrorN':max(x['errorN'] for x in gradient),'minimumBeamCapsuleGapM':min(r['minimumBeamCapsuleGapM'] for r in rows),'minimumTipCapFacing':min(r['tipCapFacesRoller'] for r in rows),'forceRangeN':[min(r['forceN'] for r in rows),max(r['forceN'] for r in rows)],'maxStressPa':max(r['maximumIncrementalBendingStressPa'] for r in rows)},indent=2),flush=True)
