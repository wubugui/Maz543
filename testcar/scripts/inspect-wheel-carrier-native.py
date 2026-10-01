"""Read existing wheel hierarchy and related component identities, without editing."""
import bpy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT/'outputs/MAZ543A_Master.blend'
EXPECTED = '0391bfde5b7474a5f1ac4eac955f2fd8dbbb6febd33fb7d772a2cd18575edec3'
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == EXPECTED
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
bpy.context.view_layer.update()

def describe(obj):
    action = obj.animation_data.action if obj.animation_data else None
    return {'name': obj.name, 'type': obj.type,
            'parent': obj.parent.name if obj.parent else None,
            'world_matrix': [list(row) for row in obj.matrix_world],
            'children': sorted(child.name for child in obj.children),
            'constraints': [{'name': c.name, 'type': c.type} for c in obj.constraints],
            'drivers': [{'path': d.data_path, 'index': d.array_index,
                         'expression': d.driver.expression}
                        for d in obj.animation_data.drivers] if obj.animation_data else [],
            'action': {'name': action.name, 'frame_range': list(action.frame_range)} if action else None,
            'custom_properties': {key: str(obj[key]) for key in obj.keys()
                                  if key != '_RNA_UI'},
            'vertices': len(obj.data.vertices) if obj.type == 'MESH' else None}

stations = []
for i in range(4):
    carrier = bpy.data.objects[f'wheels_pivot_{1+7*i:03d}']
    spin = bpy.data.objects[f'wheels_pivot_{2+7*i:03d}']
    ancestors = []
    current = carrier
    while current:
        ancestors.append(describe(current))
        current = current.parent
    stations.append({'index':i, 'carrier':describe(carrier), 'spin':describe(spin),
                     'ancestors':ancestors,
                     'carrier_descendants':[describe(o) for o in sorted(carrier.children_recursive,key=lambda o:o.name)]})
keywords = ('suspension','steering','tie_rod','tie-rod','knuckle','upright','kingpin','halfshaft','half_shaft','S543_')
related = [describe(o) for o in bpy.data.objects if any(k.lower() in o.name.lower() for k in keywords)]
out = ROOT/'outputs/cloud-wheel-alignment-20261001/carrier-topology.json'
out.write_text(json.dumps({'source_sha256':EXPECTED, 'source_sha256_after':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
                          'stations':stations, 'related_name_matches':related,
                          'limits':'Names identify candidates only. No inference of mechanical connectivity, collision clearance or correct assembly from hierarchy.',
                          'saved_blend':False},indent=2)+'\n')
print('CARRIER_TOPOLOGY',json.dumps({'descendant_counts':[len(s['carrier_descendants']) for s in stations], 'related_name_match_count':len(related)}))
