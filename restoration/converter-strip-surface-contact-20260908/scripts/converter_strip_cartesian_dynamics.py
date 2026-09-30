"""Constant-mass Cartesian alternative to the diagnostic polar integrator.

Same contact laws and quasi-static strip. Public checkpoint coordinates remain
polar; no material parameters, friction, or prescribed motion are changed.
"""
import math
import numpy as np
from converter_strip_dynamics import StripFreewheel

class CartesianStripFreewheel(StripFreewheel):
    def step(self,old,torque,h):
        R0,phi0,spin0,angle0=old['q'];vr,omega,ws,wo=old['v']
        e=np.array([math.cos(phi0),math.sin(phi0)]);t=np.array([-e[1],e[0]])
        q=np.r_[R0*e,spin0,angle0];v0=np.r_[vr*e+R0*omega*t,ws,wo]
        inv=np.array([1/(self.N*self.m),1/(self.N*self.m),1/(self.N*self.j),1/self.J])
        strip=old['strip']
        force=np.r_[self.N*np.asarray(strip['forceOnRollerWorldN']),0.,self.N*strip['torqueOnMountAboutOriginNm']+torque]
        free_velocity=v0+h*inv*force;v=free_velocity.copy();iterations=0
        for nonlinear in range(24):
            trial=q+h*v;C=trial[:2];R=float(np.linalg.norm(C));normal=C/R;tangent=np.array([-normal[1],normal[0]])
            a=trial[3]+self.alpha;n=np.array([math.cos(a),math.sin(a)]);t=np.array([-n[1],n[0]])
            gaps=np.array([R-self.ri-self.r,(self.ri+self.r)*math.cos(self.alpha)-np.dot(n,C)])
            J=np.array([[*normal,0,0],[-n[0],-n[1],0,-np.dot(t,C)],
                        [*tangent,-self.r,0],[*t,self.r,-(np.dot(n,C)+self.r)]])
            target=J[:2]@v-gaps/h;K=(J*inv)@J.T;free=J@free_velocity;best=None
            for m0 in range(4):
                for m1 in range(4):
                    iterations+=1;modes=[m0,m1];A=np.zeros((4,4));rhs=np.zeros(4)
                    for c,m in enumerate(modes):
                        j=c+2
                        if m==0:A[c,c]=1;A[j,j]=1
                        else:
                            A[c]=K[c];rhs[c]=target[c]-free[c]
                            if m==1:A[j]=K[j];rhs[j]=-free[j]
                            else:A[j,j]=1;A[j,c]=(1 if m==2 else -1)*self.mu
                    try:lam=np.linalg.solve(A,rhs)
                    except np.linalg.LinAlgError:continue
                    speed=free+K@lam;error=0.
                    for c,m in enumerate(modes):
                        nn=lam[c];tt=lam[c+2];vn=speed[c]-target[c];vt=speed[c+2]
                        error=max(error,-nn*max(K[c,c],K[c+2,c+2]),-vn if m==0 else abs(vn),
                                  abs(vt) if m==1 else -vt if m==2 else vt if m==3 else 0.,
                                  (abs(tt)-self.mu*max(0,nn))*K[c+2,c+2])
                    if error>1e-8:continue
                    velocity=free_velocity+inv*(J.T@lam);energy=float(np.sum(.5*velocity**2/inv))
                    if best is None or energy<best[0]:best=(energy,velocity,lam,error)
            if best is None:raise RuntimeError('No admissible Cartesian two-contact Coulomb mode')
            energy,velocity,lam,error=best
            change=np.max(np.abs(v-velocity)*np.array([1,1,self.r,R])*h);v=velocity
            if change<1e-11:break
        else:raise RuntimeError('Cartesian roller/race geometry did not converge')
        x=q+h*v;C=x[:2];R=float(np.linalg.norm(C));raw=math.atan2(C[1],C[0])
        phi=phi0+math.atan2(math.sin(raw-phi0),math.cos(raw-phi0))
        polar_q=np.array([R,phi,x[2],x[3]]);e=C/R;t=np.array([-e[1],e[0]])
        polar_v=np.array([np.dot(e,v[:2]),np.dot(t,v[:2])/R,v[2],v[3]])
        generalized,strip=self.spring(polar_q)
        gaps=[R-self.ri-self.r,(self.ri+self.r)*math.cos(self.alpha)-R*math.cos(phi-x[3]-self.alpha)]
        return {'q':polar_q,'v':polar_v,'time':old['time']+h,'inputWork':old['inputWork']+torque*(x[3]-angle0),
                'kinetic':float(.5*np.sum(v*v/inv)),'springEnergy':self.N*strip['energyJ'],'strip':strip,'springGeneralized':generalized,
                'gaps':gaps,'normalForce':(lam[:2]/h/self.N).tolist(),'frictionForce':(lam[2:]/h/self.N).tolist(),
                'residual':float(error),'iterations':iterations}
