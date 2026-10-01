"""Retain all native pair results; distinguish fitted compound-piece interfaces."""
import bpy,json,hashlib,argparse,sys,itertools
from pathlib import Path
from mathutils.bvhtree import BVHTree
p=argparse.ArgumentParser();p.add_argument('--input',required=True,type=Path);a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);path=a.input.resolve();out=path.parent/'contacts.json';assert not out.exists();manifest=json.loads((path.parent/'build.json').read_text());sha=hashlib.sha256(path.read_bytes()).hexdigest();assert sha==manifest['model_sha256']
bpy.ops.wm.open_mainfile(filepath=str(path));bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();trees={}
for n in manifest['closed_solids']:
 o=bpy.data.objects[n];e=o.evaluated_get(dg);m=e.to_mesh();m.calc_loop_triangles();v=[e.matrix_world@x.co for x in m.vertices];t=[tuple(x.vertices) for x in m.loop_triangles];trees[n]=BVHTree.FromPolygons(v,t,all_triangles=True);e.to_mesh_clear()
compound={frozenset(['ZERO CORRECTOR — slotted front head','ZERO CORRECTOR — retained separate shank']):'Two fitted pieces of one correction screw; mechanical joint not separately established',frozenset(['BUTTON — movable stem','BUTTON — movable cap']):'Two fitted pieces of one actuator; cap/stem joint not separately established',frozenset(['CASE — fitted hollow cylindrical envelope','FRONT — opaque lower mask and upper opening']):'Intended case/front mating interface, fastening construction unresolved'}
rows=[];unexpected=[]
for x,y in itertools.combinations(trees,2):
 hits=trees[x].overlap(trees[y]);key=frozenset([x,y]);row={'a':x,'b':y,'triangle_pairs':len(hits),'classification':compound.get(key,'not a declared compound/mating interface')};rows.append(row)
 if hits and key not in compound:unexpected.append(row)
assert hashlib.sha256(path.read_bytes()).hexdigest()==sha
r={'source_sha256':sha,'rest_pairs_checked':len(rows),'all_pairs':rows,'unexpected_surface_intersections':unexpected,'status':'UNEXPECTED_SURFACE_INTERSECTION_FAIL' if unexpected else 'NO_UNEXPECTED_REST_SURFACE_INTERSECTIONS_IN_SCOPE','limits':['Surface-only test, no full containment or continuous swept clearance','Declared compound/mating interfaces are fitted construction decisions, not factory joint validation','No contact-free claim for undeveloped internals or omitted rear equipment'],'all16VehicleGates':'OPEN'}
out.write_text(json.dumps(r,indent=2)+'\n');print('VA180_CONTACTS',len(rows),len(unexpected),flush=True)
if unexpected:raise SystemExit(2)
