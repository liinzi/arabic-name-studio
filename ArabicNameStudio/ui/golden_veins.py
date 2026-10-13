"""
Living Golden Ornament: many independent luminous veins flowing along the Islamic
lattice with randomised paths/speeds, staggered spawning, natural branching and
occasional merging. Parameterised by max_veins and intensity so the landing page
runs rich (~20 veins) while the gallery runs subtle. No painter save/restore is
used, so it can never leave unbalanced state; segment counts are capped for
steady performance.
"""
import math
import time
import random
import logging
from PySide6.QtGui import QColor, QPen
from PySide6.QtCore import QPointF, Qt

log = logging.getLogger("ui.veins")


class _Vein:
    __slots__ = ["pi", "col", "row", "t", "speed", "tail", "width", "branched",
                 "dead", "phase"]

    def __init__(self, pi, col, row, rng):
        self.pi = pi
        self.col = col
        self.row = row
        self.t = rng.uniform(0.0, 0.15)
        self.speed = rng.uniform(0.08, 0.24)
        self.tail = rng.uniform(0.12, 0.24)
        self.width = rng.uniform(1.0, 2.4)
        self.branched = False
        self.dead = False
        self.phase = rng.uniform(0.0, 6.28)


class VeinField:
    def __init__(self, tile=200, seed=7, max_veins=20, intensity=1.0):
        self.tile = float(tile)
        self.max_veins = max_veins
        self.intensity = intensity
        self.rng = random.Random(seed)
        self.veins = []
        self._last = None
        self._spawn_cd = 0.0
        self._build_paths()

    def _circle(self, cx, cy, r, n):
        return [(cx + r * math.cos(2 * math.pi * i / n), cy + r * math.sin(2 * math.pi * i / n))
                for i in range(n)]

    def _poly(self, pts, per):
        out = []
        n = len(pts)
        for i in range(n):
            x0, y0 = pts[i]
            x1, y1 = pts[(i + 1) % n]
            for k in range(per):
                t = k / float(per)
                out.append((x0 + (x1 - x0) * t, y0 + (y1 - y0) * t))
        return out

    def _build_paths(self):
        S = self.tile
        c = S / 2.0
        r = 0.42 * S
        a = r * 0.7071
        paths = []
        paths.append(self._poly([(c - a, c - a), (c + a, c - a), (c + a, c + a), (c - a, c + a)], 20))
        paths.append(self._poly([(c, c - r), (c + r, c), (c, c + r), (c - r, c)], 20))
        paths.append(self._circle(c, c, r * 0.55, 48))
        paths.append(self._circle(c, c, r * 0.92, 48))
        for cx, cy in ((0, 0), (S, 0), (0, S), (S, S)):
            paths.append(self._circle(cx, cy, r * 0.5, 32))
        self.paths = paths

    def _pen(self, color, width):
        pen = QPen(color, width)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        return pen

    def _spawn(self, cmin, cmax, rmin, rmax):
        self.veins.append(_Vein(self.rng.randrange(len(self.paths)),
                                self.rng.randint(cmin, cmax),
                                self.rng.randint(rmin, rmax), self.rng))

    def advance_and_paint(self, p, rect, dx, dy):
        try:
            now = time.monotonic()
            dt = min(0.05, (now - self._last) if self._last else 0.016)
            self._last = now
            T = self.tile

            cmin = int(math.floor((rect.left() - dx) / T)) - 1
            cmax = int(math.ceil((rect.right() - dx) / T)) + 1
            rmin = int(math.floor((rect.top() - dy) / T)) - 1
            rmax = int(math.ceil((rect.bottom() - dy) / T)) + 1
            if cmax < cmin:
                cmax = cmin
            if rmax < rmin:
                rmax = rmin

            # staggered spawning
            self._spawn_cd -= dt
            if self._spawn_cd <= 0.0:
                if len(self.veins) < self.max_veins:
                    self._spawn(cmin, cmax, rmin, rmax)
                self._spawn_cd = self.rng.uniform(0.08, 0.45)

            # advance + branch
            for v in self.veins:
                v.t += v.speed * dt
                if v.t > 1.0:
                    v.dead = True
                elif (not v.branched) and v.t > 0.4 and self.rng.random() < 0.012:
                    v.branched = True
                    if len(self.veins) < self.max_veins:
                        child = _Vein((v.pi + 1) % len(self.paths), v.col, v.row, self.rng)
                        child.width = max(0.8, v.width * 0.7)
                        self.veins.append(child)

            # merge close veins on the same path/cell
            alive = [v for v in self.veins if not v.dead]
            merged = []
            for v in alive:
                for u in merged:
                    if u.pi == v.pi and u.col == v.col and u.row == v.row \
                       and abs(u.t - v.t) < 0.03:
                        u.width = min(3.0, u.width + v.width * 0.5)
                        v.dead = True
                        break
                if not v.dead:
                    merged.append(v)
            self.veins = merged

            p.setRenderHint(p.RenderHint.Antialiasing)
            for v in self.veins:
                self._draw_vein(p, v, dx, dy)
        except Exception as exc:
            log.error("veins: %s", exc)

    def _draw_vein(self, p, v, dx, dy):
        pts = self.paths[v.pi]
        n = len(pts)
        ox = v.col * self.tile + dx
        oy = v.row * self.tile + dy
        head = v.t * n
        tail = max(0.0, head - v.tail * n)
        i0 = int(tail)
        i1 = int(head)
        if i1 - i0 > 16:
            i0 = i1 - 16
        span = max(1.0, head - tail)
        I = self.intensity
        for i in range(i0, i1):
            f = (i - tail) / span
            a = f * f
            x0, y0 = pts[i % n]
            x1, y1 = pts[(i + 1) % n]
            p0 = QPointF(ox + x0, oy + y0)
            p1 = QPointF(ox + x1, oy + y1)
            p.setPen(self._pen(QColor(233, 200, 122, int(30 * a * I)), v.width * 3.2))
            p.drawLine(p0, p1)
            p.setPen(self._pen(QColor(244, 224, 178, int(80 * a * I)), v.width * 1.6))
            p.drawLine(p0, p1)
            p.setPen(self._pen(QColor(255, 248, 224, int(210 * a * I)), v.width))
            p.drawLine(p0, p1)
