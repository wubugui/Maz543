"""Inextensible circular-wire helix; fitted dimensions, no elastic stress solve.

Two linear mesh displacement fields reproduce the analytic helix exactly when
their weights are evaluated nonlinearly. Compression changes pitch and the
small radius increase preserves centreline length. No object scale is used.
"""
import math

PITCH_KEY = 'Pitch'
RADIUS_KEY = 'Radius'
STEPS = 320
SIDES = 16

def parameters(spec, travel):
    length = spec['releaseSpringLength']
    radius = spec['releaseSpringRadius']
    sweep = spec['releaseSpringTurns'] * math.tau
    arc = math.hypot(length, radius*sweep)
    travel = max(0, min(spec['clutchTravel'], travel))
    current_length = length-travel
    current_radius = math.sqrt(arc*arc-current_length*current_length)/sweep
    end_radius = math.sqrt(arc*arc-(length-spec['clutchTravel'])**2)/sweep
    return current_length, current_radius, arc, end_radius

def weights(spec, travel):
    length, radius, _, end_radius = parameters(spec, travel)
    return ((spec['releaseSpringLength']-length)/spec['clutchTravel'],
            (radius-spec['releaseSpringRadius'])/(end_radius-spec['releaseSpringRadius']))

def vertices(spec, length, radius, arc):
    """Blender coordinates. Each wire section is normal to its helix tangent."""
    result=[]; sweep=spec['releaseSpringTurns']*math.tau; wire=spec['releaseSpringWire']
    for i in range(STEPS+1):
        t=i/STEPS; theta=t*sweep; sn=math.sin(theta); cs=math.cos(theta)
        for j in range(SIDES):
            phi=j/SIDES*math.tau; a=wire*math.cos(phi); b=wire*math.sin(phi)
            result.append((length*t-b*radius*sweep/arc,
                           -(radius+a)*sn-b*length*cs/arc,
                           (radius+a)*cs-b*length*sn/arc))
    return result

def apply_travel(coil, spec, travel):
    for name,value in zip((PITCH_KEY,RADIUS_KEY),weights(spec,travel)):
        coil.data.shape_keys.key_blocks[name].value=value

def bake_springs(frames, spec):
    import bpy
    for side in range(2):
        coil=bpy.data.objects.get(f'COOL_release_spring_{side}')
        if not coil or not coil.get('parametricSpring'): continue
        keys=coil.data.shape_keys; keys.animation_data_clear()
        name=f'COOL_spring_{side}'
        values=[weights(spec,f['pose'][name]['springTravel']) for f in frames]
        for key_index,key_name in enumerate((PITCH_KEY,RADIUS_KEY)):
            key=keys.key_blocks[key_name]
            # Let Blender create a correctly typed Key action/slot once.
            key.value=values[0][key_index]; key.keyframe_insert(data_path='value',frame=frames[0]['frame'])
            action=keys.animation_data.action
            fc=next(fc for fc in action.fcurves if fc.data_path==f'key_blocks["{key_name}"].value')
            fc.keyframe_points.clear(); fc.keyframe_points.add(len(frames))
            fc.keyframe_points.foreach_set('co',[v for f,w in zip(frames,values) for v in (f['frame'],w[key_index])])
            for point in fc.keyframe_points: point.interpolation='LINEAR'
            fc.update()
