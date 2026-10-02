"""Static role controls against the pinned saved run-01 object inventory."""
from copy import deepcopy
from graph_common import STATION_ROLE_TABLE, required_station_names


def check_roles(stations, inventory):
    names = required_station_names(stations, inventory)
    assert len(inventory) == 8522 and len(names) == 48
    controls = {'missing_common_role': [], 'missing_front_kingpin': [], 'wrong_station_role': []}
    common = ('carrier', 'spin', 'brake', 'drum', 'upright')

    def rejected(rows, objects, label):
        try:
            required_station_names(rows, objects)
        except AssertionError:
            return
        raise AssertionError('Invalid fixture accepted: ' + label)

    for station, roles in enumerate(STATION_ROLE_TABLE):
        for role in common:
            reduced = dict(inventory)
            del reduced[roles[role]]
            rejected(stations, reduced, f'missing {station}/{role}')
            controls['missing_common_role'].append([station, role])
        if station < 4:
            reduced = dict(inventory)
            del reduced[roles['kingpin']]
            rejected(stations, reduced, f'missing {station}/kingpin')
            controls['missing_front_kingpin'].append(station)
        for role in roles:
            other = (station + 1) % (4 if role in ('kingpin', 'joint_frame') else 8)
            wrong = deepcopy(stations)
            wrong[station][role] = STATION_ROLE_TABLE[other][role]
            rejected(wrong, inventory, f'wrong-station {station}/{role}')
            controls['wrong_station_role'].append([station, role, other])
    assert [len(controls[k]) for k in controls] == [40, 4, 48]
    return {'status': 'STATIC_STATION_ROLE_CONTROLS_PASS', 'positive_required_names': sorted(names),
            'positive_required_count': 48, 'inventory_objects': 8522,
            'negative_rejection_counts': {k: len(v) for k, v in controls.items()},
            'negative_rejected_cases': controls, 'native_execution': False}
