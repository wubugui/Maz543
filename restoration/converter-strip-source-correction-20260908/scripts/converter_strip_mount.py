"""Rigid moving-mount force interface for the fitted quasi-static strip.
Not a factory seat model and not installed in the vehicle/contact integrator.
"""
import math
import numpy as np

def cross(a,b):return float(a[0]*b[1]-a[1]*b[0])

def mounted_equilibrium(spring,roller_centre,angle=0.,origin=(0.,0.),roller_radius=.00625,initial=None):
    c,s=math.cos(angle),math.sin(angle);rotation=np.array([[c,-s],[s,c]])
    origin=np.asarray(origin,dtype=float);centre=np.asarray(roller_centre,dtype=float)
    local=rotation.T@(centre-origin)
    result=spring.solve(local,roller_radius,initial)
    if result['minimumBeamCapsuleGapM'] < -1e-8:
        raise ValueError('Tip-only contact invalid: another strip segment intersects the roller')
    if result['forceN']>0 and result['tipCapFacesRoller']<=0:
        raise ValueError('Tip-only contact invalid: roller is outside the rounded end cap')
    if result['minimumConstrainedStiffnessNm']<=0:
        raise ValueError('Unstable constrained strip equilibrium')
    points=np.asarray(result['points']);force=rotation@np.asarray(result['forceOnRollerN'])
    root=origin+rotation@points[0];tip=origin+rotation@points[-1]
    # The spring loads its seat with both a force and a couple. Its endpoint
    # force alone, applied at the root, would lose the couple from bending.
    seat_force=-force;seat_couple=-cross(tip-root,force)
    mount_torque=cross(root-origin,seat_force)+seat_couple
    # Independent constitutive root couple from the first bending interval.
    root_bending_couple=float(spring.k[0]*(result['angles'][0]-spring.rest_angles[0]))
    result.update({'rollerCentreWorldM':centre.tolist(),'rootWorldM':root.tolist(),'tipWorldM':tip.tolist(),
      'forceOnRollerWorldN':force.tolist(),'forceOnMountWorldN':seat_force.tolist(),
      'coupleOnMountAtRootNm':seat_couple,'rootBendingCoupleNm':root_bending_couple,
      'torqueOnMountAboutOriginNm':mount_torque,'rollerSpinTorqueNm':0.,'mountAngleRad':float(angle)})
    return result
