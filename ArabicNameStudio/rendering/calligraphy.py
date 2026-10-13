"""
Museum-grade calligraphy renderer. Size is solved from reliable font metrics
(horizontalAdvance + height) so the composition fills the card's safe area; the
text is drawn as vectors at that size (crisp), centered, aspect-preserved, with a
hard containment clamp so it can never overflow. Reveal animation, gold-foil
rim/texture, styles and overflow protection retained.
"""
import math
import random
import logging
from PySide6.QtWidgets import QWidget, QSizePolicy
from PySide6.QtGui import (
    QPainter, QFont, QFontInfo, QFontMetricsF, QColor, QPen, QLinearGradient,
    QBrush, QPainterPath, QImage, QRadialGradient,
)
from PySide6.QtCore import (
    QRectF, Qt, QPointF, QPropertyAnimation, Property, QEasingCurve, QTimer,
)
from rendering.styles import DEFAULT

log = logging.getLogger("render.calligraphy")


def _cm(short, value):
    enum_cls = getattr(QPainter, "CompositionMode", None)
    if enum_cls is not None:
        v = getattr(enum_cls, short, None)
        if v is not None:
            return v
    v = getattr(QPainter, "CompositionMode_" + short, None)
    if v is not None:
        return v
    if enum_cls is not None:
        try:
            return enum_cls(value)
        except Exception:
            pass
    return value


CM_SRC_OVER = _cm("SourceOver", 0)
CM_DEST_IN = _cm("DestinationIn", 6)
CM_DEST_OUT = _cm("DestinationOut", 8)
CM_SRC_IN = _cm("SourceIn", 5)
CM_SRC_ATOP = _cm("SourceAtop", 9)


class _Dust:
    __slots__ = ["x", "y", "vx", "vy", "life", "size"]

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = random.uniform(-0.6, 0.6)
        self.vy = random.uniform(-1.0, 0.1)
        self.life = random.uniform(18, 50)
        self.size = random.uniform(1.0, 2.6)


