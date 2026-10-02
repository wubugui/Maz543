"""Analytic planar four-bar closure. Coordinates are (height, outward lateral).

Positive camber means the wheel's upper edge points outwards. The outward
wheel-axis elevation has the opposite sign. No factory dimensions are supplied
here: callers provide their measured native datums.
"""
import math

def add(a,b):return tuple(x+y for x,y in zip(a,b))
def sub(a,b):return tuple(x-y for x,y in zip(a,b))
def mul(a,k):return tuple(x*k for x in a)
def rotate(p,t):return (p[0]*math.cos(t)-p[1]*math.sin(t),p[0]*math.sin(t)+p[1]*math.cos(t))
def angle(p):return math.atan2(p[0],p[1])

def close_at_camber(lower_inner,upper_inner,lower_outer,upper_outer,wheel,camber_degrees):
 t=math.radians(camber_degrees)
 r=math.dist(lower_inner,lower_outer);s=math.dist(upper_inner,upper_outer)
 upright=rotate(sub(upper_outer,lower_outer),t)
 centre2=sub(upper_inner,upright);d=math.dist(lower_inner,centre2)
 result={'camber_degrees':camber_degrees,'circle_centre_distance_m':d,'circle_radii_m':[r,s],'internal_separation_deficit_m':abs(r-s)-d,'external_separation_deficit_m':d-(r+s),'candidates':[]}
 if d<abs(r-s) or d>r+s or d==0:
  result['status']='NO_FIXED_HARDPOINT_RIGID_LINK_CLOSURE';return result
 e=mul(sub(centre2,lower_inner),1/d);along=(r*r-s*s+d*d)/(2*d);height=math.sqrt(max(0,r*r-along*along));mid=add(lower_inner,mul(e,along))
 for sign in [-1,1]:
  lo=add(mid,(-sign*height*e[1],sign*height*e[0]));up=add(lo,upright);w=add(lo,rotate(sub(wheel,lower_outer),t))
  lower_angle=angle(sub(lo,lower_inner));upper_angle=angle(sub(up,upper_inner))
  result['candidates'].append({'lower_outer':lo,'upper_outer':up,'wheel':w,'wheel_shift_m':sub(w,wheel),'lower_angle_to_outward_horizontal_degrees':math.degrees(lower_angle),'upper_angle_to_outward_horizontal_degrees':math.degrees(upper_angle),'lower_rotation_delta_radians':lower_angle-angle(sub(lower_outer,lower_inner)),'upper_rotation_delta_radians':upper_angle-angle(sub(upper_outer,upper_inner)),'lower_inner_minus_outer_height_m':lower_inner[0]-lo[0],'upper_inner_minus_outer_height_m':upper_inner[0]-up[0],'lower_outer_displacement_m':math.dist(lo,lower_outer),'closure_length_error_m':max(abs(math.dist(lo,lower_inner)-r),abs(math.dist(up,upper_inner)-s),abs(math.dist(lo,up)-math.dist(lower_outer,upper_outer)))})
 result['candidates'].sort(key=lambda c:c['lower_outer_displacement_m']);result['status']='RIGID_LINK_CIRCLE_INTERSECTIONS';return result

if __name__=='__main__':
 import argparse,json
 p=argparse.ArgumentParser();p.add_argument('--output',required=True);a=p.parse_args()
 datums=((.6,.55),(1.025,.61),(.6,1.065),(.997,1.015),(.75,1.1875))
 rows=[close_at_camber(*datums,c) for c in [-1,0,1]]
 assert rows[0]['status']=='RIGID_LINK_CIRCLE_INTERSECTIONS'
 assert abs(rows[0]['candidates'][0]['wheel_shift_m'][0]+.0715925639906536)<1e-12
 assert rows[1]['candidates'][0]['lower_outer_displacement_m']<1e-12
 assert rows[2]['status']=='NO_FIXED_HARDPOINT_RIGID_LINK_CLOSURE'
 assert abs(rows[2]['internal_separation_deficit_m']-.0024437525280316)<1e-12
 from pathlib import Path
 Path(a.output).write_text(json.dumps({'status':'ANALYTIC_EXISTING_RECONSTRUCTION_ONLY','coordinate_convention':'(height, outward lateral); positive camber = upper wheel edge outward; c=-asin(outward_axis.z)','datums_from':'published testcar/work/suspension-poses.json spec, not factory dimensions','rows':rows,'limits':['Negative camber is a conditional branch, not an approved static setting.','No load, tyre compliance, steering link or source sign acceptance.','Positive one-degree camber is analytically impossible with these fixed native reconstruction datums.'],'all16VehicleGates':'OPEN'},indent=2)+'\n')
