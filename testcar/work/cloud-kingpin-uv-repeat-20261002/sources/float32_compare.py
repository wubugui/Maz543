"""Exact finite float32 comparison; signed zeros have zero numeric ULP distance."""
import math
import struct


def ordered(bits):
    return 0x80000000 - (bits & 0x7fffffff) if bits & 0x80000000 else 0x80000000 + bits


def scalar(value, bits):
    if math.isfinite(value):
        return value
    return {'nonfinite': 'NaN' if math.isnan(value) else '+Infinity' if value > 0 else '-Infinity',
            'bits_u32': bits}


def compare(before, after, width, identities=None):
    if len(before) != len(after) or len(before) % (4 * width):
        raise ValueError('Float array byte shape mismatch')
    rows = len(before) // (4 * width)
    if identities is not None and len(identities) != rows:
        raise ValueError('Identity count mismatch')
    af = struct.unpack('<' + 'f' * (len(before) // 4), before)
    bf = struct.unpack('<' + 'f' * (len(after) // 4), after)
    ai = struct.unpack('<' + 'I' * len(af), before)
    bi = struct.unpack('<' + 'I' * len(bf), after)
    result = {'rows': rows, 'components': width, 'bit_changes': 0,
              'finite_numeric_changes': 0, 'nonfinite_pairs': 0,
              'signed_zero_bit_changes': 0, 'max_finite_absolute_delta': 0.0,
              'max_finite_ulp_distance': 0,
              'ulp_convention': 'Monotone float32 bit order with signed zero collapsed; nonfinite pairs excluded.',
              'changes': []}
    for i, (a, b, ab, bb) in enumerate(zip(af, bf, ai, bi)):
        finite = math.isfinite(a) and math.isfinite(b)
        if not finite:
            result['nonfinite_pairs'] += 1
        if ab == bb:
            continue
        result['bit_changes'] += 1
        row, component = divmod(i, width)
        change = {'row': row, 'component': component,
                  'before': scalar(a, ab), 'after': scalar(b, bb),
                  'before_bits_u32': ab, 'after_bits_u32': bb}
        if identities is not None:
            change['identity'] = identities[row]
        if finite:
            delta, ulp = abs(a - b), abs(ordered(ab) - ordered(bb))
            result['finite_numeric_changes'] += a != b
            result['signed_zero_bit_changes'] += a == b == 0.0
            result['max_finite_absolute_delta'] = max(result['max_finite_absolute_delta'], delta)
            result['max_finite_ulp_distance'] = max(result['max_finite_ulp_distance'], ulp)
            change.update(absolute_delta=delta, ulp_distance=ulp)
        result['changes'].append(change)
    return result


def require_same_topology(before, after):
    if before.keys() != after.keys() or any(before[k] != after[k] for k in before):
        raise ValueError('Topology differs; loop-index comparison is not qualified')


def self_test():
    pack = lambda *a: struct.pack('<' + 'f' * len(a), *a)
    bits = lambda *a: struct.pack('<' + 'I' * len(a), *a)
    x = compare(bits(0x3f800000), bits(0x3f800001), 1)
    assert x['max_finite_ulp_distance'] == 1 and x['max_finite_absolute_delta'] == 2 ** -23
    x = compare(bits(0xbf800001), bits(0xbf800000), 1)
    assert x['max_finite_ulp_distance'] == 1
    x = compare(pack(-0.0), pack(0.0), 1)
    assert x['bit_changes'] == x['signed_zero_bit_changes'] == 1
    assert x['finite_numeric_changes'] == x['max_finite_ulp_distance'] == 0
    x = compare(bits(0x80000001), bits(0x00000001), 1)
    assert x['max_finite_ulp_distance'] == 2
    x = compare(bits(0x7fc00001, 0x7f800000, 0xff800000), bits(0x7fc00002, 0x7f800000, 0x3f800000), 1)
    assert x['nonfinite_pairs'] == 3 and x['bit_changes'] == 2 and not x['finite_numeric_changes']
    assert compare(pack(1.0, 2.0), pack(1.0, 2.0), 2)['bit_changes'] == 0
    for callback in [lambda: compare(pack(1), pack(1, 2), 1),
                     lambda: compare(pack(1, 2), pack(1, 2), 2, []),
                     lambda: require_same_topology({'loops': b'01'}, {'loops': b'10'}),
                     lambda: require_same_topology({'loops': b'01'}, {'loops': b'01', 'extra': b''})]:
        try:
            callback()
        except ValueError:
            pass
        else:
            raise AssertionError('Negative control not rejected')
    require_same_topology({'loops': b'01'}, {'loops': b'01'})
    return {'status': 'PASS_PURE_NUMERIC_CONTROLS', 'cases': 11, 'native_engine_run': False}


if __name__ == '__main__':
    import json
    print(json.dumps(self_test(), indent=2))
