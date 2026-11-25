import math
import time
from dataclasses import dataclass
from enum import Enum

from pbe_editor.core import pairwise_algorithm as algo
from pbe_editor.core.autoplacer import (
    Metric,
    OptimizationMode,
    _BoardSnapshot,
    _mst_length,
    _rotate_offset,
    _snapshot_wire_lengths,
)


class PairwiseAlgoVersion(Enum):
    VERSION_1 = "version_1"
    VERSION_2 = "version_2"


class PairwiseDirectiveMode(Enum):
    NONE = "none"
    LARGEST = "largest"
    MOST_CONNECTED = "most_connected"


@dataclass
class PairwiseParams:
    A: float = 2.0
    B: float = 2.0
    C: float = 1.25
    algo_version: PairwiseAlgoVersion = PairwiseAlgoVersion.VERSION_1
    metric: Metric = Metric.EUCLIDEAN
    directive_mode: PairwiseDirectiveMode = PairwiseDirectiveMode.NONE
    optimization_mode: OptimizationMode = OptimizationMode.D_C2


@dataclass
class PairwiseResult:
    positions: dict[int, tuple[float, float]]
    time_seconds: float
    num_footprints: int
    num_connections: int
    wire_euclidean: float
    wire_manhattan: float
    directive_ref: str = ""
    board_width: float = 0.0
    board_length: float = 0.0
    pair_wire_euclidean: float = 0.0
    pair_wire_manhattan: float = 0.0
    pair_time_seconds: float = 0.0
    opt_time_seconds: float = 0.0
    shifted_count: int = 0


