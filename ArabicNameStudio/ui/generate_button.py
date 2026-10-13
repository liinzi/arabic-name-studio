"""
Premium Generate button: soft multi-layer elevation shadow (no duplicate-slab
artifact), physics-inspired press (compress -> spring overshoot -> damped
settle), and consistent default/hover/focus/pressed/disabled/loading/success
states. Self-contained; balanced painter usage.
"""
import math
import logging
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, Signal, QTimer, QPropertyAnimation, QEasingCurve, QPointF, QRectF, Property
from PySide6.QtGui import QColor, QFont, QFontMetricsF, QPainter, QPen, QRadialGradient, QLinearGradient, QPainterPath

log = logging.getLogger("ui.genbtn")


def _sparkle(painter, r, color):
    cx, cy = r.center().x(), r.center().y()
    R = min(r.width(), r.height()) / 2.0
    ri = R * 0.30
    path = QPainterPath()
    pts = []
    for k in range(4):
        ao = math.radians(-90 + k * 90)
        ai = math.radians(-90 + k * 90 + 45)
        pts.append((cx + R * math.cos(ao), cy + R * math.sin(ao)))
        pts.append((cx + ri * math.cos(ai), cy + ri * math.sin(ai)))
    path.moveTo(pts[0][0], pts[0][1])
    for x, y in pts[1:]:
        path.lineTo(x, y)
    path.closeSubpath()
    painter.save()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(Qt.NoPen)
    painter.setBrush(color)
    painter.drawPath(path)
    painter.restore()


