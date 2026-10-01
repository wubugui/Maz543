"""Exact reviewed fixed-cab local-modifier eligibility only.

A successful result grants only this modifier's local dependency clause. The caller
MUST still run the reviewed whole-object, upstream-stack, Boolean operands and
ancestor audit, and bind the result to the unchanged source SHA and view layer.
Never use this for moving objects, rendering, arbitrary NODES/SUBSURF, or source
acceptance. No evaluation or mutation is performed here. Blender 4.5.13 only.
"""
from pathlib import Path
import hashlib
import json
import math
import bpy

PROFILE_SHA256 = 'e2893870a7edf3243d0f75c0fd0b4849b9f121eeec99ec2264cf3f67dae7f762'
SOURCE_SHA256 = '8e962d6dc2565974be8a0e96930606599ddbf6098780951dc96cbb9e13e3fd70'
PROFILE_PATH = Path(__file__).resolve().parents[1] / 'reference/cab-static-local-modifier-profiles-20261001.json'
NODE_TYPES = {'NodeGroupInput', 'NodeGroupOutput', 'GeometryNodeInputPosition',
              'ShaderNodeSeparateXYZ', 'ShaderNodeMath', 'ShaderNodeCombineXYZ',
              'GeometryNodeSetPosition'}
MATH_OPS = {'SUBTRACT', 'MAXIMUM', 'MULTIPLY', 'ADD'}
MOD_IGNORED = {'rna_type', 'name', 'id_data', 'node_group', 'execution_time',
               'persistent_uid', 'is_active', 'show_expanded'}
MOD_COLLECTIONS = {'bakes', 'panels', 'node_warnings'}
NODE_IGNORED = {'rna_type', 'name', 'label', 'location', 'dimensions', 'width',
                'height', 'width_hidden', 'select', 'parent', 'inputs', 'outputs',
                'internal_links', 'id_data', 'location_absolute', 'color',
                'use_custom_color', 'show_options', 'show_preview', 'hide'}
INTERFACE_EXTRA = {'hide_in_modifier': False, 'force_non_field': False,
                   'is_inspect_output': False, 'is_panel_toggle': False,
                   'layer_selection_field': False, 'default_attribute_name': '',
                   'structure_type': 'AUTO', 'default_input': 'VALUE'}

class Ineligible(ValueError):
    pass

def require(condition, reason):
    if not condition:
        raise Ineligible(reason)

def value(v):
    if v is None or isinstance(v, (str, bool, int)):
        return v
    if isinstance(v, float):
        require(math.isfinite(v), 'non-finite numeric value')
        return v
    require(not isinstance(v, bpy.types.ID), 'external ID-valued input')
    try:
        return [value(x) for x in v]
    except TypeError as exc:
        raise Ineligible('unrecognized value type') from exc

def no_custom(block, *, unsupported_ok=False):
    try:
        require(not list(block.keys()), 'custom properties or modifier inputs present')
    except TypeError:
        require(unsupported_ok, 'custom properties unreadable')

def local_id(block):
    require(block is not None, 'missing datablock')
    require(not block.library and not block.override_library and not block.is_library_indirect,
            'library-linked or overridden datablock')
    require(not block.is_evaluated and not block.is_missing and not block.is_runtime_data,
            'evaluated, missing or runtime datablock')
    require(not getattr(block, 'animation_data', None), 'datablock animation exists')

def no_id_pointers(block, *, allow=()):
    for prop in block.bl_rna.properties:
        if prop.type == 'POINTER' and prop.identifier not in {'rna_type', *allow}:
            require(not isinstance(getattr(block, prop.identifier), bpy.types.ID),
                    'ID pointer: ' + prop.identifier)

def read_profiles():
    raw = PROFILE_PATH.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == PROFILE_SHA256, 'profile bytes changed')
    profiles = json.loads(raw)
    require(profiles['source_sha256'] == SOURCE_SHA256, 'profile source mismatch')
    require(len(profiles['modifiers']) == 10 and len(profiles['node_trees']) == 8,
            'profile cardinality mismatch')
    return profiles

