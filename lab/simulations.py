"""Pure, bounded simulations. No eval, subprocess, sockets, or user-code execution."""

def integer_model(value, delta, bits):
    if bits not in (8, 16, 32) or not -1_000_000 <= value <= 1_000_000 or not -1_000_000 <= delta <= 1_000_000:
        raise ValueError('Use 8, 16, or 32 bits and values between -1,000,000 and 1,000,000.')
    raw = value + delta
    unsigned = raw % (1 << bits)
    signed = unsigned - (1 << bits) if unsigned & (1 << (bits - 1)) else unsigned
    return {'mathematical_sum': raw, 'unsigned_stored': unsigned, 'signed_interpretation': signed,
            'hex': f'0x{unsigned:0{bits // 4}x}', 'binary': f'{unsigned:0{bits}b}',
            'little_endian': unsigned.to_bytes(bits // 8, 'little').hex(' '),
            'big_endian': unsigned.to_bytes(bits // 8, 'big').hex(' '),
            'scope': 'Mathematical fixed-width model. This does not make C signed overflow defined.'}


def tank_model(level, inflow, outflow, steps, trip):
    if not all(0 <= v <= 100 for v in (level, inflow, outflow, trip)) or not 1 <= steps <= 30:
        raise ValueError('Levels and flows must be 0–100; steps 1–30.')
    rows = []
    latched = False
    for step in range(steps):
        if level >= trip:
            latched = True
        actual_inflow = 0 if latched else inflow
        level = max(0, min(100, level + actual_inflow - outflow))
        rows.append({'step': step + 1, 'level': level, 'inflow': actual_inflow, 'trip_latched': latched})
    return {'trace': rows, 'scope': 'Discrete, clipped 100 L tank. Trip checks before each step and latches; no physical I/O or validated plant dynamics.'}


def modbus_model(frame):
    if len(frame) > 256:
        raise ValueError('Frame is too long.')
    try:
        data = bytes.fromhex(frame)
    except ValueError:
        raise ValueError('Use hexadecimal byte pairs.') from None
    if len(data) != 12:
        raise ValueError('This model accepts exactly a 12-byte function-03 request.')
    if int.from_bytes(data[2:4], 'big') != 0 or int.from_bytes(data[4:6], 'big') != 6 or data[7] != 3:
        raise ValueError('Expected protocol ID 0, length 6, and function 03.')
    start, quantity = int.from_bytes(data[8:10], 'big'), int.from_bytes(data[10:12], 'big')
    if not 1 <= quantity <= 125 or start + quantity > 65536:
        raise ValueError('Register range or quantity is invalid.')
    return {'transaction': int.from_bytes(data[:2], 'big'), 'unit': data[6], 'function': 'read holding registers',
            'start_address': start, 'quantity': quantity, 'scope': 'Offline parsing only. No packets are transmitted. Register addresses are zero-based.'}
