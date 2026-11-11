class JMethod:
    M_331 = "3.3.1"
    M_333 = "3.3.3"
    M_335 = "3.3.5"
    M_336 = "3.3.6"


def calc_J_331(c_331, i, placed):
    best = 0.0
    for j in placed:
        w = c_331[i][j]
        if w > best:
            best = w
    return best


def calc_J_333(c, i, placed):
    s = 0.0
    for j in placed:
        s += c[i][j]
    return s


def calc_J_335(c, i, placed, unplaced):
    placed_sum = 0.0
    unplaced_sum = 0.0
    ci = c[i]
    for j in placed:
        placed_sum += ci[j]
    for j in unplaced:
        if j != i:
            unplaced_sum += ci[j]
    return placed_sum - unplaced_sum


def calc_J_336(c, i, placed, unplaced, n):
    placed_sum = 0.0
    total_sum = 0.0
    ci = c[i]
    for j in range(n):
        if j == i:
            continue
        total_sum += ci[j]
        if j in placed:
            placed_sum += ci[j]
    return (placed_sum / total_sum) if total_sum > 0 else 0.0


def calc_J(c, c_331, j_method, i, placed, unplaced, n):
    if j_method == JMethod.M_331:
        return calc_J_331(c_331, i, placed)
    if j_method == JMethod.M_333:
        return calc_J_333(c, i, placed)
    if j_method == JMethod.M_335:
        return calc_J_335(c, i, placed, unplaced)
    if j_method == JMethod.M_336:
        return calc_J_336(c, i, placed, unplaced, n)
    return 0.0


def pick_next_element(c, c_331, j_method, unplaced, placed, n):
    if not unplaced:
        return None, 0.0
    scores = {i: calc_J(c, c_331, j_method, i, placed, unplaced, n) for i in unplaced}
    best_i = max(scores, key=lambda x: (scores[x], -x))
    return best_i, scores[best_i]


def pick_best_position(pi, placed_positions, metric):
    gx, gy = pi
    total = 0.0
    if metric == "manhattan":
        for jx, jy, w in placed_positions:
            if w == 0:
                continue
            total += w * (abs(gx - jx) + abs(gy - jy))
    else:
        for jx, jy, w in placed_positions:
            if w == 0:
                continue
            dx = gx - jx
            dy = gy - jy
            total += w * (dx * dx + dy * dy) ** 0.5
    return total


def choose_best_candidate(element_index, candidates, placed_positions, metric):
    best_pos = None
    best_f = float("inf")
    for pi in candidates:
        f = pick_best_position(pi, placed_positions, metric)
        if f < best_f or (f == best_f and (best_pos is None or pi < best_pos)):
            best_f = f
            best_pos = pi
    return best_pos, best_f


def _is_power_net(name):
    if not name:
        return False
    up = name.upper()
    for prefix in ("GND", "VCC", "VDD", "VSS", "AGND", "DGND",
                   "+5V", "+3V3", "+3.3V", "+12V", "-5V", "-12V"):
        if up.startswith(prefix):
            return True
    return False


def compute_omega(snapshot):
    n = len(snapshot.modules)
    if n <= 1:
        return {}

    nets_modules = {}
    net_names = {}
    for i, mod in enumerate(snapshot.modules):
        for pad_net in mod['pad_nets'].values():
            if pad_net.net_code > 0:
                nets_modules.setdefault(pad_net.net_code, set()).add(i)
                net_names[pad_net.net_code] = pad_net.net_name

    omega = {}
    for code, mods in nets_modules.items():
        if _is_power_net(net_names.get(code, "")):
            omega[code] = 0.3
        else:
            omega[code] = 1.0 - len(mods) / n
    return omega


def compute_connectivity_matrix(snapshot, lmbda=2):
    n = len(snapshot.modules)
    omega = compute_omega(snapshot)

    nets_by_mod = [set() for _ in range(n)]
    for i, mod in enumerate(snapshot.modules):
        for pad_num, pad_net in mod['pad_nets'].items():
            if pad_net.net_code > 0:
                nets_by_mod[i].add(pad_net.net_code)

    net_sizes = {}
    for nets in nets_by_mod:
        for net in nets:
            net_sizes[net] = net_sizes.get(net, 0) + 1

    c = [[0.0] * n for _ in range(n)]
    c_331 = [[0.0] * n for _ in range(n)]

    for i in range(n):
        for j in range(i + 1, n):
            common = nets_by_mod[i] & nets_by_mod[j]
            if common:
                c[i][j] = c[j][i] = float(len(common))
                c_331[i][j] = c_331[j][i] = sum(
                    ((net_sizes[code] + lmbda) / net_sizes[code]) * omega.get(code, 1.0)
                    for code in common
                )
    return c, c_331


def pick_directive_element(bboxes, c, mode, directive_position):
    scores = []
    for i in range(len(bboxes)):
        if mode == "largest":
            lb = bboxes[i]
            score = (lb[2] - lb[0]) * (lb[3] - lb[1])
        else:
            score = sum(c[i])
        scores.append((i, score))
    scores.sort(key=lambda x: x[1], reverse=True)
    return scores[0][0]