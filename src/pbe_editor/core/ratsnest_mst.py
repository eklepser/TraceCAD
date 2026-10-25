import math


def build_mst_edges(points):
    n = len(points)
    if n < 2:
        return []

    in_tree = [False] * n
    in_tree[0] = True
    edges = []

    best_dist = [float('inf')] * n
    best_from = [0] * n
    for j in range(1, n):
        dx = points[j][0] - points[0][0]
        dy = points[j][1] - points[0][1]
        best_dist[j] = math.hypot(dx, dy)
        best_from[j] = 0

    for _ in range(n - 1):
        u = -1
        best = float('inf')
        for j in range(n):
            if not in_tree[j] and best_dist[j] < best:
                best = best_dist[j]
                u = j
        if u == -1:
            break

        edges.append((best_from[u], u))
        in_tree[u] = True

        ux, uy = points[u][0], points[u][1]
        for v in range(n):
            if in_tree[v]:
                continue
            vx, vy = points[v][0], points[v][1]
            d = math.hypot(vx - ux, vy - uy)
            if d < best_dist[v]:
                best_dist[v] = d
                best_from[v] = u

    return edges