class PairwisePlacer:
    def __init__(self, snapshot, params):
        self.snap = snapshot
        self.p = params
        self.n = len(snapshot.modules)

        self.edge_rect = snapshot.edge_rect
        self.inner_rect = (
            self.edge_rect[0] + params.A,
            self.edge_rect[1] + params.A,
            self.edge_rect[2] - params.A,
            self.edge_rect[3] - params.A,
        )

        if self.inner_rect[0] >= self.inner_rect[2] or self.inner_rect[1] >= self.inner_rect[3]:
            raise ValueError("Параметр A слишком велик для данной платы.")

        self.bboxes = [m['bbox'] for m in snapshot.modules]
        self.center_offsets = [m['center_offset'] for m in snapshot.modules]
        self.positions = {}
        self.shifted_count = 0

        self.c = algo.calc_connectivity_matrix(snapshot)

    def _get_box(self, i, gx, gy):
        lb = self.bboxes[i]
        return (gx + lb[0], gy + lb[1], gx + lb[2], gy + lb[3])

    def _within_board(self, box):
        return (
            box[0] >= self.inner_rect[0] - 1e-9
            and box[1] >= self.inner_rect[1] - 1e-9
            and box[2] <= self.inner_rect[2] + 1e-9
            and box[3] <= self.inner_rect[3] + 1e-9
        )

    def _collides_with(self, box, placed_dict, exclude=-1):
        for j, (px, py) in placed_dict.items():
            if j == exclude:
                continue
            ob = self._get_box(j, px, py)
            if (
                box[0] < ob[2] + self.p.B - 1e-9
                and box[2] > ob[0] - self.p.B + 1e-9
                and box[1] < ob[3] + self.p.B - 1e-9
                and box[3] > ob[1] - self.p.B + 1e-9
            ):
                return True
        return False

    def _clamp_to_inner(self, i, gx, gy):
        lb = self.bboxes[i]
        min_gx = self.inner_rect[0] - lb[0]
        max_gx = self.inner_rect[2] - lb[2]
        min_gy = self.inner_rect[1] - lb[1]
        max_gy = self.inner_rect[3] - lb[3]
        if min_gx > max_gx + 1e-9 or min_gy > max_gy + 1e-9:
            ref = self.snap.modules[i]['reference']
            raise RuntimeError(f"Корпус {ref} не помещается на плату с заданным отступом A.")
        nx = max(min_gx, min(max_gx, gx))
        ny = max(min_gy, min(max_gy, gy))
        return (nx, ny)

    def _snap_near(self, i, gx, gy):
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

    def _prepare_initial_positions(self):
        shifted = 0
        raw_pos = {}
        for i, mod in enumerate(self.snap.modules):
            ox, oy = mod['x'], mod['y']
            box = self._get_box(i, ox, oy)
            if not self._within_board(box):
                nx, ny = self._clamp_to_inner(i, ox, oy)
                raw_pos[i] = (nx, ny)
                shifted += 1
            else:
                raw_pos[i] = (ox, oy)
        self.shifted_count = shifted
        return raw_pos

    def _build_regular_slots(self, raw_pos, fixed_elem):
        max_w = max((b[2] - b[0]) for b in self.bboxes)
        max_h = max((b[3] - b[1]) for b in self.bboxes)

        g = self.p.C
        step_x = max(g, math.ceil((max_w + self.p.B) / g - 1e-9) * g)
        step_y = max(g, math.ceil((max_h + self.p.B) / g - 1e-9) * g)

        usable_w = self.inner_rect[2] - self.inner_rect[0]
        usable_h = self.inner_rect[3] - self.inner_rect[1]

        cols = max(1, int(math.floor((usable_w - max_w) / step_x + 1e-9)) + 1)
        rows = max(1, int(math.floor((usable_h - max_h) / step_y + 1e-9)) + 1)

        if cols * rows < self.n:
            step_x = max(g * 0.25, (usable_w - max_w) / max(1, math.ceil(math.sqrt(self.n)) - 1))
            step_y = max(g * 0.25, (usable_h - max_h) / max(1, math.ceil(math.sqrt(self.n)) - 1))
            cols = max(1, int(math.floor((usable_w - max_w) / step_x + 1e-9)) + 1)
            rows = max(1, int(math.floor((usable_h - max_h) / step_y + 1e-9)) + 1)

        total_grid_w = max_w + (cols - 1) * step_x
        total_grid_h = max_h + (rows - 1) * step_y
        start_x = self.inner_rect[0] + max(0.0, (usable_w - total_grid_w) / 2.0) + max_w / 2.0
        start_y = self.inner_rect[1] + max(0.0, (usable_h - total_grid_h) / 2.0) + max_h / 2.0

        slot_centers = []
        for r in range(rows):
            for col in range(cols):
                slot_centers.append((start_x + col * step_x, start_y + r * step_y))

        if len(slot_centers) < self.n:
            raise RuntimeError("Недостаточно установочных позиций на плате для размещения всех элементов.")

        elem_centers = {}
        for i in range(self.n):
            px, py = raw_pos[i]
            cx, cy = self.center_offsets[i]
            elem_centers[i] = (px + cx, py + cy)

        assignment = [-1] * len(slot_centers)
        used_slots = set()

        order = list(range(self.n))
        if fixed_elem is not None:
            order.remove(fixed_elem)
            order.insert(0, fixed_elem)

        for e in order:
            ecx, ecy = elem_centers[e]
            best_s = min(
                (s for s in range(len(slot_centers)) if s not in used_slots),
                key=lambda s: (math.hypot(slot_centers[s][0] - ecx, slot_centers[s][1] - ecy), s),
            )
            assignment[best_s] = e
            used_slots.add(best_s)

        active_slots = sorted(used_slots)
        if len(slot_centers) > self.n:
            extra_limit = min(len(slot_centers), self.n + max(4, self.n // 2))
            remaining = [s for s in range(len(slot_centers)) if s not in used_slots]
            active_slots.extend(remaining[: max(0, extra_limit - len(active_slots))])

        compact_centers = [slot_centers[s] for s in active_slots]
        compact_assignment = [assignment[s] for s in active_slots]
        return compact_centers, compact_assignment

    def _apply_assignment(self, slot_centers, assignment, fixed_elem, raw_pos):
        placed = {}
        if fixed_elem is not None:
            fx, fy = raw_pos[fixed_elem]
            snapped = self._snap_near(fixed_elem, fx, fy)
            placed[fixed_elem] = snapped if snapped is not None else (fx, fy)

        for s_idx, elem in enumerate(assignment):
            if elem < 0 or elem == fixed_elem:
                continue
            scx, scy = slot_centers[s_idx]
            ox, oy = self.center_offsets[elem]
            gx, gy = self._clamp_to_inner(elem, scx - ox, scy - oy)
            snapped = self._snap_near(elem, gx, gy)
            cand = snapped if snapped is not None else (gx, gy)
            box = self._get_box(elem, *cand)
            if self._within_board(box) and not self._collides_with(box, placed):
                placed[elem] = cand
            else:
                placed[elem] = self._find_nearest_free(elem, gx, gy, placed)

        self.positions = placed

    def _find_nearest_free(self, i, target_x, target_y, placed):
        g = max(0.25, self.p.C / 2.0)
        ix_lo = math.ceil((self.inner_rect[0] - self.bboxes[i][0]) / g - 1e-9)
        ix_hi = math.floor((self.inner_rect[2] - self.bboxes[i][2]) / g + 1e-9)
        iy_lo = math.ceil((self.inner_rect[1] - self.bboxes[i][1]) / g - 1e-9)
        iy_hi = math.floor((self.inner_rect[3] - self.bboxes[i][3]) / g + 1e-9)

        best_pos = None
        best_dist = float('inf')
        for ix in range(ix_lo, ix_hi + 1):
            gx = ix * g
            for iy in range(iy_lo, iy_hi + 1):
                gy = iy * g
                box = self._get_box(i, gx, gy)
                if self._within_board(box) and not self._collides_with(box, placed):
                    d = math.hypot(gx - target_x, gy - target_y)
                    if d < best_dist:
                        best_dist = d
                        best_pos = (gx, gy)
        if best_pos is None:
            ref = self.snap.modules[i]['reference']
            raise RuntimeError(f"Не удалось разместить корпус {ref} без пересечений с заданным зазором B.")
        return best_pos

    def _get_pad_abs(self, i, pad_num):
        mod = self.snap.modules[i]
        lx, ly = mod['pads'][pad_num]
        if i in self.positions:
            gx, gy = self.positions[i]
            return (gx + lx, gy + ly)
        rx, ry = _rotate_offset(lx, ly, mod.get('angle', 0.0))
        return (mod['x'] + rx, mod['y'] + ry)

    def _get_net_pins(self):
        nets = {}
        for i, mod in enumerate(self.snap.modules):
            pads = mod['pads']
            for pad_num, pad_net in mod['pad_nets'].items():
                if pad_net.net_code <= 0 or not pad_net.net_name:
                    continue
                if pad_num not in pads:
                    continue
                nets.setdefault(pad_net.net_code, []).append((mod['reference'], pad_num, i))
        for code in nets:
            nets[code].sort(key=lambda x: (x[0], x[1]))
        return nets

    def _calc_total_wire(self, metric):
        total = 0.0
        for pins in self._get_net_pins().values():
            if len(pins) >= 2:
                pts = [self._get_pad_abs(i, pad_num) for _, pad_num, i in pins]
                total += _mst_length(pts, metric)
        return total

    def _opt_step(self):
        if self.p.optimization_mode == OptimizationMode.D_C:
            return self.p.C
        if self.p.optimization_mode == OptimizationMode.D_C2:
            return self.p.C / 2.0
        if self.p.optimization_mode == OptimizationMode.D_C4:
            return self.p.C / 4.0
        return 0.0

    def _run_extra_optimization(self, fixed_elem):
        d = self._opt_step()
        if d <= 0:
            return
        net_pins = self._get_net_pins()
        active_nets = {code: pins for code, pins in net_pins.items() if len(pins) >= 2}
        if not active_nets:
            return

        mod_nets = [[] for _ in range(self.n)]
        net_lengths = {}
        for code, pins in active_nets.items():
            pts = [self._get_pad_abs(m_idx, pad_num) for _, pad_num, m_idx in pins]
            net_lengths[code] = _mst_length(pts, self.p.metric)
            seen = set()
            for _, _, m_idx in pins:
                if m_idx not in seen:
                    seen.add(m_idx)
                    mod_nets[m_idx].append(code)

        directions = ((d, 0.0), (-d, 0.0), (0.0, d), (0.0, -d))
        for _ in range(500):
            improved = False
            for i in range(self.n):
                if fixed_elem is not None and i == fixed_elem:
                    continue
                incident = mod_nets[i]
                if not incident:
                    continue
                cur_x, cur_y = self.positions[i]
                cur_sub = sum(net_lengths[code] for code in incident)

                for dx, dy in directions:
                    while True:
                        nx = round((cur_x + dx) / d) * d
                        ny = round((cur_y + dy) / d) * d
                        box = self._get_box(i, nx, ny)
                        if not self._within_board(box) or self._collides_with(box, self.positions, i):
                            break
                        self.positions[i] = (nx, ny)
                        cand_lens = {}
                        cand_sub = 0.0
                        for code in incident:
                            pts = [self._get_pad_abs(m_idx, pad_num) for _, pad_num, m_idx in active_nets[code]]
                            nl = _mst_length(pts, self.p.metric)
                            cand_lens[code] = nl
                            cand_sub += nl
                        if cand_sub < cur_sub - 1e-9:
                            cur_x, cur_y = nx, ny
                            cur_sub = cand_sub
                            for code, nl in cand_lens.items():
                                net_lengths[code] = nl
                            improved = True
                        else:
                            self.positions[i] = (cur_x, cur_y)
                            break

            if not improved:
                break

    def run(self):
        board_width = self.edge_rect[2] - self.edge_rect[0]
        board_length = self.edge_rect[3] - self.edge_rect[1]
        if self.n == 0:
            return PairwiseResult(
                {}, 0.0, 0, 0, 0.0, 0.0, "",
                board_width, board_length, 0.0, 0.0, 0.0, 0.0, 0,
            )

        pair_start = time.perf_counter()

        raw_pos = self._prepare_initial_positions()
        fixed_elem = algo.pick_directive_element(self.bboxes, self.c, self.p.directive_mode.value)
        slot_centers, assignment = self._build_regular_slots(raw_pos, fixed_elem)

        metric_name = "manhattan" if self.p.metric == Metric.MANHATTAN else "euclidean"
        if self.p.algo_version == PairwiseAlgoVersion.VERSION_1:
            final_assignment = algo.solve_version_1(
                self.c, slot_centers, assignment, fixed_elem, metric_name
            )
        else:
            final_assignment = algo.solve_version_2(
                self.c, slot_centers, assignment, fixed_elem, metric_name
            )

        self._apply_assignment(slot_centers, final_assignment, fixed_elem, raw_pos)

        pair_duration = time.perf_counter() - pair_start

        pair_w_euc = self._calc_total_wire(Metric.EUCLIDEAN)
        pair_w_man = self._calc_total_wire(Metric.MANHATTAN)

        if self.p.optimization_mode != OptimizationMode.NONE:
            opt_start = time.perf_counter()
            self._run_extra_optimization(fixed_elem)
            opt_duration = time.perf_counter() - opt_start
            w_euc = self._calc_total_wire(Metric.EUCLIDEAN)
            w_man = self._calc_total_wire(Metric.MANHATTAN)
        else:
            opt_duration = 0.0
            w_euc = pair_w_euc
            w_man = pair_w_man

        total_duration = pair_duration + opt_duration
        conn_count = sum(len(v) - 1 for v in self._get_net_pins().values() if len(v) >= 2)
        directive_ref = self.snap.modules[fixed_elem]['reference'] if fixed_elem is not None else ""

        return PairwiseResult(
            self.positions,
            total_duration,
            self.n,
            conn_count,
            w_euc,
            w_man,
            directive_ref,
            board_width,
            board_length,
            pair_w_euc,
            pair_w_man,
            pair_duration,
            opt_duration,
            self.shifted_count,
        )


def run_pairwise_placement(board, params):
    snapshot = _BoardSnapshot(board)
    before_euc, before_man = _snapshot_wire_lengths(snapshot)
    result = PairwisePlacer(snapshot, params).run()
    return result, before_euc, before_man