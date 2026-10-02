"""Exact saved-frame neutral torsion schema; pure data, no Blender dependency."""
TORSION_NAMES = tuple(f'S543_{station}_{arm}_torsion_bar'
                      for station in range(8) for arm in ('lower', 'upper'))


def neutral_schema_issues(row):
    issues = []
    def check(ok, field):
        if not ok:
            issues.append(field)
    name = row['name']
    check(name in TORSION_NAMES, 'object_not_in_exact16')
    check(row['type'] == 'MESH', 'not_mesh')
    check(row['mesh_name'] == name + '_mesh', 'mesh_identity')
    check(row['data_object_users'] == [name], 'shared_mesh')
    check(row['modifiers'] == [], 'modifier_present')
    check(row['counts'] == [800, 1568, 3072, 768], 'topology_counts')
    check(row['show_only_shape_key'] is False, 'show_only_shape_key')
    check(row['use_relative'] is True, 'absolute_shape_keys')
    check(row['reference_key'] == 'Basis', 'reference_key')
    keys = row['keys']
    check([k['name'] for k in keys] == ['Basis', 'Twist_-1', 'Twist_1'], 'key_schema')
    for key in keys:
        check(key['value'] == 0.0, 'nonzero_key:' + key['name'])
        check(key['relative_key'] == 'Basis', 'relative_key:' + key['name'])
        check(key['mute'] is False, 'muted_key:' + key['name'])
        check(key['vertex_group'] == '', 'key_vertex_group:' + key['name'])
        check(key['points'] == 800, 'key_point_count:' + key['name'])
    animation = row['animation']
    if animation is not None:
        check(not animation['drivers'], 'shape_key_drivers')
        check(not animation['nla'], 'shape_key_nla')
    return issues