def socket_record(socket, direction, node):
    no_custom(socket)
    no_id_pointers(socket)
    require(socket.node == node and socket.id_data == node.id_data, 'socket owner mismatch')
    require(socket.is_output == (direction == 'outputs'), 'socket direction mismatch')
    require(not socket.is_multi_input, 'multi-input socket')
    require(socket.is_unavailable == (not socket.enabled), 'unexpected socket availability')
    require(socket.link_limit == (4095 if direction == 'outputs' or socket.bl_idname == 'NodeSocketVirtual' else 1),
            f'nonstandard socket link limit {node.name} {socket.identifier} {direction}: {socket.link_limit}')
    return {'name': socket.name, 'identifier': socket.identifier, 'type': socket.bl_idname,
            'enabled': socket.enabled, 'is_linked': socket.is_linked,
            'default_value': value(getattr(socket, 'default_value', None))}

def tree_issues_checked(tree, expected):
    local_id(tree)
    no_custom(tree)
    no_id_pointers(tree, allow={'original'})
    require(tree.bl_idname == 'GeometryNodeTree' and tree.name == expected['name'],
            'unexpected node tree identity/type')
    require(not tree.is_tool, 'tool-context node tree')
    require(len(tree.interface.items_tree) == 2, 'extra interface input/output/panel')
    iface = []
    for item in tree.interface.items_tree:
        no_custom(item)
        no_id_pointers(item)
        require(item.item_type == 'SOCKET', 'interface panel')
        for key, val in INTERFACE_EXTRA.items():
            require(getattr(item, key) == val, 'interface setting changed: ' + key)
        iface.append({key: value(getattr(item, key)) for key in
                      ['name', 'item_type', 'identifier', 'in_out', 'socket_type',
                       'attribute_domain', 'hide_value']})
    require(iface == expected['interface'], 'interface signature changed')
    require(len(tree.nodes) == 13 and len(tree.links) == 15, 'graph size changed')
    expected_nodes = {n['name']: n for n in expected['nodes']}
    require(set(n.name for n in tree.nodes) == set(expected_nodes), 'node membership changed')
    actual = {}
    for node in tree.nodes:
        exp = expected_nodes[node.name]
        require(node.bl_idname in NODE_TYPES and node.bl_idname == exp['type'],
                'unsupported or substituted node: ' + node.name)
        require(node.id_data == tree and not node.parent, 'node owner/parent changed')
        require(not node.mute, 'muted node')
        no_custom(node)
        no_id_pointers(node)
        if node.bl_idname == 'ShaderNodeMath':
            require(node.operation in MATH_OPS and not node.use_clamp,
                    'math operation or clamp changed')
        if node.bl_idname == 'NodeGroupOutput':
            require(node.is_active_output, 'inactive group output')
        props = {}
        for prop in node.bl_rna.properties:
            if prop.identifier in NODE_IGNORED:
                continue
            require(prop.identifier in exp['properties'], 'unrecognized node property')
            props[prop.identifier] = value(getattr(node, prop.identifier))
        expect_props = {k: v for k, v in exp['properties'].items() if k not in NODE_IGNORED}
        require(props == expect_props, 'node semantic properties changed: ' + node.name)
        for direction in ['inputs', 'outputs']:
            actual[(node.name, direction)] = [socket_record(s, direction, node)
                                             for s in getattr(node, direction)]
            require(actual[(node.name, direction)] == exp[direction],
                    'socket/default signature changed: ' + node.name + '.' + direction)
    links = []
    for link in tree.links:
        require(link.is_valid and not link.is_muted, 'invalid or muted link')
        require(link.from_node.id_data == tree and link.to_node.id_data == tree,
                'link crosses trees')
        require(link.from_socket.enabled and link.to_socket.enabled, 'link to disabled socket')
        require(link.from_socket.bl_idname != 'NodeSocketVirtual' and
                link.to_socket.bl_idname != 'NodeSocketVirtual', 'virtual socket link')
        links.append({'from_node': link.from_node.name, 'from_socket': link.from_socket.identifier,
                      'to_node': link.to_node.name, 'to_socket': link.to_socket.identifier,
                      'is_valid': link.is_valid, 'is_muted': link.is_muted})
    order = lambda x: (x['from_node'], x['from_socket'], x['to_node'], x['to_socket'])
    require(sorted(links, key=order) == sorted(expected['links'], key=order),
            'graph wiring changed (including cycles or bypass)')
    # Exact 15-edge reference is acyclic; equality rejects duplicates and cycles.

