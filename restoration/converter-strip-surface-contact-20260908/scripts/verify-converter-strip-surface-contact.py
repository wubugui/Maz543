"""Independent closest-surface derivatives and multi-contact virtual work."""
from pathlib import Path
import json,math,numpy as np
from converter_strip_spring import rest_curve
from converter_strip_surface_contact import SurfaceContactStrip
from converter_strip_mount import mounted_equilibrium,cross
ROOT=Path(__file__).resolve().parents[1];source=json.loads((ROOT/'work/freewheel-contact/strip-surface-domain.json').read_text());beam=SurfaceContactStrip(rest_curve(64,24))
row=next(r for r in source['rows'] if r['radialClearanceFraction']==0 and r['betaRad']==-.11);angles=np.array(row['solution']['angles']);centre=np.array(row['centreM']);derivatives=[]
body=next(c for c in row['solution']['rollerContacts'] if c['kind']=='face');key=('face',body['node'],body['side']);fraction=beam.face_fraction(angles,centre,key);assert .001<fraction<.999
for key in [('vertex',17,1),('vertex',0,-1),('vertex',88,1),key,('face',0,1)]:
    g,J,H,_,_=beam.circle_constraint(angles,centre,.00625,key)
    for k in sorted(set([0,16,17,18,87])):
        step=1e-6;d=np.zeros(88);d[k]=step
        before=beam.circle_constraint(angles-d,centre,.00625,key);after=beam.circle_constraint(angles+d,centre,.00625,key)
        ge=abs((after[0]-before[0])/(2*step)-J[k]);he=float(np.max(np.abs((after[1]-before[1])/(2*step)-H[:,k])))
        assert ge<2e-11 and he<2e-10,(key,k,ge,he)
        derivatives.append({'kind':key[0],'node':key[1],'side':key[2],'director':k,'gradientErrorM':float(ge),'hessianErrorM':he})
checks=[];balances=[]
continued=json.loads((ROOT/'work/freewheel-contact/strip-surface-continuation.json').read_text())
selected=source['rows']+[b['accepted'][-1] for b in continued['branches'] if b['accepted']]
for row in [r for r in selected if r['tipModelValid'] and any(c['kind']=='face' for c in r['solution']['rollerContacts'])]:
    angle=.47;origin=np.array([.013,-.008]);R=np.array([[math.cos(angle),-math.sin(angle)],[math.sin(angle),math.cos(angle)]])
    centre=origin+R@row['centreM'];initial=row['solution'];s=mounted_equilibrium(beam,centre,angle,origin,initial=initial)
    force=np.array(s['forceOnRollerWorldN']);mount=np.array(s['forceOnMountWorldN'])
    torque_error=abs(cross(centre-origin,force)+s['torqueOnMountAboutOriginNm']);root_error=abs(s['coupleOnMountAtRootNm']-s['rootBendingCoupleNm'])
    spin_torque=sum(cross(np.array(c['pointM'])-np.array(row['centreM']),np.array(c['forceOnRollerN'])) for c in s['rollerContacts'])
    assert np.linalg.norm(force+mount)<1e-10 and torque_error<1e-10 and root_error<1e-8 and abs(spin_torque)<1e-10,(row['betaRad'],root_error,spin_torque)
    balances.append({'beta':row['betaRad'],'fraction':row['radialClearanceFraction'],'contacts':len(s['rollerContacts']),
      'rootCoupleErrorNm':root_error,'netMomentErrorNm':torque_error,'frictionlessRollerSpinTorqueNm':spin_torque})
    for dof in range(5):
        step=1e-7 if dof<4 else 1e-6;energies=[]
        for sign in [-1,1]:
            cp=centre.copy();op=origin.copy();ap=angle
            if dof<2:cp[dof]+=sign*step
            elif dof<4:op[dof-2]+=sign*step
            else:ap+=sign*step
            energies.append(mounted_equilibrium(beam,cp,ap,op,initial=initial)['energyJ'])
        measured=-(energies[1]-energies[0])/(2*step);expected=(force.tolist()+mount.tolist()+[s['torqueOnMountAboutOriginNm']])[dof];error=abs(measured-expected)
        assert error<(2e-3 if dof<4 else 2e-5),(row['betaRad'],dof,error)
        checks.append({'beta':row['betaRad'],'fraction':row['radialClearanceFraction'],'coordinate':dof,'energyDerivativeLoad':measured,'reportedLoad':expected,'error':error})
report={'slidingFaceFraction':fraction,'derivatives':derivatives,'bodyBalances':balances,'virtualWork':checks,
 'limits':'Fitted full ribbon surface contact, including eliminated sliding-point coordinate. No factory seating, material, strength or full dynamic trajectory acceptance.'}
(ROOT/'outputs/converter-strip-surface-verification.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print(json.dumps({'slidingFaceFraction':fraction,'derivativeChecks':len(derivatives),'bodyBalances':balances,'virtualWorkChecks':len(checks),
 'maxForceDifferenceN':max(r['error'] for r in checks if r['coordinate']<4),'maxTorqueDifferenceNm':max(r['error'] for r in checks if r['coordinate']==4)},indent=2),flush=True)
