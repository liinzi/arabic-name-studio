"""
Ambient warm golden-dust field with soft glowing orbs and a slow light sweep.
Calm, low-opacity, never distracting.
"""
import random
import math
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import QTimer, Qt, QPointF, QRectF
from PySide6.QtGui import QPainter, QColor, QLinearGradient, QRadialGradient
import logging


class _Mote:
    __slots__ = ["x", "y", "vx", "vy", "size", "opacity", "life", "max_life", "glow"]

    def __init__(self, w, h):
        self.reset(w, h, True)

    def reset(self, w, h, initial=False):
        self.x = random.uniform(0, w)
        self.y = random.uniform(0, h) if initial else h + 20
        self.vx = random.uniform(-0.12, 0.12)
        self.vy = random.uniform(-0.28, -0.04)
        self.glow = random.random() < 0.18
        self.size = random.uniform(2.5, 6.0) if self.glow else random.uniform(0.8, 2.2)
        self.opacity = random.uniform(0.10, 0.34)
        self.life = random.uniform(500, 1100)
        self.max_life = self.life


class ParticleWidget(QWidget):
    def __init__(self, count=55, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self._motes = []
        self._count = count
        self._sweep = 0.0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)

    def showEvent(self, event):
        super().showEvent(event)
        w, h = max(self.width(), 1), max(self.height(), 1)
        if not self._motes:
            self._motes = [_Mote(w, h) for _ in range(self._count)]
        if not self._timer.isActive():
            self._timer.start(33)

    def hideEvent(self, event):
        self._timer.stop()
        super().hideEvent(event)

    def _tick(self):
        w, h = max(self.width(), 1), max(self.height(), 1)
        for m in self._motes:
            m.x += m.vx
            m.y += m.vy
            m.life -= 1
            if m.life <= 0 or m.y < -20:
                m.reset(w, h)
        self._sweep += 0.0016
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        try:
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setRenderHint(QPainter.SmoothPixmapTransform)
            w, h = self.width(), self.height()

            # slow diagonal light sweep
            phase = (self._sweep % 1.0)
            sx = -w * 0.4 + phase * w * 1.8
            sweep = QLinearGradient(sx, 0, sx + w * 0.5, h)
            sweep.setColorAt(0.0, QColor(233, 200, 122, 0))
            sweep.setColorAt(0.5, QColor(233, 200, 122, 10))
            sweep.setColorAt(1.0, QColor(233, 200, 122, 0))
            painter.fillRect(QRectF(0, 0, w, h), sweep)

            painter.setPen(Qt.NoPen)
            for m in self._motes:
                fade = min(1.0, m.life / (m.max_life * 0.3))
                alpha = int(m.opacity * fade * 255)
                if alpha < 3:
                    continue
                if m.glow:
                    g = QRadialGradient(QPointF(m.x, m.y), m.size * 2.2)
                    g.setColorAt(0.0, QColor(244, 224, 178, alpha))
                    g.setColorAt(0.4, QColor(233, 200, 122, alpha // 3))
                    g.setColorAt(1.0, QColor(233, 200, 122, 0))
                    painter.setBrush(g)
                    painter.drawEllipse(QPointF(m.x, m.y), m.size * 2.2, m.size * 2.2)
                else:
                    painter.setBrush(QColor(233, 200, 122, alpha))
                    painter.drawEllipse(QPointF(m.x, m.y), m.size, m.size)
        except Exception as exc:
            logging.error("Particle paint error: %s", exc)
        finally:
            if painter.isActive():
                painter.end()
