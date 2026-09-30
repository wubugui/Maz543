"""Offline roller/race dynamics driven by the curved-strip contact energy.
One periodic cell represents twelve identical rollers sharing one outer race.
The strip is massless/quasi-static; no factory performance is claimed.
"""
import math
import numpy as np
from converter_strip_mount import mounted_equilibrium,cross

class PocketDomainExit(RuntimeError):
    def __init__(self,beta,q):
        self.beta=float(beta);self.candidate_q=np.asarray(q).copy()
        super().__init__(('Outside audited pocket angular region',self.beta,'candidatePolarQ',self.candidate_q.tolist()))

class StripFreewheel:
    def __init__(self,beam,roller_mass,roller_inertia,outer_inertia,rollers=12,friction=.12):
        self.beam=beam;self.m=roller_mass;self.j=roller_inertia;self.J=outer_inertia;self.N=rollers;self.mu=friction
        self.ri=.056;self.r=.00625;self.alpha=math.radians(7);self.initial_angles=None

    def spring(self,q):
        R,phi,spin,angle=q;centre=R*np.array([math.cos(phi),math.sin(phi)])
        beta=math.atan2(math.sin(phi-angle),math.cos(phi-angle))
        # This stop exposes an unexamined pocket region. It never clamps a
        # roller pose or angular speed and must not be treated as a trajectory.
        if beta<-.060001 or beta>.000001:raise PocketDomainExit(beta,q)
        row=mounted_equilibrium(self.beam,centre,angle,initial=self.initial_angles)
        self.initial_angles=row['angles']
        force=np.asarray(row['forceOnRollerWorldN']);radial=np.dot(force,[math.cos(phi),math.sin(phi)])
        generalized=self.N*np.array([radial,cross(centre,force),0.,row['torqueOnMountAboutOriginNm']])
        return generalized,row

    def initial(self):
        q=np.array([self.ri+self.r,0.,0.,0.]);v=np.zeros(4);force,strip=self.spring(q)
        return {'q':q,'v':v,'time':0.,'inputWork':0.,'kinetic':0.,'springEnergy':self.N*strip['energyJ'],
          'strip':strip,'springGeneralized':force,'gaps':[0.,0.],'normalForce':[0.,0.],'frictionForce':[0.,0.],'residual':0.,'iterations':0}

    def step(self,old,torque,h):
        N=self.N;r=self.r;q=old['q'];R0,phi0,spin0,angle0=q;v0=old['v'];radial,orbital=v0[:2]
        inv=np.array([1/(N*self.m),1/(N*self.m*R0**2),1/(N*self.j),1/self.J])
        force=old['springGeneralized'].copy();force[0]+=N*self.m*R0*orbital**2
        force[1]-=2*N*self.m*R0*radial*orbital;force[3]+=torque
        free_velocity=v0+h*inv*force;v=free_velocity.copy();iterations=0
        for nonlinear in range(24):
            trial=q+h*v;R,phi,spin,angle=trial;delta=phi-angle-self.alpha;cd=math.cos(delta);sd=math.sin(delta)
            gaps=np.array([R-self.ri-r,(self.ri+r)*math.cos(self.alpha)-R*cd])
            J=np.array([[1,0,0,0],[-cd,R*sd,0,-R*sd],[0,R,-r,0],[sd,R*cd,r,-(R*cd+r)]])
            target=J[:2]@v-gaps/h;K=(J*inv)@J.T;free=J@free_velocity;best=None
            for m0 in range(4):
                for m1 in range(4):
                    iterations+=1;modes=[m0,m1];A=np.zeros((4,4));rhs=np.zeros(4)
                    for c,m in enumerate(modes):
                        t=c+2
                        if m==0:A[c,c]=1;A[t,t]=1
                        else:
                            A[c]=K[c];rhs[c]=target[c]-free[c]
                            if m==1:A[t]=K[t];rhs[t]=-free[t]
                            else:A[t,t]=1;A[t,c]=(1 if m==2 else -1)*self.mu
                    try:lam=np.linalg.solve(A,rhs)
                    except np.linalg.LinAlgError:continue
                    speed=free+K@lam;error=0.
                    for c,m in enumerate(modes):
                        n=lam[c];t=lam[c+2];vn=speed[c]-target[c];vt=speed[c+2]
                        error=max(error,-n*max(K[c,c],K[c+2,c+2]),-vn if m==0 else abs(vn),
                          abs(vt) if m==1 else -vt if m==2 else vt if m==3 else 0.,
                          (abs(t)-self.mu*max(0,n))*K[c+2,c+2])
                    if error>1e-8:continue
                    velocity=free_velocity+inv*(J.T@lam);energy=float(np.sum(.5*velocity**2/inv))
                    if best is None or energy<best[0]:best=(energy,velocity,lam,error)
            if best is None:raise RuntimeError('No admissible two-contact Coulomb mode')
            energy,velocity,lam,error=best;change=np.max(np.abs(v-velocity)*np.array([1,R,r,R])*h);v=velocity
            if change<1e-11:break
        else:raise RuntimeError('Nonlinear roller/race contact did not converge')
        next_q=q+h*v;generalized,strip=self.spring(next_q);R,phi,spin,angle=next_q
        gaps=[R-self.ri-r,(self.ri+r)*math.cos(self.alpha)-R*math.cos(phi-angle-self.alpha)]
        kinetic=.5*N*self.m*(v[0]**2+R**2*v[1]**2)+.5*N*self.j*v[2]**2+.5*self.J*v[3]**2
        return {'q':next_q,'v':v,'time':old['time']+h,'inputWork':old['inputWork']+torque*(angle-angle0),
          'kinetic':float(kinetic),'springEnergy':N*strip['energyJ'],'strip':strip,'springGeneralized':generalized,
          'gaps':gaps,'normalForce':(lam[:2]/h/N).tolist(),'frictionForce':(lam[2:]/h/N).tolist(),'residual':float(error),'iterations':iterations}
