"""
Brown & Gold luxury design system: palette, spacing, radii, shared shadows and
hairlines, an 8-pointed-star Islamic tessellation generator, a gold-leaf gradient
helper, a calligraphic divider, a circular progress ring, spring/elastic easing,
and a glass (blur) helper. Every screen consumes these so the whole app feels
like one cohesive product.
"""
import math
from PySide6.QtCore import Qt, QPointF, QRectF, QEasingCurve
from PySide6.QtWidgets import QGraphicsBlurEffect
from PySide6.QtGui import (
    QColor, QLinearGradient, QRadialGradient, QPainter, QPainterPath, QPen,
    QBrush, QFont, QPixmap,
)

def _resolve_spacing_type():
    enum_cls = getattr(QFont, "SpacingType", None)
    if enum_cls is not None:
        v = getattr(enum_cls, "PercentageSpacing", None)
        if v is not None:
            return v
    v = getattr(QFont, "PercentageSpacing", None)
    if v is not None:
        return v
    if enum_cls is not None:
        try:
            return enum_cls(1)
        except Exception:
            pass
    return 1


PCT_SPACING = _resolve_spacing_type()


# -- palette -----------------------------------------------------------------
WALNUT_DEEP = QColor(24, 15, 9)
WALNUT = QColor(38, 24, 15)
MOCHA = QColor(58, 37, 23)
COFFEE = QColor(78, 51, 32)
CAMEL = QColor(140, 96, 58)
SAND = QColor(196, 160, 116)
PARCHMENT = QColor(233, 213, 178)
IVORY = QColor(245, 236, 219)
CREAM = QColor(250, 244, 232)
GOLD = QColor(201, 162, 79)
GOLD_BRIGHT = QColor(233, 200, 122)
GOLD_CHAMPAGNE = QColor(244, 224, 178)
GOLD_DEEP = QColor(140, 105, 45)
BRONZE = QColor(120, 84, 44)
INK = QColor(28, 18, 10)
TEXT_PRIMARY = IVORY
TEXT_SECONDARY = QColor(214, 196, 168)
TEXT_MUTED = QColor(170, 150, 122)

# -- spacing & radius --------------------------------------------------------
SP = {"xs": 4, "sm": 8, "md": 16, "lg": 24, "xl": 40, "xxl": 64}
RADIUS = {"sm": 10, "md": 16, "lg": 24, "xl": 32}


def font_display(size, weight=QFont.Medium, italic=False):
    f = QFont("Seravek", size, weight)
    f.setStyleHint(QFont.Serif)
    f.setItalic(italic)
    f.setLetterSpacing(PCT_SPACING, 101)
    return f


def font_ui(size, weight=QFont.Normal):
    f = QFont("Optima", size, weight)
    f.setStyleHint(QFont.SansSerif)
    return f


def shadow(painter, rect, radius, color=QColor(0, 0, 0, 120), blur=18, dy=10):
    painter.save()
    painter.setPen(Qt.NoPen)
    painter.setBrush(color)
    for i in range(3):
        r = rect.adjusted(-i * (blur / 3), -i * (blur / 3), i * (blur / 3), i * (blur / 3))
        r = r.translated(0, dy * (1 - i * 0.25))
        painter.setOpacity(0.35 - i * 0.1)
        painter.drawRoundedRect(r, radius, radius)
    painter.restore()


def hairline(painter, rect, radius, color=None):
    if color is None:
        color = QColor(201, 162, 79, 60)
    painter.save()
    painter.setPen(QPen(color, 1.0))
    painter.setBrush(Qt.NoBrush)
    painter.drawRoundedRect(rect.adjusted(0.5, 0.5, -0.5, -0.5), radius, radius)
    painter.restore()


def gold_leaf_gradient(rect, angle=90.0):
    g = QLinearGradient(rect.topLeft(), rect.bottomLeft())
    if abs(angle - 45) < 1:
        g = QLinearGradient(rect.topLeft(), rect.bottomRight())
    g.setColorAt(0.00, GOLD_CHAMPAGNE)
    g.setColorAt(0.22, GOLD_BRIGHT)
    g.setColorAt(0.50, GOLD)
    g.setColorAt(0.78, GOLD_DEEP)
    g.setColorAt(1.00, BRONZE)
    return g


def make_star_tile(size=180, line=None, alpha=26):
    if line is None:
        line = QColor(201, 162, 79, alpha)
    pix = QPixmap(size, size)
    pix.fill(Qt.transparent)
    p = QPainter(pix)
    try:
        p.setRenderHint(QPainter.Antialiasing)
        p.setPen(QPen(line, 1.0))
        p.setBrush(Qt.NoBrush)
        c = size / 2.0
        r = size * 0.42
        p.save()
        p.translate(c, c)
        half = r * 0.7071
        p.drawRect(QRectF(-half, -half, half * 2, half * 2))
        p.rotate(45)
        p.drawRect(QRectF(-half, -half, half * 2, half * 2))
        p.restore()
        p.drawEllipse(QPointF(c, c), r * 0.55, r * 0.55)
        p.drawEllipse(QPointF(c, c), r * 0.92, r * 0.92)
        for cx, cy in ((0, 0), (size, 0), (0, size), (size, size)):
            p.drawEllipse(QPointF(cx, cy), r * 0.5, r * 0.5)
    finally:
        if p.isActive():
            p.end()
    return pix


def calligraphic_divider(painter, cx, cy, width, color=None, alpha=1.0):
    if color is None:
        color = GOLD
    col = QColor(color)
    col.setAlphaF(col.alphaF() * alpha)
    hw = width / 2.0
    painter.save()
    painter.setRenderHint(QPainter.Antialiasing)
    pen = QPen(col, 1.6)
    pen.setCapStyle(Qt.RoundCap)
    painter.setPen(pen)
    painter.setBrush(Qt.NoBrush)
    path = QPainterPath()
    path.moveTo(cx - hw, cy)
    path.cubicTo(QPointF(cx - hw * 0.4, cy - 6), QPointF(cx - hw * 0.15, cy + 6), QPointF(cx, cy))
    path.cubicTo(QPointF(cx + hw * 0.15, cy - 6), QPointF(cx + hw * 0.4, cy + 6), QPointF(cx + hw, cy))
    painter.drawPath(path)
    painter.setPen(Qt.NoPen)
    painter.setBrush(col)
    painter.save()
    painter.translate(cx, cy)
    painter.rotate(45)
    painter.drawRect(QRectF(-3.2, -3.2, 6.4, 6.4))
    painter.restore()
    for ex in (cx - hw, cx + hw):
        painter.drawEllipse(QPointF(ex, cy), 2.2, 2.2)
    painter.restore()


class ProgressRing:
    @staticmethod
    def draw(painter, cx, cy, radius, progress, color=None, width=3.0):
        if color is None:
            color = GOLD
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)
        track = QColor(color)
        track.setAlphaF(0.18)
        painter.setPen(QPen(track, width))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(QPointF(cx, cy), radius, radius)
        pen = QPen(color, width)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        span = int(-progress * 360 * 16)
        painter.drawArc(QRectF(cx - radius, cy - radius, radius * 2, radius * 2), 90 * 16, span)
        painter.restore()


def spring_easing(overshoot=1.4):
    return QEasingCurve(QEasingCurve.OutBack)


def glass_effect(radius=18, blur=22):
    fx = QGraphicsBlurEffect()
    fx.setBlurRadius(blur)
    return fx
