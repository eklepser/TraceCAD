import math


def arc_radius(cx, cy, sx, sy):
    return math.hypot(sx - cx, sy - cy)


def arc_start_angle(cx, cy, sx, sy):
    return math.atan2(sy - cy, sx - cx)


def arc_sample_points(cx, cy, sx, sy, angle_deg, segments=64):
    R = arc_radius(cx, cy, sx, sy)
    if R < 1e-9:
        return [(cx, cy), (sx, sy)]
    a1 = arc_start_angle(cx, cy, sx, sy)
    sweep = math.radians(angle_deg)
    pts = []
    for i in range(segments + 1):
        t = i / segments
        a = a1 + t * sweep
        pts.append((cx + R * math.cos(a), cy + R * math.sin(a)))
    return pts