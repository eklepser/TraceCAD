import math
import time
from dataclasses import dataclass
from enum import Enum
from multiprocessing import Pool

from pbe_editor.core import sequential_algorithm as algo


class Metric(Enum):
    EUCLIDEAN = "euclidean"
    MANHATTAN = "manhattan"


class DirectiveMode(Enum):
    LARGEST = "largest"
    MOST_CONNECTED = "most_connected"


class DirectivePosition(Enum):
    CENTER = "center"
    TOP_LEFT = "top_left"
    BOTTOM_LEFT = "bottom_left"


class JMethod(Enum):
    M_331 = "3.3.1"
    M_333 = "3.3.3"
    M_335 = "3.3.5"
    M_336 = "3.3.6"


@dataclass
class PlacementParams:
    A: float = 2.0
    B: float = 2.0
    C: float = 1.25
    metric: Metric = Metric.EUCLIDEAN
    j_method: JMethod = JMethod.M_335
    directive_mode: DirectiveMode = DirectiveMode.LARGEST
    directive_position: DirectivePosition = DirectivePosition.CENTER
    threads: int = 1


@dataclass
class PlacementResult:
    positions: dict[int, tuple[float, float]]
    time_seconds: float
    num_footprints: int
    num_connections: int
    wire_euclidean: float
    wire_manhattan: float
    directive_ref: str = ""
    threads_used: int = 1


def _J_task(args):
    c, c_331, jm, i, placed, unplaced, n = args
    return i, algo.calc_J(c, c_331, jm, i, placed, unplaced, n)


def _F_task(args):
    conn_row, candidates, placed_positions, metric_name = args
    return [
        (gx, gy, algo.pick_best_position((gx, gy), placed_positions, metric_name))
        for gx, gy in candidates
    ]


def _arc_points(cx, cy, sx, sy, angle_deg, segments=16):
    r = math.hypot(sx - cx, sy - cy)
    if r < 1e-9:
        return [(cx, cy), (sx, sy)]
    a1 = math.atan2(sy - cy, sx - cx)
    sweep = math.radians(angle_deg)
    pts = []
    for i in range(segments + 1):
        t = i / segments
        a = a1 + t * sweep
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def _get_local_bbox(module):
    fp = module.footprint
    xs, ys = [], []
    for pad in fp.pads:
        xs.extend([pad.x - pad.width / 2, pad.x + pad.width / 2])
        ys.extend([pad.y - pad.height / 2, pad.y + pad.height / 2])
    for line in fp.lines:
        xs.extend([line.x, line.x2])
        ys.extend([line.y, line.y2])
    for circle in fp.circles:
        xs.extend([circle.x - circle.radius, circle.x + circle.radius])
        ys.extend([circle.y - circle.radius, circle.y + circle.radius])
    for arc in fp.arcs:
        for px, py in _arc_points(arc.x, arc.y, arc.sx, arc.sy, arc.angle, 16):
            xs.append(px)
            ys.append(py)
    for text in fp.texts:
        if getattr(text, 'text_type', None) == 0:
            continue
        xs.append(text.x)
        ys.append(text.y)
    if not xs:
        return (-1.0, -1.0, 1.0, 1.0)
    return (min(xs), min(ys), max(xs), max(ys))


def _mst_length(points, metric):
    n = len(points)
    if n < 2:
        return 0.0
    in_tree = [False] * n
    min_d = [float('inf')] * n
    min_d[0] = 0.0
    total = 0.0
    for _ in range(n):
        best, best_d = -1, float('inf')
        for i in range(n):
            if not in_tree[i] and min_d[i] < best_d:
                best_d, best = min_d[i], i
        if best == -1:
            break
        in_tree[best] = True
        total += best_d
        bx, by = points[best]
        for i in range(n):
            if in_tree[i]:
                continue
            ix, iy = points[i]
            d = abs(ix - bx) + abs(iy - by) if metric == Metric.MANHATTAN else math.hypot(ix - bx, iy - by)
            if d < min_d[i]:
                min_d[i] = d
    return total


def _get_board_edge_rect(board):
    xs, ys = [], []
    for line in board.lines:
        if line.layer == "Edge.Cuts":
            xs.extend([line.x1, line.x2])
            ys.extend([line.y1, line.y2])
    if not xs:
        raise ValueError("На плате отсутствует контур Edge.Cuts. Нарисуйте границы платы.")
    if max(xs) - min(xs) <= 0 or max(ys) - min(ys) <= 0:
        raise ValueError("Границы платы нулевого размера.")
    return (min(xs), min(ys), max(xs), max(ys))


class _BoardSnapshot:
    def __init__(self, board):
        self.edge_rect = _get_board_edge_rect(board)
        self.modules = []
        for m in board.modules:
            self.modules.append({
                'uid': m.uid,
                'reference': m.reference,
                'x': m.x,
                'y': m.y,
                'pad_nets': dict(m.pad_nets),
                'bbox': _get_local_bbox(m),
            })


