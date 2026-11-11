import math
import time
from dataclasses import dataclass
from enum import Enum
from concurrent.futures import ProcessPoolExecutor

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

@dataclass
class PlacementResult:
    positions: dict[int, tuple[float, float]]
    time_seconds: float
    num_footprints: int
    num_connections: int
    wire_euclidean: float
    wire_manhattan: float
    directive_ref: str = ""

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

class SequentialPlacer:
    def __init__(self, board, params):
        self.board = board
        self.p = params
        self.n = len(board.modules)
        
        self.edge_rect = self._get_board_bounds()
        self.inner_rect = (self.edge_rect[0] + params.A, self.edge_rect[1] + params.A,
                           self.edge_rect[2] - params.A, self.edge_rect[3] - params.A)
        
        if self.inner_rect[0] >= self.inner_rect[2] or self.inner_rect[1] >= self.inner_rect[3]:
            raise ValueError("Параметр A слишком велик для данной платы.")
        
        self.bboxes = [_get_local_bbox(m) for m in board.modules]
        self.positions = {}
        self.placed = set()
        self.unplaced = set(range(self.n))
        
        self.c, self.c_331 = self._build_connectivity()

    def _get_board_bounds(self):
        xs, ys = [], []
        for line in self.board.lines:
            if line.layer == "Edge.Cuts":
                xs.extend([line.x1, line.x2])
                ys.extend([line.y1, line.y2])
        if not xs:
            raise ValueError("На плате отсутствует контур Edge.Cuts. Нарисуйте границы платы.")
        if max(xs) - min(xs) <= 0 or max(ys) - min(ys) <= 0:
            raise ValueError("Границы платы нулевого размера.")
        return (min(xs), min(ys), max(xs), max(ys))

    def _build_connectivity(self):
        nets_by_mod = [set() for _ in range(self.n)]
        for i, mod in enumerate(self.board.modules):
            for pad_num, pad_net in mod.pad_nets.items():
                if pad_net.net_code > 0:
                    nets_by_mod[i].add(pad_net.net_code)
                    
        net_sizes = {}
        for nets in nets_by_mod:
            for net in nets:
                net_sizes[net] = net_sizes.get(net, 0) + 1
                
        lmbda = 2 
        c = [[0.0] * self.n for _ in range(self.n)]
        c_331 = [[0.0] * self.n for _ in range(self.n)]
        
        for i in range(self.n):
            for j in range(i + 1, self.n):
                common = nets_by_mod[i] & nets_by_mod[j]
                if common:
                    c[i][j] = c[j][i] = float(len(common))
                    c_331[i][j] = c_331[j][i] = sum((net_sizes[code] + lmbda) / net_sizes[code] for code in common)
        return c, c_331

    def _pick_directive(self):
        scores = []
        for i in range(self.n):
            if self.p.directive_mode == DirectiveMode.LARGEST:
                lb = self.bboxes[i]
                score = (lb[2] - lb[0]) * (lb[3] - lb[1])
            else:
                score = sum(self.c[i])
            scores.append((i, score))
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[0][0]

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
            
        lb = self.bboxes[i]
        g = self.p.C
        candidates = []
        for ix in range(math.ceil(self.inner_rect[0] / g), math.floor(self.inner_rect[2] / g) + 1):
            for iy in range(math.ceil(self.inner_rect[1] / g), math.floor(self.inner_rect[3] / g) + 1):
                gx, gy = ix * g, iy * g
                box = self._get_box(i, gx, gy)
                if self._within_board(box) and not self._collides(box, i):
                    candidates.append((gx, gy))
        return candidates

    def _calc_J(self, i):
        if self.p.j_method == JMethod.M_331:
            return max([self.c_331[i][j] for j in self.placed] + [0.0])
        elif self.p.j_method == JMethod.M_333:
            return sum(self.c[i][j] for j in self.placed)
        elif self.p.j_method == JMethod.M_335:
            placed = sum(self.c[i][j] for j in self.placed)
            unplaced = sum(self.c[i][j] for j in self.unplaced)
            return placed - unplaced
        elif self.p.j_method == JMethod.M_336:
            placed = sum(self.c[i][j] for j in self.placed)
            total = sum(self.c[i][j] for j in range(self.n) if j != i)
            return (placed / total) if total > 0 else 0.0
        return 0.0

    def _calc_F(self, i, pos):
        gx, gy = pos
        total = 0.0
        conn = self.c_331 if self.p.j_method == JMethod.M_331 else self.c
        for j in self.placed:
            w = conn[i][j]
            if w == 0:
                continue
            jx, jy = self.positions[j]
            if self.p.metric == Metric.MANHATTAN:
                d = abs(gx - jx) + abs(gy - jy)
            else:
                d = math.hypot(gx - jx, gy - jy)
            total += w * d
        return total

    def _calc_total_wire(self, metric):
        centers = [self.positions.get(i, (self.board.modules[i].x, self.board.modules[i].y)) for i in range(self.n)]
        total = 0.0
        for idxs in self._get_nets().values():
            if len(idxs) >= 2:
                pts = [centers[i] for i in idxs]
                total += _mst_length(pts, metric)
        return total

    def _get_nets(self):
        nets = {}
        for i, mod in enumerate(self.board.modules):
            for pad_num, pad_net in mod.pad_nets.items():
                if pad_net.net_code > 0:
                    nets.setdefault(pad_net.net_code, set()).add(i)
        return nets

    def run(self):
        start_time = time.perf_counter()
        if self.n == 0:
            return PlacementResult({}, 0.0, 0, 0, 0.0, 0.0, "")
            
        idx = self._pick_directive()
        pos = self._snap_to_grid(idx, *self._get_directive_pos(idx))
        if pos is None:
            raise RuntimeError(f"Корпус {self.board.modules[idx].reference} не помещается на плату.")
            
        self.positions[idx] = pos
        self.placed.add(idx)
        self.unplaced.discard(idx)

        while self.unplaced:
            j_scores = {i: self._calc_J(i) for i in self.unplaced}
            best_i = max(j_scores, key=lambda x: (j_scores[x], -x))
            
            cands = self._get_candidates(best_i)
            if not cands:
                raise RuntimeError(f"Корпус {self.board.modules[best_i].reference} не помещается на плату с заданными зазорами.")
                
            f_scores = [(p, self._calc_F(best_i, p)) for p in cands]
            best_pos = min(f_scores, key=lambda x: (x[1], x[0][1], x[0][0]))[0]
            
            self.positions[best_i] = best_pos
            self.placed.add(best_i)
            self.unplaced.discard(best_i)

        duration = time.perf_counter() - start_time
        w_euc = self._calc_total_wire(Metric.EUCLIDEAN)
        w_man = self._calc_total_wire(Metric.MANHATTAN)
        conn_count = sum(len(v) - 1 for v in self._get_nets().values() if len(v) >= 2)
        
        return PlacementResult(self.positions, duration, self.n, conn_count, w_euc, w_man, self.board.modules[idx].reference)

def _worker(job):
    board, params = job
    return SequentialPlacer(board, params).run()

def run_auto_placement(board, params, threads=1):
    if threads <= 1:
        return SequentialPlacer(board, params).run()
    jobs = [(board, params) for _ in range(threads)]
    results = []
    with ProcessPoolExecutor(max_workers=threads) as pool:
        futures = [pool.submit(_worker, job) for job in jobs]
        for fut in futures:
            results.append(fut.result())
    return min(results, key=lambda r: r.wire_euclidean)