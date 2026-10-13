"""
Cinematic name->Arabic conversion overlay, retimed to ~2.6 s for a fast, premium
feel while keeping the dissolve -> form -> sweep choreography.
"""
import math
import random
import logging
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QTimer, Signal, QPointF, QRectF
from PySide6.QtGui import QPainter, QColor, QFont, QRadialGradient, QLinearGradient

log = logging.getLogger("ui.overlay")


class _Spark:
    __slots__ = ["x", "y", "vx", "vy", "life", "size"]

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = random.uniform(-0.6, 0.6)
        self.vy = random.uniform(-1.0, 0.2)
        self.life = random.uniform(20, 55)
        self.size = random.uniform(1.0, 2.6)


class TransformOverlay(QWidget):
    transformation_complete = Signal()
    TOTAL = 2600

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent;")
        self._elapsed = 0
        self._active = False
        self._done = False
        self._english = ""
        self._arabic = ""
        self._sparks = []
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)

    def start(self, english="", arabic=""):
        self._english = english
        self._arabic = arabic
        self._elapsed = 0
        self._done = False
        self._active = True
        self._sparks = []
        if self.parent():
            self.setGeometry(self.parent().rect())
        self.raise_()
        self.show()
        self._timer.start(16)

    def set_arabic(self, a):
        self._arabic = a

    def _tick(self):
        if not self._active:
            return
        self._elapsed += 16
        if random.random() < 0.6:
            self._sparks.append(_Spark(random.uniform(0, self.width()), random.uniform(0, self.height())))
        for s in self._sparks:
            s.x += s.vx
            s.y += s.vy
            s.vy += 0.02
            s.life -= 1
        self._sparks = [s for s in self._sparks if s.life > 0]
        self.update()
        if self._elapsed >= self.TOTAL and not self._done:
            self._done = True
            self._active = False
            self._timer.stop()
            self.hide()
            self.transformation_complete.emit()

    def paintEvent(self, event):
        if not self._active and self._elapsed == 0:
            return
        p = QPainter(self)
        try:
            p.setRenderHint(QPainter.RenderHint.Antialiasing)
            p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
            r = QRectF(self.rect())
            t = self._elapsed
            cx, cy = r.center().x(), r.center().y()

            bg_a = int(min(1.0, t / 300.0) * 235)
            if t > self.TOTAL - 500:
                bg_a = int(max(0.0, (self.TOTAL - t) / 500.0) * 235)
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(12, 8, 4, bg_a))
            p.drawRect(r)

            # english dissolve (0-700)
            if t < 800 and self._english:
                ea = max(0.0, 1.0 - t / 700.0)
                p.setPen(QColor(245, 236, 219, int(255 * ea)))
                p.setFont(QFont("Optima", 30, QFont.Medium))
                p.drawText(QRectF(0, cy - 60, r.width(), 60), Qt.AlignCenter, self._english)

            # arabic forming (500-2000)
            if t > 500 and self._arabic:
                prog = min(1.0, (t - 500) / 1400.0)
                n = max(1, int(len(self._arabic) * prog))
                shown = self._arabic[:n]
                af = min(1.0, (t - 500) / 500.0)
                p.setLayoutDirection(Qt.RightToLeft)
                p.setPen(QColor(233, 200, 122, int(255 * af)))
                p.setFont(QFont("Amiri", 48, QFont.Bold))
                p.drawText(QRectF(0, cy - 40, r.width(), 90), Qt.AlignCenter, shown)
                p.setLayoutDirection(Qt.LeftToRight)

            # sparks
            p.setPen(Qt.NoPen)
            for s in self._sparks:
                a = int(min(1.0, s.life / 25.0) * 200)
                p.setBrush(QColor(244, 224, 178, a))
                p.drawEllipse(QPointF(s.x, s.y), s.size, s.size)

            # light sweep (2000-2600)
            if 2000 < t < 2600:
                sp = (t - 2000) / 600.0
                sx = -r.width() * 0.3 + sp * r.width() * 1.6
                sweep = QLinearGradient(sx, 0, sx + r.width() * 0.4, r.height())
                sweep.setColorAt(0.0, QColor(244, 224, 178, 0))
                sweep.setColorAt(0.5, QColor(244, 224, 178, 80))
                sweep.setColorAt(1.0, QColor(244, 224, 178, 0))
                p.fillRect(r, sweep)
        except Exception as exc:
            log.error("overlay: %s", exc)
        finally:
            if p.isActive():
                p.end()