class SequentialPlacer:
    def __init__(self, snapshot, params):
        self.snap = snapshot
        self.p = params
        self.n = len(snapshot.modules)

        self.edge_rect = snapshot.edge_rect
        self.inner_rect = (self.edge_rect[0] + params.A, self.edge_rect[1] + params.A,
                           self.edge_rect[2] - params.A, self.edge_rect[3] - params.A)

        if self.inner_rect[0] >= self.inner_rect[2] or self.inner_rect[1] >= self.inner_rect[3]:
            raise ValueError("Параметр A слишком велик для данной платы.")

        self.bboxes = [m['bbox'] for m in snapshot.modules]
        self.positions = {}
        self.placed = set()
        self.unplaced = set(range(self.n))

        self.c, self.c_331 = algo.compute_connectivity_matrix(snapshot)

        area = (self.inner_rect[2] - self.inner_rect[0]) * (self.inner_rect[3] - self.inner_rect[1])
        cell_count = max(1.0, area / (params.C * params.C))
        self._work_estimate = cell_count * self.n * self.n

        self._pool = None
        self.threads_used = 1
        if params.threads > 1 and self._parallel_worthwhile():
            try:
                self._pool = Pool(processes=params.threads)
                self.threads_used = params.threads
            except Exception:
                self._pool = None
                self.threads_used = 1

    def _parallel_worthwhile(self):
        return self._work_estimate >= 5_000_000

    def _shutdown_pool(self):
        if self._pool is not None:
            self._pool.terminate()
            self._pool.join()
            self._pool = None

    def _pick_directive(self):
        mode = "largest" if self.p.directive_mode == DirectiveMode.LARGEST else "most_connected"
        return algo.pick_directive_element(self.bboxes, self.c, mode, self.p.directive_position.value)

    def _get_directive_pos(self, i):
        lb = self.bboxes[i]
        if self.p.directive_position == DirectivePosition.CENTER:
            cx = (self.edge_rect[0] + self.edge_rect[2]) / 2.0
            cy = (self.edge_rect[1] + self.edge_rect[3]) / 2.0
            return (cx - (lb[0] + lb[2]) / 2, cy - (lb[1] + lb[3]) / 2)
        elif self.p.directive_position == DirectivePosition.TOP_LEFT:
            ix = self.inner_rect[0]
            iy = self.inner_rect[3]
            return (ix - lb[0], iy - lb[3])
        else:
            ix = self.inner_rect[0]
            iy = self.inner_rect[1]
            return (ix - lb[0], iy - lb[1])

    def _snap_to_grid(self, i, gx, gy):
        lb = self.bboxes[i]
        g = self.p.C
        ix_lo = math.ceil((self.inner_rect[0] - lb[0]) / g - 1e-9)
        ix_hi = math.floor((self.inner_rect[2] - lb[2]) / g + 1e-9)
        iy_lo = math.ceil((self.inner_rect[1] - lb[1]) / g - 1e-9)
        iy_hi = math.floor((self.inner_rect[3] - lb[3]) / g + 1e-9)
        if ix_lo > ix_hi or iy_lo > iy_hi:
            return None
        ix = max(ix_lo, min(ix_hi, round(gx / g)))
        iy = max(iy_lo, min(iy_hi, round(gy / g)))
        return (ix * g, iy * g)

    def _get_box(self, i, gx, gy):
        lb = self.bboxes[i]
        return (gx + lb[0], gy + lb[1], gx + lb[2], gy + lb[3])

    def _collides(self, box, exclude):
        for j in self.placed:
            if j == exclude:
                continue
            ob = self._get_box(j, *self.positions[j])
            if (box[0] < ob[2] + self.p.B and box[2] > ob[0] - self.p.B and
                    box[1] < ob[3] + self.p.B and box[3] > ob[1] - self.p.B):
                return True
        return False

    def _within_board(self, box):
        return (box[0] >= self.inner_rect[0] - 1e-9 and box[1] >= self.inner_rect[1] - 1e-9 and
                box[2] <= self.inner_rect[2] + 1e-9 and box[3] <= self.inner_rect[3] + 1e-9)

    def _get_candidates(self, i):
        if not self.placed:
            pos = self._snap_to_grid(i, *self._get_directive_pos(i))
            return [pos] if pos else []
        g = self.p.C
        candidates = []
        ix_range = range(int(math.ceil(self.inner_rect[0] / g)), int(math.floor(self.inner_rect[2] / g)) + 1)
        iy_range = range(int(math.ceil(self.inner_rect[1] / g)), int(math.floor(self.inner_rect[3] / g)) + 1)
        for ix in ix_range:
            for iy in iy_range:
                gx, gy = ix * g, iy * g
                box = self._get_box(i, gx, gy)
                if self._within_board(box) and not self._collides(box, i):
                    candidates.append((gx, gy))
        return candidates

    def _get_placed_positions(self, conn_row):
        return [(self.positions[j][0], self.positions[j][1], conn_row[j]) for j in self.placed]

    def _compute_J_scores(self):
        items = list(self.unplaced)
        if not items:
            return {}
        jm = self.p.j_method.value
        if self._pool is None or len(items) < 4:
            return {i: algo.calc_J(self.c, self.c_331, jm, i, self.placed, self.unplaced, self.n)
                    for i in items}
        jobs = [(self.c, self.c_331, jm, i, self.placed, self.unplaced, self.n) for i in items]
        chunk = max(1, len(jobs) // (self.p.threads * 4))
        results = self._pool.map(_J_task, jobs, chunksize=chunk)
        return dict(results)

    def _compute_F_scores(self, best_i, cands):
        if not cands:
            return []
        conn = self.c_331 if self.p.j_method == JMethod.M_331 else self.c
        conn_row = conn[best_i]
        placed_positions = self._get_placed_positions(conn_row)
        metric_name = "manhattan" if self.p.metric == Metric.MANHATTAN else "euclidean"
        work = len(cands) * max(1, len(placed_positions))
        if self._pool is None or work < 2000:
            return [
                (p, algo.pick_best_position(p, placed_positions, metric_name))
                for p in cands
            ]
        n_chunks = self.p.threads * 4
        chunk_size = max(1, (len(cands) + n_chunks - 1) // n_chunks)
        chunks = [cands[k:k + chunk_size] for k in range(0, len(cands), chunk_size)]
        jobs = [(conn_row, ch, placed_positions, metric_name) for ch in chunks]
        results = self._pool.map(_F_task, jobs, chunksize=1)
        out = []
        for ch in results:
            for gx, gy, v in ch:
                out.append(((gx, gy), v))
        return out

    def _calc_total_wire(self, metric):
        centers = [self.positions.get(i, (self.snap.modules[i]['x'], self.snap.modules[i]['y'])) for i in range(self.n)]
        total = 0.0
        for idxs in self._get_nets().values():
            if len(idxs) >= 2:
                pts = [centers[i] for i in idxs]
                total += _mst_length(pts, metric)
        return total

    def _get_nets(self):
        nets = {}
        for i, mod in enumerate(self.snap.modules):
            for pad_num, pad_net in mod['pad_nets'].items():
                if pad_net.net_code > 0:
                    nets.setdefault(pad_net.net_code, set()).add(i)
        return nets

    def run(self):
        start_time = time.perf_counter()
        if self.n == 0:
            return PlacementResult({}, 0.0, 0, 0, 0.0, 0.0, "", self.threads_used)
        try:
            idx = self._pick_directive()
            pos = self._snap_to_grid(idx, *self._get_directive_pos(idx))
            if pos is None:
                ref = self.snap.modules[idx]['reference']
                raise RuntimeError(f"Корпус {ref} не помещается на плату.")
            self.positions[idx] = pos
            self.placed.add(idx)
            self.unplaced.discard(idx)

            while self.unplaced:
                j_scores = self._compute_J_scores()
                best_i = max(j_scores, key=lambda x: (j_scores[x], -x))

                cands = self._get_candidates(best_i)
                if not cands:
                    ref = self.snap.modules[best_i]['reference']
                    raise RuntimeError(f"Корпус {ref} не помещается на плату с заданными зазорами.")

                f_scores = self._compute_F_scores(best_i, cands)
                best_pos = min(f_scores, key=lambda x: (x[1], x[0][1], x[0][0]))[0]

                self.positions[best_i] = best_pos
                self.placed.add(best_i)
                self.unplaced.discard(best_i)
        finally:
            self._shutdown_pool()

        duration = time.perf_counter() - start_time
        w_euc = self._calc_total_wire(Metric.EUCLIDEAN)
        w_man = self._calc_total_wire(Metric.MANHATTAN)
        conn_count = sum(len(v) - 1 for v in self._get_nets().values() if len(v) >= 2)

        return PlacementResult(
            self.positions, duration, self.n, conn_count, w_euc, w_man,
            self.snap.modules[idx]['reference'], self.threads_used
        )


def _snapshot_wire_lengths(snapshot):
    placer = SequentialPlacer.__new__(SequentialPlacer)
    placer.snap = snapshot
    placer.n = len(snapshot.modules)
    placer.positions = {}
    placer.placed = set()
    placer.unplaced = set(range(placer.n))
    return placer._calc_total_wire(Metric.EUCLIDEAN), placer._calc_total_wire(Metric.MANHATTAN)


def run_auto_placement(board, params, threads=1):
    snapshot = _BoardSnapshot(board)
    before_euc, before_man = _snapshot_wire_lengths(snapshot)

    params.threads = threads
    result = SequentialPlacer(snapshot, params).run()

    return result, before_euc, before_man