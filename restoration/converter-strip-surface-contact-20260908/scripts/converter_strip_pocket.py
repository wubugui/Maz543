"""Fitted curved strip with roller-tip and outer wedge-plane contact.
The plane constrains actual ribbon offsets, including interior mitres.
No factory seating, material or operating-envelope claim is made.
"""
import math
import numpy as np
from converter_strip_spring import StripSpring

class PocketStripSpring(StripSpring):
    def __init__(self,*args,inner_radius=.056,roller_radius=.00625,wedge_angle=math.radians(7),**kwargs):
        super().__init__(*args,**kwargs)
        self.plane_normal=np.array([math.cos(wedge_angle),math.sin(wedge_angle)])
        self.plane_distance=roller_radius+(inner_radius+roller_radius)*math.cos(wedge_angle)

    def plane_constraint(self,angles,index,derivatives=True):
        p=self.positions(angles);normal=self.plane_normal;half=self.thickness/2
        tangent=np.stack([np.cos(angles),np.sin(angles)],axis=1)
        A=tangent@normal;B=np.stack([-np.sin(angles),np.cos(angles)],axis=1)@normal
        skin_grad=np.zeros(self.n);skin_hess=np.zeros((self.n,self.n)) if derivatives else None
        if index==self.n and A[-1]>0:
            # Maximum projection over the outward-facing rounded end cap.
            skin=1.
        elif index==0 or index==self.n:
            j=0 if index==0 else self.n-1;sign=1. if B[j]>=0 else -1.
            skin=abs(B[j]);skin_grad[j]=-sign*A[j]
            if derivatives:skin_hess[j,j]=-sign*B[j]
        else:
            j=index-1;k=index;delta=(angles[k]-angles[j])/2;tan=math.tan(delta);sec2=1+tan*tan
            h=B[j]-A[j]*tan;sign=1. if h>=0 else -1.;skin=abs(h)
            skin_grad[j]=sign*(A[j]*(.5*sec2-1)-B[j]*tan);skin_grad[k]=sign*(-.5*A[j]*sec2)
            if derivatives:
                skin_hess[j,j]=sign*(B[j]*(sec2-1)+A[j]*tan*(1-.5*sec2))
                skin_hess[j,k]=skin_hess[k,j]=sign*(.5*A[j]*sec2*tan-.5*B[j]*sec2)
                skin_hess[k,k]=sign*(-.5*A[j]*sec2*tan)
        gap=float(self.plane_distance-np.dot(normal,p[index])-half*skin)
        if not derivatives:return gap
        grad=-half*skin_grad;grad[:index]-=self.lengths[:index]*B[:index]
        hess=-half*skin_hess;ids=np.arange(index);hess[ids,ids]+=self.lengths[:index]*A[:index]
        return gap,grad,hess

    def plane_gaps(self,angles):
        # Same exact support geometry in vector form for active-set discovery.
        p=self.positions(angles);a=np.cos(angles)*self.plane_normal[0]+np.sin(angles)*self.plane_normal[1]
        b=-np.sin(angles)*self.plane_normal[0]+np.cos(angles)*self.plane_normal[1]
        skin=np.r_[abs(b[0]),np.abs(b[:-1]-a[:-1]*np.tan(np.diff(angles)/2)),1. if a[-1]>0 else abs(b[-1])]
        return self.plane_distance-p@self.plane_normal-self.thickness/2*skin

    def plane_contact_point(self,angles,index):
        tangent=np.stack([np.cos(angles),np.sin(angles)],axis=1)
        normals=np.stack([-np.sin(angles),np.cos(angles)],axis=1)
        if index==self.n and np.dot(tangent[-1],self.plane_normal)>0:offset=self.plane_normal
        elif index==0 or index==self.n:
            offset=normals[0 if index==0 else -1]
            offset=offset*(1. if np.dot(offset,self.plane_normal)>=0 else -1.)
        else:
            offset=(normals[index-1]+normals[index])/(1+np.dot(normals[index-1],normals[index]))
            offset=offset*(1. if np.dot(offset,self.plane_normal)>=0 else -1.)
        return self.positions(angles)[index]+self.thickness/2*offset

    def solve(self,centre,roller_radius=.00625,initial=None):
        centre=np.asarray(centre,dtype=float)
        if initial is None:
            baseline=super().solve(centre,roller_radius)
            angles=np.asarray(baseline['angles']);active=[];forces=np.array([baseline['forceN']])
            if baseline['forceN']==0:
                if self.plane_gaps(angles).min()<-1e-10:raise RuntimeError('Free strip intersects wedge: unseated free-shape case is not supported')
                return self.pocket_result(angles,forces,active,centre,roller_radius,0,0.)
        else:
            # Continue the previously equilibrated shape and its wedge contacts.
            # Re-solving an unconstrained tip-only beam here discards that
            # feasible branch precisely when the strip is confined by the race.
            angles=np.asarray(initial,dtype=float).copy()
            active=np.flatnonzero(self.plane_gaps(angles)<1e-8).tolist()
            J=np.array([self.tip_constraint(angles,centre,roller_radius)[1]]+[self.plane_constraint(angles,i)[1] for i in active])
            forces=np.maximum(0.,np.linalg.lstsq(J.T,self.K@(angles-self.rest_angles),rcond=None)[0])
        iterations=0
        for outer in range(40):
            for iteration in range(80):
                iterations+=1
                # A newly activated neighbour can unload an earlier contact.
                # Release that tensile constraint immediately; demanding full
                # Newton convergence with it retained can stall indefinitely.
                if iteration and np.any(forces[1:] < -1e-7):break
                constraints=[self.tip_constraint(angles,centre,roller_radius)[:3]]+[self.plane_constraint(angles,i) for i in active]
                g=np.array([x[0] for x in constraints]);J=np.array([x[1] for x in constraints])
                residual=np.r_[self.K@(angles-self.rest_angles)-forces@J,-g];norm=np.linalg.norm(residual)
                if norm<1e-10 and np.max(np.abs(g))<1e-10:break
                hess=self.K-sum((f*x[2] for f,x in zip(forces,constraints)),np.zeros_like(self.K))
                matrix=np.block([[hess,-J.T],[-J,np.zeros((len(g),len(g)))]])
                step=np.linalg.solve(matrix,-residual);scale=min(1.,.25/max(1e-30,float(np.abs(step[:self.n]).max())))
                for line in range(28):
                    trial=angles+scale*step[:self.n];lam=forces+scale*step[self.n:]
                    trial_c=[self.tip_constraint(trial,centre,roller_radius)[:2]]+[self.plane_constraint(trial,i)[:2] for i in active]
                    r=np.r_[self.K@(trial-self.rest_angles)-lam@np.array([x[1] for x in trial_c]),-np.array([x[0] for x in trial_c])]
                    if np.linalg.norm(r)<norm:angles=trial;forces=lam;break
                    scale*=.5
                else:raise RuntimeError(('Pocket strip line search',centre.tolist(),active,iteration,float(norm)))
            else:raise RuntimeError(('Pocket strip Newton limit',centre.tolist(),active,float(norm),g.tolist(),forces.tolist()))
            gaps=self.plane_gaps(angles)
            if min(forces)<-1e-7:
                remove=int(np.argmin(forces))
                if remove==0:raise RuntimeError('Roller contact opens during wedge contact; additional active-set mode required')
                active.pop(remove-1);forces=np.delete(forces,remove)
            elif gaps.min()<-1e-10:
                index=int(np.argmin(gaps))
                if index in active:raise RuntimeError(('Active wedge contact remains infeasible',index,float(gaps[index])))
                active.append(index);forces=np.r_[forces,0.]
            else:
                return self.pocket_result(angles,forces,active,centre,roller_radius,iterations,0.)
        raise RuntimeError(('Pocket strip active-set limit',centre.tolist(),active))

    def pocket_result(self,angles,forces,active,centre,radius,iterations,residual):
        # Retain existing full-roller clearance and mesh/energy result fields.
        result=super().result(angles,float(forces[0]),centre,radius,iterations,residual)
        constraints=[self.tip_constraint(angles,centre,radius)[:3]]+[self.plane_constraint(angles,i) for i in active]
        J=np.array([x[1] for x in constraints]);_,singular,vh=np.linalg.svd(J,full_matrices=True)
        rank=int(np.sum(singular>singular.max()*1e-10));null=vh[rank:].T
        H=self.K-sum((f*x[2] for f,x in zip(forces,constraints)),np.zeros_like(self.K))
        result['minimumConstrainedStiffnessNm']=float(np.linalg.eigvalsh(null.T@H@null).min())
        result['residual']=float(np.linalg.norm(self.K@(angles-self.rest_angles)-forces@J))
        result['minimumWedgePlaneGapM']=float(self.plane_gaps(angles).min())
        result['wedgeContacts']=[{'node':i,'forceN':float(f),'gapM':float(self.plane_constraint(angles,i,False)),
          'pointM':self.plane_contact_point(angles,i).tolist(),'forceOnMountN':(f*self.plane_normal).tolist()} for i,f in zip(active,forces[1:])]
        return result
