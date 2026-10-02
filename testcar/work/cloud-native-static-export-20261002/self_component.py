"""Pure checks for one source-bound legacy curve/font evaluated Mesh component."""
INT_MAX = 2147483647


def source_issues(source, expected_type, saved_matrix):
    issues = []
    if expected_type not in {'CURVE', 'FONT'} or source['type'] != expected_type:
        issues.append('source_type')
    if source['pointer'] != source['original']['pointer']:
        issues.append('source_not_original')
    if source['instance_type'] != 'NONE' or source['instance_collection'] is not None:
        issues.append('source_instancing')
    if source['particle_system_count'] or 'NODES' in source['modifier_types']:
        issues.append('source_particles_or_nodes')
    if source['is_instancer']:
        issues.append('legacy_exporter_instancer_path')
    if source['matrix_world'] != saved_matrix:
        issues.append('source_saved_matrix')
    return issues


def component_issues(proof, component):
    """All inputs are copied plain values, never live iterator/RNA references."""
    issues = []
    source, evaluated = proof['source'], proof['evaluated_object']
    original = source['pointer']
    if not component['is_instance']:
        issues.append('not_generated_component')
    for role in ('object', 'instance_object', 'parent'):
        obj = component[role]
        if obj is None or obj['original']['pointer'] != original:
            issues.append(role + '_original_identity')
            continue
        if obj['matrix_world'] != proof['saved_matrix']:
            issues.append(role + '_matrix')
        if role != 'object' and (obj['pointer'] != evaluated['pointer'] or
                                obj['type'] != source['type'] or obj['data'] != evaluated['data']):
            issues.append(role + '_evaluated_identity')
    obj = component['object']
    if obj is None or obj['type'] != 'MESH' or obj['data'] is None or obj['data']['rna_type'] != 'Mesh':
        issues.append('temporary_mesh_type')
    elif obj['pointer'] in {source['pointer'], evaluated['pointer']}:
        issues.append('temporary_object_identity')
    ids = component['persistent_id']
    if len(ids) != 8 or ids[0] != 0 or any(i != INT_MAX for i in ids[1:]):
        issues.append('root_component_persistent_id')
    if component['particle_system'] is not None:
        issues.append('particle_instance')
    if component['matrix_world'] != proof['saved_matrix']:
        issues.append('component_matrix')
    if evaluated['original']['pointer'] != original or evaluated['type'] != source['type']:
        issues.append('evaluated_source_identity')
    if evaluated['matrix_world'] != proof['saved_matrix']:
        issues.append('evaluated_source_matrix')
    if component['mesh_fields'] != proof['evaluated_mesh_fields']:
        issues.append('component_native_fields')
    return issues


def count_issues(ordinary_count, components):
    # Ordinary entries may be absent when the iterator emits geometry components.
    # Their count is observed independently and is not guessed to be one.
    assert isinstance(ordinary_count, int) and ordinary_count >= 0
    return [] if len(components) == 1 else ['component_count_not_one']
