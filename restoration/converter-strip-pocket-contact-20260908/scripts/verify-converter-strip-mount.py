"""Independent free-body, rigid-frame and virtual-work checks of moving mount loads."""
from pathlib import Path
import json,math,numpy as np
from converter_strip_spring import StripSpring,rest_curve
from converter_strip_mount import mounted_equilibrium,cross
ROOT=Path(__file__).resolve().parents[1]
source=json.loads((ROOT/'work/freewheel-contact/strip-spring-study.json').read_text())
spring=StripSpring(rest_curve(128,48));checks=[];gradient=[]
origin=np.array([.017,-.009])
for index,row in enumerate(source['rows']):
    angle=[0.,.37,2.1][index%3];c,s=math.cos(angle),math.sin(angle);R=np.array([[c,-s],[s,c]])
    centre=origin+R@row['centre'];r=mounted_equilibrium(spring,centre,angle,origin,initial=row['angles'])
    f=np.asarray(r['forceOnRollerWorldN']);fm=np.asarray(r['forceOnMountWorldN'])
    force_error=float(np.linalg.norm(f+fm));moment_error=abs(cross(centre-origin,f)+r['torqueOnMountAboutOriginNm'])
    couple_error=abs(r['coupleOnMountAtRootNm']-r['rootBendingCoupleNm'])
    assert force_error<1e-10 and moment_error<1e-10 and couple_error<1e-9,(index,force_error,moment_error,couple_error)
    assert abs(r['energyJ']-row['energyJ'])<1e-10
    checks.append({'index':index,'angleRad':angle,'forceBalanceErrorN':force_error,'momentBalanceErrorNm':moment_error,
      'rootConstitutiveCoupleErrorNm':couple_error,'mountTorqueNm':r['torqueOnMountAboutOriginNm'],'rootCoupleNm':r['coupleOnMountAtRootNm']})
    if index%5:continue
    # Perturb independent physical coordinates while equilibrating the strip,
    # rather than differentiating the force transformation implementation.
    for dof in range(5):
        step=1e-6 if dof==4 else 1e-7;values=[]
        for sign in [-1,1]:
            cp=centre.copy();op=origin.copy();ap=angle
            if dof<2:cp[dof]+=sign*step
            elif dof<4:op[dof-2]+=sign*step
            else:ap+=sign*step
            values.append(mounted_equilibrium(spring,cp,ap,op,initial=row['angles'])['energyJ'])
        derivative_force=-(values[1]-values[0])/(2*step)
        expected=(f.tolist()+fm.tolist()+[r['torqueOnMountAboutOriginNm']])[dof]
        error=abs(derivative_force-expected);assert error<(1e-4 if dof<4 else 1e-6),(index,dof,error)
        gradient.append({'index':index,'coordinate':dof,'energyDerivativeLoad':derivative_force,'reportedLoad':expected,'absoluteError':error})
report={'equilibria':checks,'virtualWork':gradient,
  'limits':'Fitted clamped seat, massless quasi-static strip and frictionless rounded-tip contact. No actual seat geometry/material acceptance; continuous roller integrator not connected.'}
(ROOT/'outputs/converter-strip-mount-verification.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print(json.dumps({'equilibria':len(checks),'virtualWorkChecks':len(gradient),
  'maxForceBalanceErrorN':max(r['forceBalanceErrorN'] for r in checks),'maxMomentBalanceErrorNm':max(r['momentBalanceErrorNm'] for r in checks),
  'maxRootCoupleErrorNm':max(r['rootConstitutiveCoupleErrorNm'] for r in checks),
  'maxTranslationEnergyForceErrorN':max(r['absoluteError'] for r in gradient if r['coordinate']<4),
  'maxRotationEnergyTorqueErrorNm':max(r['absoluteError'] for r in gradient if r['coordinate']==4)},indent=2),flush=True)
