"""Planar inextensible curved-strip cantilever with frictionless rounded-tip contact.
Source-guided form, fitted free curve, clamped seating, width and thickness.
This standalone study is not installed in the freewheel dynamics yet.
"""
import numpy as np
import math

def rest_curve(arc_segments=32,tail_segments=12):
    # Tail seats at the fitted pocket wall; a broad half curl ends at the roller.
    control=np.array([[.0618,-.01564],[.0618,-.0137],[.0628,-.01235],[.064,-.01235]])
    points=[]
    for t in np.linspace(0,1,tail_segments+1):
        points.append((1-t)**3*control[0]+3*(1-t)**2*t*control[1]+3*(1-t)*t*t*control[2]+t**3*control[3])
    for a in np.linspace(-math.pi/2,math.pi/2,arc_segments+1)[1:]:
        points.append(np.array([.064,-.0091])+.00325*np.array([math.cos(a),math.sin(a)]))
    return np.array(points)

class StripSpring:
    def __init__(self,points=None,width=.016,thickness=.00030,young=210e9):
        self.rest=rest_curve() if points is None else np.array(points,dtype=float)
        segments=np.diff(self.rest,axis=0);self.lengths=np.linalg.norm(segments,axis=1)
        self.rest_angles=np.unwrap(np.arctan2(segments[:,1],segments[:,0]));self.n=len(segments)
        self.width=width;self.thickness=thickness;self.young=young;self.EI=young*width*thickness**3/12
        # Segment directors live at segment midpoints. A clamped root fixes the
        # boundary director, not the whole first segment: its bending interval
        # is half a segment. Freezing that segment causes first-order bias.
        self.bending_lengths=np.r_[self.lengths[0]/2,(self.lengths[1:]+self.lengths[:-1])/2]
        self.k=self.EI/self.bending_lengths
        self.D=np.eye(self.n)-np.eye(self.n,k=-1)
        self.K=self.D.T@np.diag(self.k)@self.D

    def positions(self,angles):
        segments=self.lengths[:,None]*np.stack([np.cos(angles),np.sin(angles)],axis=1)
        return np.vstack([self.rest[0],self.rest[0]+np.cumsum(segments,axis=0)])

    def tip_constraint(self,angles,centre,radius):
        p=self.positions(angles);d=p[-1]-centre;distance=np.linalg.norm(d);normal=d/distance
        jac=self.lengths[:,None]*np.stack([-np.sin(angles),np.cos(angles)],axis=1)
        grad=jac@normal
        hess=jac@((np.eye(2)-np.outer(normal,normal))/distance)@jac.T
        hess+=np.diag(-self.lengths*(np.stack([np.cos(angles),np.sin(angles)],axis=1)@normal))
        return distance-radius-self.thickness/2,grad,hess,p,normal

    def solve(self,centre,roller_radius=.00625,initial=None):
        centre=np.array(centre);angles=self.rest_angles.copy() if initial is None else np.array(initial)
        if self.tip_constraint(self.rest_angles,centre,roller_radius)[0]>=0:
            return self.result(self.rest_angles,0,centre,roller_radius,0,0)
        force=0.
        for iteration in range(80):
            gap,grad,hess,points,normal=self.tip_constraint(angles,centre,roller_radius)
            residual=np.r_[self.K@(angles-self.rest_angles)-force*grad,-gap]
            norm=np.linalg.norm(residual)
            if norm<1e-11 and abs(gap)<1e-10:
                assert force>=0,('tensile contact',force)
                return self.result(angles,force,centre,roller_radius,iteration,norm)
            matrix=np.block([[self.K-force*hess,-grad[:,None]],[-grad[None,:],np.zeros((1,1))]])
            step=np.linalg.solve(matrix,-residual)
            scale=min(1.,.25/max(1e-30,np.max(np.abs(step[:-1]))))
            for line in range(24):
                trial=angles.copy();trial+=scale*step[:-1];lam=force+scale*step[-1]
                g,j,_,_,_=self.tip_constraint(trial,centre,roller_radius)
                r=np.r_[self.K@(trial-self.rest_angles)-lam*j,-g]
                if np.linalg.norm(r)<norm:
                    angles=trial;force=lam;break
                scale*=.5
            else:raise RuntimeError(('strip line search',centre.tolist(),iteration,norm))
        raise RuntimeError(('strip did not converge',centre.tolist(),norm))

    def result(self,angles,force,centre,radius,iterations,residual):
        gap,grad,hess,points,normal=self.tip_constraint(angles,centre,radius)
        change=self.D@(angles-self.rest_angles);energy=.5*np.sum(self.k*change*change)
        stress=np.max(np.abs(change/self.bending_lengths))*self.young*self.thickness/2
        # Full centreline capsule clearance detects when tip-only contact is invalid.
        minimum=float('inf')
        for a,b in zip(points,points[1:]):
            ab=b-a;t=np.clip(np.dot(centre-a,ab)/np.dot(ab,ab),0,1)
            minimum=min(minimum,float(np.linalg.norm(a+t*ab-centre)-radius-self.thickness/2))
        tangent=np.array([math.cos(angles[-1]),math.sin(angles[-1])])
        # The equilibrium must be a minimum on the active-contact tangent space.
        _,_,vh=np.linalg.svd(grad[None,:],full_matrices=True);null=vh[1:].T
        minimumStiffness=float(np.linalg.eigvalsh(null.T@(self.K-force*hess)@null).min())
        return {'points':points.tolist(),'angles':angles.tolist(),'forceN':float(force),'forceOnRollerN':(-force*normal).tolist(),
          'energyJ':float(energy),'tipGapM':float(gap),'minimumBeamCapsuleGapM':minimum,'tipCapFacesRoller':float(np.dot(-normal,tangent)),
          'maximumIncrementalBendingStressPa':float(stress),'minimumConstrainedStiffnessNm':minimumStiffness,'iterations':iterations,'residual':float(residual)}
