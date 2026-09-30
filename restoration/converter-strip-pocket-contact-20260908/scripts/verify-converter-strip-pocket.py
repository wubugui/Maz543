"""Independent ribbon support derivatives, stored energy and distributed seat loads."""
from pathlib import Path
import math,json,numpy as np
from converter_strip_spring import rest_curve
from converter_strip_pocket import PocketStripSpring
from converter_strip_mount import mounted_equilibrium,cross
ROOT=Path(__file__).resolve().parents[1];beam=PocketStripSpring(rest_curve(128,48))
source=json.loads((ROOT/'work/freewheel-contact/strip-pocket-domain.json').read_text());contact=source['rows'][-1]
angles=np.array(contact['solution']['angles']);derivatives=[]
for index in [0,1,48,143,176]:
    g,j,H=beam.plane_constraint(angles,index)
    assert abs(g-beam.plane_gaps(angles)[index])<1e-14
    for k in sorted(set([0,max(0,index-1),min(175,index),175])):
        step=1e-6;d=np.zeros(beam.n);d[k]=step
        before=beam.plane_constraint(angles-d,index);after=beam.plane_constraint(angles+d,index)
        grad_error=abs((after[0]-before[0])/(2*step)-j[k]);hess_error=float(np.max(np.abs((after[1]-before[1])/(2*step)-H[:,k])))
        assert grad_error<2e-11 and hess_error<2e-11,(index,k,grad_error,hess_error)
        derivatives.append({'node':index,'director':k,'gradientErrorM':float(grad_error),'hessianErrorM':hess_error})
virtual=[];balances=[]
for index in [12,25,38]:
    row=source['rows'][index];a=.63;o=np.array([.017,-.009]);R=np.array([[math.cos(a),-math.sin(a)],[math.sin(a),math.cos(a)]])
    centre=o+R@row['centreM'];initial=row['solution']['angles'];result=mounted_equilibrium(beam,centre,a,o,initial=initial)
    f=np.array(result['forceOnRollerWorldN']);fm=np.array(result['forceOnMountWorldN'])
    force_error=float(np.linalg.norm(f+fm));moment_error=abs(cross(centre-o,f)+result['torqueOnMountAboutOriginNm'])
    couple_error=abs(result['rootBendingCoupleNm']-result['coupleOnMountAtRootNm'])
    assert force_error<1e-10 and moment_error<1e-10 and couple_error<1e-8,(index,couple_error)
    balances.append({'index':index,'wedgeContacts':len(result['wedgeContacts']),'forceBalanceErrorN':force_error,
      'momentBalanceErrorNm':moment_error,'rootCoupleErrorNm':couple_error,'wedgeLoadsWorld':result['wedgeLoadsWorld']})
    for dof in range(5):
        step=1e-7 if dof<4 else 1e-6;values=[]
        for sign in [-1,1]:
            cp=centre.copy();op=o.copy();ap=a
            if dof<2:cp[dof]+=sign*step
            elif dof<4:op[dof-2]+=sign*step
            else:ap+=sign*step
            values.append(mounted_equilibrium(beam,cp,ap,op,initial=initial)['energyJ'])
        calculated=-(values[1]-values[0])/(2*step);expected=(f.tolist()+fm.tolist()+[result['torqueOnMountAboutOriginNm']])[dof]
        error=abs(calculated-expected);assert error<(1e-4 if dof<4 else 1e-6),(index,dof,error)
        virtual.append({'index':index,'coordinate':dof,'energyDerivativeLoad':calculated,'reportedLoad':expected,'error':error})
report={'ribbonDerivativeChecks':derivatives,'bodyBalances':balances,'virtualWorkChecks':virtual,
 'limits':'Exact current ribbon offsets and fitted wedge plane. Clamped seat, linear elastic material and full operating-envelope acceptance remain open.'}
(ROOT/'outputs/converter-strip-pocket-verification.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print(json.dumps({'derivativeChecks':len(derivatives),'bodyBalances':balances,'virtualWorkChecks':len(virtual),
  'maxForceEnergyErrorN':max(r['error'] for r in virtual if r['coordinate']<4),'maxTorqueEnergyErrorNm':max(r['error'] for r in virtual if r['coordinate']==4)},indent=2),flush=True)
