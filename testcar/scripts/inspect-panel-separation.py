"""Check actual retained dashboard/seat partition; do not save the model."""
import bpy,json,hashlib,argparse,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--input',type=Path,default=ROOT/'outputs/cloud-cab-panel-fit-20261001/iteration-02/MAZ543A_Master.blend')
args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
p=args.input.resolve();out=p.parent/'separation-inspection.json';assert not out.exists();h=hashlib.sha256(p.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(p))
records=[]
for name in ['cab_0064','BL_PanelFit_original_dashboard_blocks_retained']:
 o=bpy.data.objects[name];vs=[o.matrix_world@v.co for v in o.data.vertices]
 records.append({'name':name,'vertices':len(vs),'polygons':len(o.data.polygons),'hide_render':o.hide_render,'bounds':[[min(v[k] for v in vs),max(v[k] for v in vs)] for k in range(3)] if vs else None,'vertices_outside_dashboard_selection':sum(v.x>=-4.78 for v in vs)})
assert hashlib.sha256(p.read_bytes()).hexdigest()==h
r={'source_sha256':h,'records':records,'expected_archived_dashboard_vertices':1800,'saved_file_unchanged':True}
out.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r),flush=True)
