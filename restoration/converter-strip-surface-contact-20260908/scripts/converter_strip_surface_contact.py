"""Unilateral roller contact over ribbon faces, vertices and the rounded tip.
Extends the fitted clamped-strip study; not an original-part/material model.
"""
import math
import numpy as np
from converter_strip_pocket import PocketStripSpring
from converter_strip_spring import StripSpring

class SurfaceContactStrip(PocketStripSpring):
    accepts_contact_history=True
    def ribbon_vertices(self,angles):
        p=self.positions(angles);t=np.stack([np.cos(angles),np.sin(angles)],axis=1)
        n=np.stack([-np.sin(angles),np.cos(angles)],axis=1)
        m=np.vstack([n[0],(n[:-1]+n[1:])/(1+np.sum(n[:-1]*n[1:],axis=1))[:,None],n[-1]])
        return p+self.thickness/2*m,p-self.thickness/2*m

    def vertex_kinematics(self,angles,index,side):
        t=np.stack([np.cos(angles),np.sin(angles)],axis=1);n=np.stack([-np.sin(angles),np.cos(angles)],axis=1)
        p=self.positions(angles)[index];J=np.zeros((self.n,2));H=np.zeros((self.n,self.n,2))
        J[:index]=self.lengths[:index,None]*n[:index];ids=np.arange(index);H[ids,ids]=-self.lengths[:index,None]*t[:index]
        half=side*self.thickness/2
        if index in [0,self.n]:
            j=0 if index==0 else self.n-1;p=p+half*n[j];J[j]-=half*t[j];H[j,j]-=half*n[j]
        else:
            j=index-1;k=index;T=math.tan((angles[k]-angles[j])/2);S=1+T*T
            p=p+half*(n[j]-T*t[j]);J[j]+=half*(t[j]*(.5*S-1)-n[j]*T);J[k]-=half*.5*t[j]*S
            H[j,j]+=half*(n[j]*(S-1)+t[j]*T*(1-.5*S))
            H[j,k]+=half*(.5*t[j]*S*T-.5*n[j]*S);H[k,j]=H[j,k]
            H[k,k]-=half*.5*t[j]*S*T
        return p,J,H

    def circle_constraint(self,angles,centre,radius,key):
        kind,index,side=key
        if kind=='tip':
            g,J,H,p,n=self.tip_constraint(angles,centre,radius)
            return g,J,H,p[-1]-self.thickness/2*n,n
        a,Ja,Ha=self.vertex_kinematics(angles,index,side)
        if kind=='vertex':
            p,J,H=a,Ja,Ha;fraction=None
        else:
            b,Jb,Hb=self.vertex_kinematics(angles,index+1,side)
            edge=b-a;fraction=float(np.clip(np.dot(centre-a,edge)/np.dot(edge,edge),0,1))
            p=a+fraction*edge;J=Ja+fraction*(Jb-Ja);H=Ha+fraction*(Hb-Ha)
        delta=p-centre;distance=float(np.linalg.norm(delta));normal=delta/distance;P=(np.eye(2)-np.outer(normal,normal))/distance
        grad=J@normal;hess=J@P@J.T+H@normal
        if fraction is not None and 0<fraction<1:
            # Eliminate the contact point's free sliding coordinate. Omitting
            # this Schur term gives a fixed-material-point Hessian, not the
            # closest-surface contact used by the actual geometry.
            mixed=J@P@edge+(Jb-Ja)@normal;denominator=float(edge@P@edge)
            if denominator<=1e-20:raise RuntimeError('Degenerate sliding surface contact')
            hess-=np.outer(mixed,mixed)/denominator
        return distance-radius,grad,hess,p,normal

    def candidates(self,angles,centre,radius):
        result={};plus,minus=self.ribbon_vertices(angles)
        for side,vertices in [(1,plus),(-1,minus)]:
            for i,(a,b) in enumerate(zip(vertices,vertices[1:])):
                edge=b-a;fraction=float(np.clip(np.dot(centre-a,edge)/np.dot(edge,edge),0,1))
                p=a+fraction*edge;result[('face',i,side)]=(float(np.linalg.norm(p-centre)-radius),p)
        tip=self.positions(angles)[-1];tangent=np.array([math.cos(angles[-1]),math.sin(angles[-1])])
        if np.dot(centre-tip,tangent)>=0:
            normal=(tip-centre)/np.linalg.norm(tip-centre)
            result[('tip',self.n,0)]=(float(np.linalg.norm(tip-centre)-radius-self.thickness/2),tip-self.thickness/2*normal)
        for i,gap in enumerate(self.plane_gaps(angles)):
            result[('plane',i,0)]=(float(gap),self.plane_contact_point(angles,i))
        return result

    def face_fraction(self,angles,centre,key):
        vertices=self.ribbon_vertices(angles)[0 if key[2]==1 else 1];a,b=vertices[key[1]:key[1]+2]
        return float(np.clip(np.dot(centre-a,b-a)/np.dot(b-a,b-a),0,1))

    def constraint(self,angles,centre,radius,key):
        return self.plane_constraint(angles,key[1]) if key[0]=='plane' else self.circle_constraint(angles,centre,radius,key)[:3]

    def solve(self,centre,roller_radius=.00625,initial=None):
        centre=np.asarray(centre,dtype=float)
        if np.linalg.norm(centre-self.rest[0])<roller_radius:raise RuntimeError('Fixed strip root is inside the roller')
        history=initial if isinstance(initial,dict) else None
        if initial is None:angles=np.asarray(StripSpring.solve(self,centre,roller_radius)['angles'])
        else:angles=np.asarray(history['angles'] if history else initial,dtype=float).copy()
        candidates=self.candidates(angles,centre,roller_radius);active=[];points=[]
        prior_forces={}
        if history:
            for contact in history.get('wedgeContacts',[]):prior_forces[('plane',contact['node'],0)]=contact['forceN']
            if 'rollerContacts' in history:
                for contact in history['rollerContacts']:prior_forces[(contact['kind'],contact['node'],contact['side'])]=contact['forceN']
            elif history['forceN']>0:prior_forces[('tip',self.n,0)]=history['forceN']
            active=[k for k in prior_forces if k in candidates]
        else:
            for key,(gap,p) in candidates.items():
                if abs(gap)<=1e-8 and not any(key[0]!='plane' and k[0]!='plane' and np.linalg.norm(p-q)<1e-9 for k,q in points):
                    active.append(key);points.append((key,p))
        # The previous roller contact can be penetrated by the new prescribed
        # centre, so it is no longer a near-zero gap in the initial guess.
        # Keep its closest surface active before relaxing the prestressed strip.
        closest=min((k for k in candidates if k[0]!='plane'),key=lambda k:candidates[k][0])
        if closest not in active and (candidates[closest][0]<0 or np.linalg.norm(self.K@(angles-self.rest_angles))>1e-10):active.append(closest)
        J=np.array([self.constraint(angles,centre,roller_radius,k)[1] for k in active])
        forces=np.array([prior_forces.get(k,0.) for k in active]) if history else np.maximum(0.,np.linalg.lstsq(J.T,self.K@(angles-self.rest_angles),rcond=None)[0]) if active else np.zeros(0)
        iterations=0
        for outer in range(100):
            # Tip cap is a semicircle. Body-face contact must take over if the
            # roller passes behind it; never enforce a fictitious full tip ball.
            candidates=self.candidates(angles,centre,roller_radius)
            invalid=[i for i,k in enumerate(active) if k[0]=='tip' and k not in candidates]
            if invalid:
                for i in reversed(invalid):active.pop(i);forces=np.delete(forces,i)
            for iteration in range(80):
                iterations+=1
                if iteration and np.any(forces < -1e-7):break
                constraints=[self.constraint(angles,centre,roller_radius,k) for k in active]
                merged=False
                for i in range(len(active)):
                    if active[i][0]=='plane':continue
                    pi=self.circle_constraint(angles,centre,roller_radius,active[i])[3]
                    for j in range(i+1,len(active)):
                        if active[j][0]=='plane':continue
                        pj=self.circle_constraint(angles,centre,roller_radius,active[j])[3]
                        if np.linalg.norm(pi-pj)<1e-12 and np.max(np.abs(constraints[i][1]-constraints[j][1]))<1e-12:
                            # Adjacent clamped face projections can represent
                            # exactly the same vertex contact. Sum its reaction
                            # instead of solving a singular duplicate row.
                            forces[i]+=forces[j];active.pop(j);forces=np.delete(forces,j);merged=True;break
                    if merged:break
                if merged:continue
                g=np.array([x[0] for x in constraints]);J=np.array([x[1] for x in constraints]).reshape(len(active),self.n)
                residual=np.r_[self.K@(angles-self.rest_angles)-forces@J,-g];norm=float(np.linalg.norm(residual))
                if norm<1e-10 and (not len(g) or np.max(np.abs(g))<1e-10):break
                H=self.K-sum((f*c[2] for f,c in zip(forces,constraints)),np.zeros_like(self.K))
                matrix=np.block([[H,-J.T],[-J,np.zeros((len(g),len(g)))]])
                step=np.linalg.solve(matrix,-residual);scale=min(1.,.15/max(1e-30,float(np.abs(step[:self.n]).max())))
                for line in range(28):
                    trial=angles+scale*step[:self.n];lam=forces+scale*step[self.n:]
                    tc=[self.constraint(trial,centre,roller_radius,k) for k in active];tj=np.array([x[1] for x in tc]).reshape(len(active),self.n)
                    tr=np.r_[self.K@(trial-self.rest_angles)-lam@tj,-np.array([x[0] for x in tc])]
                    if np.linalg.norm(tr)<norm:angles=trial;forces=lam;break
                    scale*=.5
                else:raise RuntimeError(('Surface-contact line search',active,iteration,norm))
            else:raise RuntimeError(('Surface-contact Newton limit',active,norm,g.tolist(),forces.tolist()))
            if len(forces) and forces.min()<-1e-7:
                i=int(np.argmin(forces));active.pop(i);forces=np.delete(forces,i);continue
            candidates=self.candidates(angles,centre,roller_radius)
            invalid=[i for i,k in enumerate(active) if k[0]=='tip' and k not in candidates]
            if invalid:
                for i in reversed(invalid):active.pop(i);forces=np.delete(forces,i)
                continue
            key=min(candidates,key=lambda k:candidates[k][0]);gap=candidates[key][0]
            if gap<-1e-10:
                if key in active:raise RuntimeError(('Active surface contact remains infeasible',key,gap))
                if key[0]=='face' and 0<self.face_fraction(angles,centre,key)<1:
                    # Once contact moves into a face, a neighbouring face whose
                    # closest point is their shared vertex is redundant. Keeping
                    # both forces an impossible vertex-plus-interior tangency.
                    remove=[]
                    for i,k in enumerate(active):
                        if k[0]!='face' or k[2]!=key[2]:continue
                        fraction=self.face_fraction(angles,centre,k)
                        vertex=k[1] if fraction==0 else k[1]+1 if fraction==1 else None
                        if vertex in [key[1],key[1]+1]:remove.append(i)
                    for i in reversed(remove):active.pop(i);forces=np.delete(forces,i)
                active.append(key);forces=np.r_[forces,0.];continue
            return self.surface_result(angles,forces,active,centre,roller_radius,iterations)
        raise RuntimeError(('Surface-contact active-set limit',active))

    def surface_result(self,angles,forces,active,centre,radius,iterations):
        result=StripSpring.result(self,angles,0.,centre,radius,iterations,0.)
        contacts=[];wedge=[];F=np.zeros(2);constraints=[]
        for key,force in zip(active,forces):
            constraints.append(self.constraint(angles,centre,radius,key))
            if key[0]=='plane':
                wedge.append({'node':key[1],'forceN':float(force),'gapM':self.plane_constraint(angles,key[1],False),
                  'pointM':self.plane_contact_point(angles,key[1]).tolist(),'forceOnMountN':(force*self.plane_normal).tolist()})
            else:
                gap,_,_,point,normal=self.circle_constraint(angles,centre,radius,key);f=-force*normal;F+=f
                contacts.append({'kind':key[0],'node':key[1],'side':key[2],'forceN':float(force),'pointM':point.tolist(),'forceOnRollerN':f.tolist(),'gapM':float(gap)})
        J=np.array([x[1] for x in constraints]).reshape(len(active),self.n);H=self.K-sum((f*c[2] for f,c in zip(forces,constraints)),np.zeros_like(self.K))
        if len(active):
            _,sv,vh=np.linalg.svd(J,full_matrices=True);rank=int(np.sum(sv>sv.max()*1e-10));null=vh[rank:].T
        else:null=np.eye(self.n)
        candidates=self.candidates(angles,centre,radius)
        result.update({'forceN':float(np.linalg.norm(F)),'forceOnRollerN':F.tolist(),'rollerContacts':contacts,'wedgeContacts':wedge,
          'tipContactActive':any(k[0]=='tip' for k in active),'minimumRollerSurfaceGapM':min(g for k,(g,p) in candidates.items() if k[0]!='plane'),
          'minimumWedgePlaneGapM':float(self.plane_gaps(angles).min()),
          'minimumConstrainedStiffnessNm':float(np.linalg.eigvalsh(null.T@H@null).min()),
          'residual':float(np.linalg.norm(self.K@(angles-self.rest_angles)-forces@J))})
        return result