class GenerateButton(QWidget):
    clicked = Signal()

    def __init__(self, text, parent=None):
        super().__init__(parent)
        self.text = text
        self._hover = 0.0
        self._press = 0.0
        self._enabled = True
        self._ripple = 0.0
        self._ripple_op = 0.0
        self._ripple_center = QPointF(0, 0)
        self._state = "default"
        self._load_phase = 0.0

        self.setFocusPolicy(Qt.StrongFocus)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(176, 58)

        self.hover_anim = QPropertyAnimation(self, b"hover_val")
        self.hover_anim.setDuration(220)
        self.hover_anim.setEasingCurve(QEasingCurve.OutCubic)

        self.press_anim = QPropertyAnimation(self, b"press_val")
        self.press_anim.setDuration(120)
        self.press_anim.setEasingCurve(QEasingCurve.OutQuad)

        self.release_anim = QPropertyAnimation(self, b"press_val")
        self.release_anim.setDuration(520)
        self.release_anim.setEasingCurve(QEasingCurve.OutBack)  # overshoot + settle

        self.ripple_anim = QPropertyAnimation(self, b"ripple_val")
        self.ripple_anim.setDuration(620)
        self.ripple_anim.setEasingCurve(QEasingCurve.OutCubic)
        self.ripple_fade = QPropertyAnimation(self, b"ripple_op_val")
        self.ripple_fade.setDuration(620)

        self._load_timer = QTimer(self)
        self._load_timer.timeout.connect(self._tick_load)

    # properties
    def _get_hover(self):
        return self._hover

    def _set_hover(self, v):
        self._hover = v
        self.update()

    hover_val = Property(float, _get_hover, _set_hover)

    def _get_press(self):
        return self._press

    def _set_press(self, v):
        self._press = v
        self.update()

    press_val = Property(float, _get_press, _set_press)

    def _get_ripple(self):
        return self._ripple

    def _set_ripple(self, v):
        self._ripple = v
        self.update()

    ripple_val = Property(float, _get_ripple, _set_ripple)

    def _get_ripple_op(self):
        return self._ripple_op

    def _set_ripple_op(self, v):
        self._ripple_op = v
        self.update()

    ripple_op_val = Property(float, _get_ripple_op, _set_ripple_op)

    def _tick_load(self):
        self._load_phase += 0.15
        self.update()

    def set_state(self, s):
        self._state = s
        if s == "loading":
            self._load_timer.start(40)
        else:
            self._load_timer.stop()
        self.update()

    def setEnabled(self, enabled):
        self._enabled = enabled
        self.setCursor(Qt.PointingHandCursor if enabled else Qt.ArrowCursor)
        self.update()

    def isEnabled(self):
        return self._enabled

    def enterEvent(self, e):
        if self._enabled:
            self.hover_anim.stop()
            self.hover_anim.setStartValue(self._hover)
            self.hover_anim.setEndValue(1.0)
            self.hover_anim.start()
        super().enterEvent(e)

    def leaveEvent(self, e):
        self.hover_anim.stop()
        self.hover_anim.setStartValue(self._hover)
        self.hover_anim.setEndValue(0.0)
        self.hover_anim.start()
        super().leaveEvent(e)

    def mousePressEvent(self, e):
        if not self._enabled:
            return
        self._ripple_center = QPointF(e.pos())
        self.ripple_anim.stop(); self.ripple_anim.setStartValue(0.0)
        self.ripple_anim.setEndValue(240.0); self.ripple_anim.start()
        self.ripple_fade.stop(); self.ripple_fade.setStartValue(0.5)
        self.ripple_fade.setEndValue(0.0); self.ripple_fade.start()
        self.release_anim.stop()
        self.press_anim.stop()
        self.press_anim.setStartValue(self._press)
        self.press_anim.setEndValue(1.0)
        self.press_anim.start()
        super().mousePressEvent(e)

    def mouseReleaseEvent(self, e):
        if not self._enabled:
            return
        self.press_anim.stop()
        self.release_anim.stop()
        self.release_anim.setStartValue(self._press)
        self.release_anim.setEndValue(0.0)
        self.release_anim.start()
        if self.rect().contains(e.pos()):
            self.clicked.emit()
        super().mouseReleaseEvent(e)

    def paintEvent(self, e):
        p = QPainter(self)
        try:
            p.setRenderHint(QPainter.RenderHint.Antialiasing)
            p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
            r = QRectF(self.rect())
            radius = 20.0
            cx, cy = r.center().x(), r.center().y()
            press = max(-0.3, min(1.0, self._press))
            scale = 1.0 - 0.05 * press
            lift = self._hover * 2.0

            # soft multi-layer elevation shadow (subtle, not a duplicate slab)
            p.setPen(Qt.NoPen)
            for off, al in ((6, 24), (9, 14), (12, 8)):
                p.setBrush(QColor(0, 0, 0, al))
                p.drawRoundedRect(r.adjusted(3, off - lift, -3, -2), radius, radius)

            # hover glow
            if self._enabled and self._hover > 0.01:
                g = QRadialGradient(r.center(), r.width() * 0.7)
                g.setColorAt(0.0, QColor(233, 200, 122, int(55 * self._hover)))
                g.setColorAt(1.0, QColor(233, 200, 122, 0))
                p.setBrush(g)
                p.drawRoundedRect(r.adjusted(-8, -8, 8, 8), radius + 8, radius + 8)

            # body (scaled for spring)
            p.save()
            p.translate(cx, cy)
            p.scale(scale, scale)
            p.translate(-cx, -cy)
            rr = r.adjusted(2, 2 - lift, -2, -2 - lift)

            if self._enabled:
                if self._state == "success":
                    body = QLinearGradient(0, rr.top(), 0, rr.bottom())
                    body.setColorAt(0.0, QColor(190, 220, 150))
                    body.setColorAt(1.0, QColor(120, 160, 90))
                else:
                    body = QLinearGradient(0, rr.top(), 0, rr.bottom())
                    body.setColorAt(0.0, QColor(232, 199, 119))
                    body.setColorAt(1.0, QColor(184, 134, 47))
                p.setBrush(body)
                p.setPen(QPen(QColor(244, 224, 178, int(120 + self._hover * 100)), 1.2))
            else:
                p.setBrush(QColor(78, 51, 32, 110))
                p.setPen(QPen(QColor(201, 162, 79, 40), 1.0))
            p.drawRoundedRect(rr, radius, radius)

            # top inner highlight
            if self._enabled:
                hl = QLinearGradient(0, rr.top(), 0, rr.top() + rr.height() * 0.5)
                hl.setColorAt(0.0, QColor(255, 250, 230, 90))
                hl.setColorAt(1.0, QColor(255, 250, 230, 0))
                p.setPen(Qt.NoPen)
                p.setBrush(hl)
                p.drawRoundedRect(rr.adjusted(3, 2, -3, -rr.height() * 0.5), radius - 3, radius - 3)

            # ripple (clipped to body)
            if self._ripple_op > 0.01:
                clip = QPainterPath()
                clip.addRoundedRect(rr, radius, radius)
                p.save()
                p.setClipPath(clip)
                p.setPen(Qt.NoPen)
                p.setBrush(QColor(255, 248, 224, int(self._ripple_op * 255)))
                p.drawEllipse(self._ripple_center, self._ripple, self._ripple)
                p.restore()

            # loading spinner arc
            if self._state == "loading" and self._enabled:
                p.setPen(QPen(QColor(40, 26, 12, 200), 3.0))
                p.setBrush(Qt.NoBrush)
                a0 = int(self._load_phase * 57.3)
                p.drawArc(rr.adjusted(6, 6, -6, -6), a0 * 16, 90 * 16)

            # label + sparkle / success check
            f = QFont("Optima", 15, QFont.DemiBold)
            if hasattr(QFont, "PercentageSpacing"):
                f.setLetterSpacing(QFont.PercentageSpacing, 104)
            p.setFont(f)
            fm = QFontMetricsF(f)
            textcolor = QColor(28, 18, 10) if self._enabled else QColor(214, 196, 168, 120)
            p.setPen(textcolor)
            if self._state == "success":
                p.drawText(rr, Qt.AlignCenter, "Ready")
            else:
                textw = fm.horizontalAdvance(self.text)
                spk = 13.0
                gap = 10.0
                total = textw + gap + spk
                sx = rr.center().x() - total / 2.0
                p.drawText(QRectF(sx, rr.y(), textw, rr.height()), Qt.AlignLeft | Qt.AlignVCenter, self.text)
                _sparkle(p, QRectF(sx + textw + gap, rr.center().y() - spk / 2.0, spk, spk), textcolor)
            p.restore()

            # focus ring
            if self._enabled and self.hasFocus():
                p.setPen(QPen(QColor(244, 224, 178, 130), 1.5))
                p.setBrush(Qt.NoBrush)
                p.drawRoundedRect(r.adjusted(-3, -3, 3, 3), radius + 3, radius + 3)
        except Exception as exc:
            log.error("genbtn: %s", exc)
        finally:
            if p.isActive():
                p.end()
