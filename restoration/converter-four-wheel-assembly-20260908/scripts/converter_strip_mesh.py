"""Closed, constant-width strip with a rounded free tip; engineering XYZ."""
import math

def geometry(points,width,thickness):
    n=len(points);segments=[]
    for a,b in zip(points,points[1:]):
        dy,dz=b[0]-a[0],b[1]-a[1];length=math.hypot(dy,dz);segments.append((dy/length,dz/length))
    plus=[];minus=[];half=thickness/2
    for i,(y,z) in enumerate(points):
        if i==0:t=segments[0];offset=(-t[1]*half,t[0]*half)
        elif i==n-1:t=segments[-1];offset=(-t[1]*half,t[0]*half)
        else:
            a,b=segments[i-1],segments[i];den=1+a[0]*b[0]+a[1]*b[1]
            offset=(-(a[1]+b[1])*half/den,(a[0]+b[0])*half/den)
        plus.append((y+offset[0],z+offset[1]));minus.append((y-offset[0],z-offset[1]))
    profile=plus+minus;tipDirection=math.atan2(segments[-1][1],segments[-1][0]);tip=points[-1];arc=[n-1];steps=32
    for j in range(1,steps):
        a=tipDirection+math.pi/2-math.pi*j/steps;arc.append(len(profile));profile.append((tip[0]+half*math.cos(a),tip[1]+half*math.sin(a)))
    arc.append(2*n-1);centre=len(profile);profile.append(tuple(tip))
    caps=[]
    for i in range(n-2):caps.extend([(i,i+1,n+i+1),(i,n+i+1,n+i)])
    i=n-2;caps.extend([(i,i+1,centre),(i,centre,n+i),(n+i,centre,n+i+1)])
    caps.extend((centre,a,b) for a,b in zip(arc,arc[1:]))
    outline=list(range(n))+arc[1:-1]+list(range(2*n-1,n-1,-1));count=len(profile)
    vertices=[(x,y,z) for x in [-width/2,width/2] for y,z in profile]
    faces=[tuple(reversed(f)) for f in caps]+[tuple(v+count for v in f) for f in caps]
    for a,b in zip(outline,outline[1:]+outline[:1]):faces.append((a,b,b+count,a+count))
    return vertices,faces