def modifier_issues(obj, modifier, *, fixed_context=False, depsgraph_mode='VIEWPORT'):
    """Return [] only for an exact reviewed stationary modifier; else reasons.

    No cache: audit every live RNA call. Caller must not translate exceptions into
    acceptance. This wrapper deliberately converts schema/read errors to rejection.
    """
    try:
        require(bpy.app.version[:3] == (4, 5, 13), 'unreviewed Blender version')
        require(fixed_context and depsgraph_mode == 'VIEWPORT', 'fixed viewport context required')
        require(modifier.id_data == obj and modifier in list(obj.modifiers), 'modifier owner mismatch')
        local_id(obj)
        local_id(obj.data)
        require(obj.type == 'MESH' and not obj.data.shape_keys, 'requires unkeyed mesh')
        require(not obj.constraints and not obj.rigid_body and not obj.rigid_body_constraint and
                obj.instance_type == 'NONE', 'dynamic object inputs')
        require(obj.parent_type == 'OBJECT', 'unsupported parent type')
        require(all(math.isfinite(v) for row in obj.matrix_world for v in row), 'non-finite transform')
        require(not getattr(bpy.context.scene, 'animation_data', None), 'scene animation')
        require(not bpy.context.scene.render.use_simplify, 'scene simplification is not frozen')
        for name in ['frame_change_pre', 'frame_change_post', 'depsgraph_update_pre',
                     'depsgraph_update_post']:
            require(not getattr(bpy.app.handlers, name), 'active evaluation handler: ' + name)
        profiles = read_profiles()
        matches = [p for p in profiles['modifiers'] if p['object'] == obj.name and
                   p['modifier'] == modifier.name and p['modifier_type'] == modifier.type]
        require(len(matches) == 1, 'object/modifier outside exact reviewed scope')
        profile = matches[0]
        expected = {k: v for k, v in profile['settings'].items() if k not in MOD_IGNORED}
        observed = {}
        for prop in modifier.bl_rna.properties:
            if prop.identifier in MOD_IGNORED:
                continue
            if prop.type == 'COLLECTION':
                require(prop.identifier in MOD_COLLECTIONS and not len(getattr(modifier, prop.identifier)),
                        'unreviewed modifier collection/bake state: ' + prop.identifier)
            else:
                require(prop.identifier in expected, 'unreviewed modifier setting: ' + prop.identifier)
                observed[prop.identifier] = value(getattr(modifier, prop.identifier))
        require(observed == expected, 'modifier settings changed')
        no_id_pointers(modifier, allow={'node_group'})
        if modifier.type == 'NODES':
            no_custom(modifier)
            require(modifier.node_group is not None, 'missing node group')
            tree_issues_checked(modifier.node_group, profiles['node_trees'][profile['node_tree']])
        elif modifier.type == 'SUBSURF':
            no_custom(modifier, unsupported_ok=True)
        else:
            raise Ineligible('unrecognized modifier type')
        return []
    except (Ineligible, AttributeError, KeyError, TypeError, ValueError, RuntimeError, OSError) as exc:
        return [f'{obj.name}: local static modifier rejected: {type(exc).__name__}: {exc}']