class CalligraphyWidget(QWidget):
    TATWEEL = "ـ"

    def __init__(self, font_family="Arial", parent=None):
        super().__init__(parent)
        self.text = ""
        self.font_family = font_family
        self.style = DEFAULT
        self._wrap = False
        self._reveal = 0.0
        self._style_t = 1.0
        self._shimmer_phase = 0.0
        self._breath_phase = 0.0
        self.mouse_x = 0.0
        self.mouse_y = 0.0
        self._dust = []
        self._burst = []
        self._snap = None
        self._mask = None
        self._shadow = None
        self._tex = None
        self._hi = None
        self._lo = None
        self._colored = None
        self._asset_key = None
        self._building = False
        self._art_bbox = QRectF()

        self.setMinimumSize(400, 300)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMouseTracking(True)

        self.shimmer_timer = QTimer(self)
        self.shimmer_timer.timeout.connect(self._tick_shimmer)
        self.shimmer_timer.start(40)
        self.breath_timer = QTimer(self)
        self.breath_timer.timeout.connect(self._tick_breath)
        self.breath_timer.start(50)

        self.reveal_anim = QPropertyAnimation(self, b"reveal_val")
        self.reveal_anim.setEasingCurve(QEasingCurve.InOutCubic)
        self.style_anim = QPropertyAnimation(self, b"style_t")
        self.style_anim.setDuration(900)
        self.style_anim.setEasingCurve(QEasingCurve.OutCubic)
        self.style_anim.finished.connect(self._clear_snap)

    def _get_reveal(self):
        return self._reveal

    def _set_reveal(self, v):
        self._reveal = max(0.0, min(1.0, float(v)))
        self.update()

    reveal_val = Property(float, _get_reveal, _set_reveal)

    def _get_style_t(self):
        return self._style_t

    def _set_style_t(self, v):
        self._style_t = max(0.0, min(1.0, float(v)))
        self.update()

    style_t = Property(float, _get_style_t, _set_style_t)

    def _tick_shimmer(self):
        self._shimmer_phase += 0.012
        self.update()

    def _tick_breath(self):
        self._breath_phase += 0.022
        if 0.0 < self._reveal < 1.0 and self._art_bbox.width() > 0:
            bb = self._art_bbox
            if random.random() < 0.8:
                ex = bb.right() - bb.width() * self._reveal
                ey = bb.center().y() + random.uniform(-bb.height() * 0.3, bb.height() * 0.3)
                self._dust.append(_Dust(ex, ey))
        for d in self._dust:
            d.x += d.vx
            d.y += d.vy
            d.vy += 0.02
            d.life -= 1
        self._dust = [d for d in self._dust if d.life > 0]
        for b in self._burst:
            b.x += b.vx
            b.y += b.vy
            b.vy += 0.03
            b.life -= 1
        self._burst = [b for b in self._burst if b.life > 0]
        self.update()

    def set_text(self, text):
        self.text = text
        self._reveal = 0.0
        self._asset_key = None
        self._dust = []
        self.update()

    def set_style(self, preset, animate=True):
        if preset is self.style:
            return
        if animate and self._mask is not None and self.width() > 0:
            try:
                self._snap = self.grab()
            except Exception:
                self._snap = None
            for _ in range(40):
                self._burst.append(_Dust(random.uniform(0, self.width()), random.uniform(0, self.height())))
        else:
            self._snap = None
        self.style = preset
        self._asset_key = None
        if animate:
            self._style_t = 0.0
            self.style_anim.stop()
            self.style_anim.setStartValue(0.0)
            self.style_anim.setEndValue(1.0)
            self.style_anim.start()
        else:
            self._style_t = 1.0
        self.update()

    def _clear_snap(self):
        self._snap = None
        self.update()

    def start_animation(self):
        self.reveal_anim.stop()
        self._reveal = 0.0
        self._dust = []
        n = len(self.text)
        dur = 1000 if n <= 8 else int(min(2000, 1000 + (n - 8) * 45))
        self.reveal_anim.setDuration(dur)
        self.reveal_anim.setStartValue(0.0)
        self.reveal_anim.setEndValue(1.0)
        self.reveal_anim.start()

    def mouseMoveEvent(self, event):
        self.mouse_x = float(event.pos().x())
        self.mouse_y = float(event.pos().y())
        self.update()

    def resizeEvent(self, event):
        self.mouse_x = self.width() / 2.0
        self.mouse_y = self.height() / 2.0
        self._asset_key = None
        super().resizeEvent(event)

    def _flags(self):
        return Qt.AlignCenter | (Qt.TextWordWrap if self._wrap else 0)

    def _family_for_style(self):
        try:
            from PySide6.QtGui import QFontDatabase
            fams = set(QFontDatabase.families())
        except Exception:
            fams = set()
        for f in self.style.get("fonts", []):
            if f in fams:
                return f
        return self.font_family

    def _apply_kashida(self, text, rect, fm):
        if self._wrap or len(text.split()) > 3:
            return text
        target = rect.width() * 0.78
        if fm.horizontalAdvance(text) >= target:
            return text
        connectable = set("بتثجحخسشصضطظعغفقكلمنهىئيـ")
        no_left = set("ادذرزو")
        words = text.split(" ")
        idx = max(range(len(words)), key=lambda i: len(words[i].replace(self.TATWEEL, "")))
        for _ in range(6):
            w = list(words[idx])
            done = False
            for i in range(len(w) - 1):
                if w[i] in connectable and w[i + 1] not in no_left and w[i] != self.TATWEEL:
                    w.insert(i + 1, self.TATWEEL)
                    done = True
                    break
            if not done:
                break
            words[idx] = "".join(w)
            nt = " ".join(words)
            if fm.horizontalAdvance(nt) >= target:
                return nt
        return " ".join(words)

    def _build_assets(self):
        w = self.width()
        h = self.height()
        if w < 12 or h < 12 or not self.text:
            return
        key = (self.text, w, h, self.style["id"])
        if key == self._asset_key and self._mask is not None:
            return
        if self._building:
            return
        self._building = True
        try:
            rng = random.Random(hash((self.text, self.style["id"])) & 0xFFFFFFFF)
            self._wrap = len(self.text) > 24
            display = self.text
            vs = self.style["vscale"] if not self._wrap else 1.0
            shear = self.style.get("shear", 0.0) if not self._wrap else 0.0

            pad = min(w, h) * 0.06
            availW = w - 2 * pad
            availH = h - 2 * pad
            optical_dy = 0.07 * h
            availH_eff = availH - 2 * optical_dy

            family = self._family_for_style()
            ref = QFont(family, 100, self.style["weight"])
            ref.setStyleHint(QFont.Serif)
            if hasattr(QFont, "PercentageSpacing"):
                ref.setLetterSpacing(QFont.PercentageSpacing, self.style["spacing"])
            fm = QFontMetricsF(ref)
            display = self._apply_kashida(display, QRectF(0, 0, availW * 4, availH * 4), fm)

            # RELIABLE metrics: advance width + line height
            advW = max(1.0, fm.horizontalAdvance(display))
            advH = max(1.0, fm.height())
            pts = 100.0 * min(availW / advW, availH_eff / (advH * vs))
            pts = max(8.0, min(pts, 600.0))

            font = QFont(family, int(pts), self.style["weight"])
            font.setStyleHint(QFont.Serif)
            if hasattr(QFont, "PercentageSpacing"):
                font.setLetterSpacing(QFont.PercentageSpacing, self.style["spacing"])

            mask = QImage(w, h, QImage.Format.Format_ARGB32)
            mask.fill(QColor(0, 0, 0, 0))
            mp = QPainter(mask)
            try:
                mp.setRenderHint(QPainter.RenderHint.Antialiasing)
                mp.setRenderHint(QPainter.RenderHint.TextAntialiasing)
                mp.setLayoutDirection(Qt.RightToLeft)
                mp.setFont(font)
                mp.translate(w / 2.0, h / 2.0)
                mp.scale(1.0, vs)
                if shear:
                    mp.shear(shear, 0.0)
                mp.translate(-w / 2.0, -h / 2.0)
                mp.translate(0.0, optical_dy)
                mp.setPen(QPen(QColor(255, 255, 255, 255)))
                mp.drawText(QRectF(0, 0, w, h), self._flags(), display)
            finally:
                if mp.isActive():
                    mp.end()

            fm2 = QFontMetricsF(font)
            bw = fm2.horizontalAdvance(display)
            bh = fm2.height() * vs
            self._mask = mask
            self._art_bbox = QRectF((w - bw) / 2.0, (h - bh) / 2.0 + optical_dy, bw, bh)
            self._shadow = self._render_shadow(w, h, mask)
            if self.style["body"] == "gold":
                self._hi = self._build_rim(mask, 2, 2, (255, 240, 182, 235))
                self._lo = self._build_rim(mask, -2, -2, (92, 56, 16, 235))
            else:
                self._hi = self._build_rim(mask, 1, 1, (212, 175, 55, 200))
                self._lo = self._build_rim(mask, -1, -1, (212, 175, 55, 120))
            self._tex = self._make_texture(w, h, rng)
            self._colored = None
            self._asset_key = key
        except Exception as exc:
            log.error("asset build failed: %s", exc)
            self._mask = None
        finally:
            self._building = False

    def _build_rim(self, mask, dx, dy, tint):
        w, h = mask.width(), mask.height()
        img = QImage(w, h, QImage.Format.Format_ARGB32)
        img.fill(QColor(0, 0, 0, 0))
        p = QPainter(img)
        try:
            p.drawImage(0, 0, mask)
            p.setCompositionMode(CM_DEST_OUT)
            p.drawImage(dx, dy, mask)
            p.setCompositionMode(CM_SRC_IN)
            p.fillRect(0, 0, w, h, QColor(*tint))
        finally:
            if p.isActive():
                p.end()
        return img

    def _render_shadow(self, w, h, mask):
        img = QImage(w, h, QImage.Format.Format_ARGB32)
        img.fill(QColor(0, 0, 0, 0))
        p = QPainter(img)
        try:
            p.fillRect(0, 0, w, h, QColor(20, 12, 6, 255))
            p.setCompositionMode(CM_DEST_IN)
            p.drawImage(0, 0, mask)
        finally:
            if p.isActive():
                p.end()
        return img

    def _make_texture(self, w, h, rng):
        img = QImage(w, h, QImage.Format.Format_ARGB32)
        img.fill(QColor(0, 0, 0, 0))
        p = QPainter(img)
        try:
            p.setRenderHint(QPainter.RenderHint.Antialiasing)
            p.setPen(Qt.NoPen)
            d = int(w * h * 0.006)
            for _ in range(d):
                x = rng.randint(0, w - 1)
                y = rng.randint(0, h - 1)
                p.setBrush(QColor(60, 38, 12, rng.randint(10, 22)))
                p.drawEllipse(QPointF(x, y), rng.uniform(0.5, 1.3), rng.uniform(0.5, 1.3))
            for _ in range(d):
                x = rng.randint(0, w - 1)
                y = rng.randint(0, h - 1)
                p.setBrush(QColor(255, 240, 200, rng.randint(8, 18)))
                p.drawEllipse(QPointF(x, y), rng.uniform(0.4, 1.1), rng.uniform(0.4, 1.1))
            if self.style["brushed"]:
                for _ in range(int(w * 0.4)):
                    y = rng.randint(0, h - 1)
                    x = rng.randint(0, w - 1)
                    p.setPen(QPen(QColor(255, 244, 210, rng.randint(4, 10)), 1.0))
                    p.drawLine(x, y, min(w - 1, x + rng.randint(6, 40)), y)
        finally:
            if p.isActive():
                p.end()
        return img

    def _gold_gradient(self, h):
        grad = QLinearGradient(0, 0, 0, h)
        for pos, col in self.style["palette"]:
            grad.setColorAt(pos, QColor(col))
        return grad

    def _fallback_draw(self, painter, rect):
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        painter.setLayoutDirection(Qt.RightToLeft)
        f = QFont(self.font_family, 48, self.style["weight"])
        painter.setFont(f)
        pen = QPen()
        pen.setBrush(QBrush(self._gold_gradient(rect.height())))
        pen.setWidthF(1.2)
        painter.setPen(pen)
        painter.drawText(rect, self._flags(), self.text)

    def _organic_clip(self, progress, rect):
        width = rect.width() * progress
        x_start = rect.right() - width
        path = QPainterPath()
        path.moveTo(rect.right(), rect.top())
        steps = 18
        prev_x = x_start
        prev_y = rect.top()
        for i in range(steps + 1):
            y = rect.top() + (rect.height() * i / steps)
            wave = math.sin(y * 0.014 + progress * 13.0) * 46.0 * (1.0 - progress * progress)
            x = x_start + wave
            if i == 0:
                path.lineTo(x, y)
            else:
                c_y = (prev_y + y) * 0.5
                path.cubicTo(QPointF(prev_x + 30, c_y), QPointF(x - 30, c_y), QPointF(x, y))
            prev_x = x
            prev_y = y
        path.lineTo(rect.right(), rect.bottom())
        path.closeSubpath()
        return path

    def paintEvent(self, event):
        if not self.text:
            return
        painter = QPainter(self)
        try:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
            w = self.width()
            h = self.height()
            rect = QRectF(0, 0, w, h)

            painter.setClipRect(rect)

            self._build_assets()
            if self._mask is None:
                self._fallback_draw(painter, rect)
                return

            if self._reveal < 0.999:
                if self._reveal <= 0.001:
                    painter.setClipRect(QRectF())
                else:
                    painter.setClipPath(self._organic_clip(self._reveal, rect), Qt.IntersectClip)

            cx, cy = w * 0.5, h * 0.5
            scale = 1.0 + math.sin(self._breath_phase) * 0.004
            px = (self.mouse_x - cx) * 0.008
            py = (self.mouse_y - cy) * 0.008
            painter.save()
            painter.translate(cx + px, cy + py)
            painter.scale(scale, scale)
            painter.translate(-cx, -cy)

            if self._shadow is not None:
                painter.setOpacity(0.50 * self._reveal)
                painter.drawImage(2, 3, self._shadow)
                painter.setOpacity(0.30 * self._reveal)
                painter.drawImage(4, 6, self._shadow)
                painter.setOpacity(1.0)

            colored = self._colored
            if colored is None or colored.width() != w or colored.height() != h:
                colored = QImage(w, h, QImage.Format.Format_ARGB32)
                self._colored = colored
            colored.fill(QColor(0, 0, 0, 0))
            cp = QPainter(colored)
            try:
                cp.fillRect(rect, QBrush(self._gold_gradient(h)))
                cp.setCompositionMode(CM_DEST_IN)
                cp.drawImage(0, 0, self._mask)
                if self._tex is not None:
                    cp.setCompositionMode(CM_SRC_ATOP)
                    cp.drawImage(0, 0, self._tex)
                cp.setCompositionMode(CM_SRC_OVER)
                if self._hi is not None:
                    cp.drawImage(0, 0, self._hi)
                if self._lo is not None:
                    cp.drawImage(0, 0, self._lo)
            finally:
                if cp.isActive():
                    cp.end()
            painter.drawImage(0, 0, colored)

            painter.restore()

            painter.setPen(Qt.NoPen)
            for d in self._dust:
                a = int(min(1.0, d.life / 22.0) * 210)
                painter.setBrush(QColor(244, 224, 178, a))
                painter.drawEllipse(QPointF(d.x, d.y), d.size, d.size)
            for b in self._burst:
                a = int(min(1.0, b.life / 30.0) * 230)
                painter.setBrush(QColor(255, 248, 224, a))
                painter.drawEllipse(QPointF(b.x, b.y), b.size, b.size)

            if self._snap is not None and self._style_t < 1.0:
                painter.setOpacity(1.0 - self._style_t)
                tgt = QRectF(self.rect())
                grow = tgt.adjusted(-20 * self._style_t, -20 * self._style_t,
                                    20 * self._style_t, 20 * self._style_t)
                painter.drawPixmap(grow, self._snap, QRectF(self._snap.rect()))
                painter.setOpacity(1.0)
        except Exception as exc:
            log.error("calligraphy paint: %s", exc)
        finally:
            if painter.isActive():
                painter.end()
