"""Scientific plot of measured native vertices; no photographic image editing."""
import hashlib
import json
import os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
os.environ['MPLCONFIGDIR']=str(ROOT/'work/stop-projection-mpl-cache')
os.environ['XDG_CACHE_HOME']=str(ROOT/'work/stop-projection-font-cache')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon

OUT=ROOT/'outputs/cloud-suspension-stop-axis-20261001'
source=OUT/'projection-probe.json';data=json.loads(source.read_text());r=data['rows'][1]
ray=json.loads((OUT/'axis-probe.json').read_text())['rows'][1]
cx,cy,_=ray['actual_bolt_cap_centre']
local=lambda p:((p[0]-cx)*1000,(p[1]-cy)*1000)
bolt=[local(p) for p in r['bolt_full_projection_hull']]
triangle=[local(p) for p in r['nearest_triangle']['world_vertices']]
fig,ax=plt.subplots(figsize=(10,7),dpi=150)
fig.patch.set_facecolor('#eef2f4');ax.set_facecolor('#ffffff')
ax.add_patch(Polygon(bolt,facecolor='#efaa52',edgecolor='#9b570b',linewidth=1.5,label='Convex hull of the entire evaluated bolt'))
ax.add_patch(Polygon(triangle,facecolor='#4b9bb7',edgecolor='#256b84',linewidth=2,label='Nearest upper-arm triangle projection'))
p=min(bolt,key=lambda p:p[1]);edge=max(p[1] for p in triangle)
assert abs((p[1]-edge)/1000-r['minimum_xy_projection_gap_m'])<1e-7
ax.annotate('',xy=(p[0],p[1]),xytext=(p[0],edge),arrowprops={'arrowstyle':'<->','color':'#b62b34','linewidth':1.7})
ax.text(2,(p[1]+edge)/2,f"{r['minimum_xy_projection_gap_m']*1000:.3f} mm gap",color='#a3232c',va='center',fontsize=12)
ax.plot([0],[0],'+',color='#653d13',markersize=10)
ax.set_xlim(-30,35);ax.set_ylim(-25,22);ax.set_aspect('equal')
ax.set_xlabel('Longitudinal X relative to bolt centre (mm)');ax.set_ylabel('Transverse Y relative to bolt centre (mm)')
ax.grid(True,color='#dce3e7',linewidth=.6);ax.legend(loc='upper left',fontsize=9)
ax.set_title('Actual native projection: retained bolt misses upper arm\nStation 0, 138.5 mm installation setting',fontsize=14,pad=15)
fig.text(.08,.035,'Original-axis vertical translation leaves these XY projections unchanged.\nOnly the nearest upper-arm triangle is drawn; the calculation checks every upper-arm triangle.\nFitted model hardpoints. Three sampled suspension poses; no whole-vehicle acceptance.',fontsize=9,color='#36434c')
fig.subplots_adjust(left=.13,right=.97,top=.86,bottom=.17)
path=OUT/'actual-native-projection-gap.png';assert not path.exists();fig.savefig(path);plt.close(fig)
(OUT/'projection-plot-provenance.json').write_text(json.dumps({'file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'source_report_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'kind':'Scientific plot of actual evaluated native vertices, not a Cycles screenshot','displayed_upper_part':r['nearest_triangle']['object'],'triangle':r['nearest_triangle']['triangle'],'source_native_sha256':data['source_sha256']},indent=2)+'\n')
print('NATIVE_PROJECTION_PLOT',path.name)
