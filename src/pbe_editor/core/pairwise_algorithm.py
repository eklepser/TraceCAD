import math


def calc_connectivity_matrix(snapshot):
    n = len(snapshot.modules)
    c = [[0.0] * n for _ in range(n)]
    nets = {}
    for i, mod in enumerate(snapshot.modules):
        for pad_net in mod['pad_nets'].values():
            if pad_net.net_code <= 0 or not pad_net.net_name:
                continue
            nets.setdefault(pad_net.net_code, set()).add(i)
    for mod_set in nets.values():
        m_list = list(mod_set)
        for idx1 in range(len(m_list)):
            for idx2 in range(idx1 + 1, len(m_list)):
                u, v = m_list[idx1], m_list[idx2]
                c[u][v] += 1.0
                c[v][u] += 1.0
    return c


def pick_directive_element(bboxes, c, mode):
    if mode == "none":
        return None
    n = len(bboxes)
    if n == 0:
        return None
    if mode == "largest":
        return max(
            range(n),
            key=lambda i: ((bboxes[i][2] - bboxes[i][0]) * (bboxes[i][3] - bboxes[i][1]), -i),
        )
    return max(range(n), key=lambda i: (sum(c[i]), -i))


def distance(p1, p2, metric_name):
    dx = abs(p1[0] - p2[0])
    dy = abs(p1[1] - p2[1])
    if metric_name == "manhattan":
        return dx + dy
    return math.hypot(dx, dy)


def _node_distances(nodes, metric_name):
    m = len(nodes)
    d = [[0.0] * m for _ in range(m)]
    for i in range(m):
        for j in range(i + 1, m):
            dist = distance(nodes[i], nodes[j], metric_name)
            d[i][j] = dist
            d[j][i] = dist
    return d


def solve_version_1(c, nodes, assignment, fixed_elem, metric_name, max_iters=200):
    m = len(nodes)
    d_mat = _node_distances(nodes, metric_name)

    r = [[0.0] * m for _ in range(m)]
    for u in range(m):
        eu = assignment[u]
        if eu < 0:
            continue
        for v in range(u + 1, m):
            ev = assignment[v]
            if ev < 0:
                continue
            val = c[eu][ev]
            r[u][v] = val
            r[v][u] = val

    p = [[0.0] * m for _ in range(m)]
    for i in range(m):
        for j in range(m):
            s = 0.0
            for k in range(m):
                s += r[i][k] * d_mat[j][k]
            p[i][j] = s

    for _ in range(max_iters):
        candidates = []
        for i in range(m):
            if fixed_elem is not None and assignment[i] == fixed_elem:
                continue
            for j in range(i + 1, m):
                if fixed_elem is not None and assignment[j] == fixed_elem:
                    continue
                if assignment[i] < 0 and assignment[j] < 0:
                    continue
                q_ij = (p[i][j] - p[i][i]) + (p[j][i] - p[j][j])
                dl_ij = 2.0 * r[i][j] * d_mat[i][j] + q_ij
                if dl_ij < -1e-9:
                    candidates.append((dl_ij, i, j))

        if not candidates:
            break

        candidates.sort(key=lambda x: (x[0], x[1], x[2]))

        selected = []
        used_nodes = set()
        for dl_ij, i, j in candidates:
            if i in used_nodes or j in used_nodes:
                continue
            if any(r[i][u] > 0 or r[i][v] > 0 or r[j][u] > 0 or r[j][v] > 0 for u, v in selected):
                continue
            selected.append((i, j))
            used_nodes.add(i)
            used_nodes.add(j)

        if not selected:
            break

        for i, j in selected:
            assignment[i], assignment[j] = assignment[j], assignment[i]
            for k in range(m):
                r[i][k], r[j][k] = r[j][k], r[i][k]
            for k in range(m):
                r[k][i], r[k][j] = r[k][j], r[k][i]

        for i in range(m):
            for j in range(m):
                s = 0.0
                for k in range(m):
                    s += r[i][k] * d_mat[j][k]
                p[i][j] = s

    return assignment


def solve_version_2(c, nodes, assignment, fixed_elem, metric_name, max_iters=200):
    n = len(c)
    m = len(nodes)
    d_mat = _node_distances(nodes, metric_name)

    elem_to_node = [-1] * n
    for u, e in enumerate(assignment):
        if e >= 0:
            elem_to_node[e] = u

    order = sorted(range(n), key=lambda e: (-sum(c[e]), e))

    for _ in range(max_iters):
        improved_any = False
        for idx_k, ei in enumerate(order):
            if fixed_elem is not None and ei == fixed_elem:
                continue
            h = elem_to_node[ei]

            best_df = 0.0
            best_target_node = -1

            for idx_m in range(idx_k + 1, n):
                ej = order[idx_m]
                if fixed_elem is not None and ej == fixed_elem:
                    continue
                k = elem_to_node[ej]

                df = 0.0
                for s in range(n):
                    if s == ei or s == ej:
                        continue
                    ps = elem_to_node[s]
                    df += (c[ei][s] - c[ej][s]) * (d_mat[h][ps] - d_mat[k][ps])

                if df > best_df + 1e-9:
                    best_df = df
                    best_target_node = k

            for u in range(m):
                if assignment[u] != -1:
                    continue
                df = 0.0
                for s in range(n):
                    if s == ei:
                        continue
                    ps = elem_to_node[s]
                    df += c[ei][s] * (d_mat[h][ps] - d_mat[u][ps])
                if df > best_df + 1e-9:
                    best_df = df
                    best_target_node = u

            if best_target_node != -1:
                k = best_target_node
                ej = assignment[k]
                assignment[h] = ej
                assignment[k] = ei
                elem_to_node[ei] = k
                if ej >= 0:
                    elem_to_node[ej] = h
                improved_any = True

        if not improved_any:
            break

    return assignment