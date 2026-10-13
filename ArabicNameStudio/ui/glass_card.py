"""
Clean premium render card: soft elevation shadow + simple frame + field + subtle
lighting/vignette. The decorative corner brackets / arabesque tile / extra
hairline surround have been removed so the calligraphy is the sole focal point.
"""
import logging
from PySide6.QtWidgets import QWidget, QVBoxLayout, QSizePolicy
from PySide6.QtCore import Qt, QPointF, QRectF, QTimer
from PySide6.QtGui import (
    QPainter, QColor, QPen, QRadialGradient, QLinearGradient,
)
from rendering.calligraphy import CalligraphyWidget

log = logging.getLogger("ui.card")


class PresentationCard(QWidget):
    def __init__(self, font_family="Arial", parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self._target = QPointF(0, 0)
        self._current = QPointF(0, 0)

        self.calligraphy = CalligraphyWidget(font_family, self)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(56, 56, 56, 56)
        layout.addWidget(self.calligraphy)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._interpolate)
        self._timer.start(16)

    def set_text(self, text):
        self.calligraphy.set_text(text)

    def start_animation(self):
        self.calligraphy.start_animation()

    def mouseMoveEvent(self, event):
        self._target = QPointF(event.pos())

    def leaveEvent(self, event):
        self._target = QPointF(self.width() / 2.0, self.height() / 2.0)

    def resizeEvent(self, event):
        self._target = QPointF(self.width() / 2.0, self.height() / 2.0)
        self._current = QPointF(self._target)
        super().resizeEvent(event)

    def _interpolate(self):
        dx = self._target.x() - self._current.x()
        dy = self._target.y() - self._current.y()
        if abs(dx) > 0.05 or abs(dy) > 0.05:
            self._current.setX(self._current.x() + dx * 0.05)
            self._current.setY(self._current.y() + dy * 0.05)
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        try:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
            rect = self.rect()
            cx = self.width() / 2.0
            cy = self.height() / 2.0
            ndx = (self._current.x() - cx) / max(cx, 1.0)
            ndy = (self._current.y() - cy) / max(cy, 1.0)
            offset = QPointF(ndx * 16.0, ndy * 16.0)

            outer = QRectF(rect.adjusted(40, 40, -40, -40))
            shadow = outer.translated(offset)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(0, 0, 0, 90))
            painter.drawRoundedRect(shadow.translated(6, 16), 30, 30)
            painter.setBrush(QColor(0, 0, 0, 130))
            painter.drawRoundedRect(shadow, 30, 30)

            frame = QLinearGradient(0, outer.top(), 0, outer.bottom())
            frame.setColorAt(0.0, QColor(78, 51, 32))
            frame.setColorAt(0.5, QColor(58, 37, 23))
            frame.setColorAt(1.0, QColor(38, 24, 15))
            painter.setBrush(frame)
            painter.setPen(QPen(QColor(233, 200, 122, 90), 1.2))
            painter.drawRoundedRect(outer, 28, 28)

            inner = outer.adjusted(16, 16, -16, -16)
            field = QLinearGradient(0, inner.top(), 0, inner.bottom())
            field.setColorAt(0.0, QColor(48, 31, 19))
            field.setColorAt(0.5, QColor(36, 23, 14))
            field.setColorAt(1.0, QColor(28, 18, 11))
            painter.setBrush(field)
            painter.setPen(QPen(QColor(201, 162, 79, 60), 1.0))
            painter.drawRoundedRect(inner, 20, 20)

            hl = QRadialGradient(self._current, max(self.width(), self.height()) * 0.55)
            hl.setColorAt(0.0, QColor(233, 200, 122, 34))
            hl.setColorAt(0.5, QColor(140, 105, 45, 12))
            hl.setColorAt(1.0, QColor(0, 0, 0, 0))
            painter.setPen(Qt.NoPen)
            painter.setBrush(hl)
            painter.drawRoundedRect(inner, 20, 20)

            vg = QRadialGradient(QPointF(cx, cy), max(self.width(), self.height()) * 0.75)
            vg.setColorAt(0.0, QColor(0, 0, 0, 0))
            vg.setColorAt(0.72, QColor(0, 0, 0, 0))
            vg.setColorAt(1.0, QColor(8, 5, 2, 140))
            painter.setBrush(vg)
            painter.drawRoundedRect(inner, 20, 20)
        except Exception as exc:
            log.error("card paint: %s", exc)
        finally:
            if painter.isActive():
                painter.end()
