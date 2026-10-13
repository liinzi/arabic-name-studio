"""
Premium action bar. Icons are vector QPainterPaths (no font glyphs / assets),
HiDPI-crisp and theme-coloured. The text is drawn FIRST in a guarded block so an
icon-drawing failure can never hide the label; _draw_icon is fully exception-safe
and its refresh arrowhead uses analytic geometry (no fragile pointAt).
"""
import math
import logging
from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton
from PySide6.QtCore import (
    Signal, Qt, QPropertyAnimation, QEasingCurve, QPointF, QRectF, Property,
)
from PySide6.QtGui import (
    QColor, QPainter, QPen, QLinearGradient, QFont, QFontMetricsF, QPainterPath,
)
from ui.theme import font_ui


def _draw_icon(painter, kind, r, color):
    """Draw a crisp vector glyph inside square rect r. Fully exception-safe."""
    painter.save()
    try:
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(color, max(1.4, r.height() * 0.12))
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        x0, y0, W, H = r.x(), r.y(), r.width(), r.height()

        def P(nx, ny):
            return QPointF(x0 + nx * W, y0 + ny * H)

        if kind == "copy":
            back = QPainterPath()
            back.moveTo(P(0.34, 0.16))
            back.lineTo(P(0.82, 0.16))
            back.lineTo(P(0.82, 0.64))
            painter.drawPath(back)
            painter.drawRoundedRect(QRectF(x0 + 0.16 * W, y0 + 0.34 * H, 0.52 * W, 0.52 * H), 2.5, 2.5)
        elif kind == "save":
            tray = QPainterPath()
            tray.moveTo(P(0.18, 0.60))
            tray.lineTo(P(0.18, 0.84))
            tray.lineTo(P(0.82, 0.84))
            tray.lineTo(P(0.82, 0.60))
            painter.drawPath(tray)
            painter.drawLine(P(0.50, 0.14), P(0.50, 0.60))
            arrow = QPainterPath()
            arrow.moveTo(P(0.32, 0.42))
            arrow.lineTo(P(0.50, 0.62))
            arrow.lineTo(P(0.68, 0.42))
            painter.drawPath(arrow)
        elif kind == "regen":
            cx = x0 + 0.5 * W
            cy = y0 + 0.5 * H
            rx = 0.34 * W
            ry = 0.34 * H
            rin = QRectF(cx - rx, cy - ry, 2 * rx, 2 * ry)
            start = 50.0
            sweep = 300.0
            path = QPainterPath()
            path.arcMoveTo(rin, start)
            path.arcTo(rin, start, sweep)
            painter.drawPath(path)
            a = math.radians(start + sweep)
            ex = cx + rx * math.cos(a)
            ey = cy - ry * math.sin(a)
            txx = -rx * math.sin(a)
            tyy = -ry * math.cos(a)
            ln = math.hypot(txx, tyy) or 1.0
            ux, uy = txx / ln, tyy / ln
            blen = r.height() * 0.26
            for sgn in (1.0, -1.0):
                ang = 2.6 * sgn
                ca, sa = math.cos(ang), math.sin(ang)
                bx = -(ux * ca - uy * sa)
                by = -(ux * sa + uy * ca)
                painter.drawLine(QPointF(ex, ey), QPointF(ex + bx * blen, ey + by * blen))
        elif kind == "back":
            painter.drawLine(P(0.78, 0.50), P(0.26, 0.50))
            chev = QPainterPath()
            chev.moveTo(P(0.46, 0.28))
            chev.lineTo(P(0.22, 0.50))
            chev.lineTo(P(0.46, 0.72))
            painter.drawPath(chev)
    except Exception as exc:
        logging.error("icon draw (%s): %s", kind, exc)
    finally:
        painter.restore()


class TactileButton(QPushButton):
    def __init__(self, text, icon=None, parent=None):
        super().__init__(text, parent)
        self._icon = icon
        self._hover = 0.0
        self._press = 0.0
        self._ripple = 0.0
        self._ripple_op = 0.0
        self._ripple_center = QPointF(0, 0)

        self.hover_anim = QPropertyAnimation(self, b"hover_val")
        self.hover_anim.setDuration(220)
        self.hover_anim.setEasingCurve(QEasingCurve.OutCubic)
        self.press_anim = QPropertyAnimation(self, b"press_val")
        self.press_anim.setDuration(130)
        self.ripple_anim = QPropertyAnimation(self, b"ripple_val")
        self.ripple_anim.setDuration(560)
        self.ripple_anim.setEasingCurve(QEasingCurve.OutCubic)
        self.ripple_fade = QPropertyAnimation(self, b"ripple_op_val")
        self.ripple_fade.setDuration(560)

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

    def enterEvent(self, e):
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
        self._ripple_center = QPointF(e.pos())
        self.ripple_anim.stop()
        self.ripple_anim.setStartValue(0.0)
        self.ripple_anim.setEndValue(180.0)
        self.ripple_anim.start()
        self.ripple_fade.stop()
        self.ripple_fade.setStartValue(0.4)
        self.ripple_fade.setEndValue(0.0)
        self.ripple_fade.start()
        self.press_anim.stop()
        self.press_anim.setStartValue(self._press)
        self.press_anim.setEndValue(1.0)
        self.press_anim.start()
        super().mousePressEvent(e)

    def mouseReleaseEvent(self, e):
        self.press_anim.stop()
        self.press_anim.setStartValue(self._press)
        self.press_anim.setEndValue(0.0)
        self.press_anim.start()
        super().mouseReleaseEvent(e)

    def paintEvent(self, e):
        p = QPainter(self)
        try:
            p.setRenderHint(QPainter.RenderHint.Antialiasing)
            r = QRectF(self.rect())
            radius = 16.0
            lift = self._hover * 2 - self._press * 1.5
            rr = r.adjusted(2, 2 - lift, -2, -2 - lift)

            p.setPen(Qt.NoPen)
            p.setBrush(QColor(0, 0, 0, int(60 - self._press * 25)))
            p.drawRoundedRect(rr.adjusted(3, 6 + self._hover * 3, -3, -1), radius, radius)

            body = QLinearGradient(0, 0, 0, rr.height())
            body.setColorAt(0.0, QColor(78, 51, 32, int(150 + self._hover * 40)))
            body.setColorAt(1.0, QColor(38, 24, 15, int(170 + self._hover * 30)))
            p.setBrush(body)
            border = QColor(201, 162, 79, int(50 + self._hover * 110))
            p.setPen(QPen(border, 1.1))
            p.drawRoundedRect(rr, radius, radius)

            if self._ripple_op > 0.01:
                p.setPen(Qt.NoPen)
                p.setBrush(QColor(244, 224, 178, int(self._ripple_op * 255)))
                p.drawEllipse(self._ripple_center, self._ripple, self._ripple)

            if self._hover > 0.5:
                textcolor = QColor(244, 224, 178)
            else:
                textcolor = QColor(245, 236, 219, int(200 + self._hover * 55))

            # layout the icon+label as one centred group
            label = self.text()
            f = font_ui(13, QFont.DemiBold)
            p.setFont(f)
            fm = QFontMetricsF(f)
            textw = fm.horizontalAdvance(label)
            icon_sz = 16.0
            gap = 9.0
            have_icon = bool(self._icon)
            total = (icon_sz + gap + textw) if have_icon else textw
            gx = rr.center().x() - total / 2.0
            if gx < rr.x() + 6:
                gx = rr.x() + 6
            cy = rr.center().y()
            tx = (gx + icon_sz + gap) if have_icon else gx
            trect = QRectF(tx, rr.y(), max(0.0, rr.right() - 6.0 - tx), rr.height())

            # TEXT FIRST and guarded: it must never be skipped by an icon error
            p.setPen(textcolor)
            try:
                p.drawText(trect, Qt.AlignLeft | Qt.AlignVCenter, label)
            except Exception as ex2:
                logging.error("TactileButton text: %s", ex2)

            # ICON SECOND and guarded
            if have_icon:
                _draw_icon(p, self._icon, QRectF(gx, cy - icon_sz / 2.0, icon_sz, icon_sz), textcolor)
        except Exception as exc:
            logging.error("TactileButton paint: %s", exc)
        finally:
            if p.isActive():
                p.end()


class ActionBar(QWidget):
    copy_clicked = Signal()
    regen_clicked = Signal()
    save_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.arabic_text = ""
        self._init_ui()

    def _init_ui(self):
        layout = QHBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(16)
        layout.setContentsMargins(0, 12, 0, 12)

        self.btn_copy = TactileButton("Copy Text", icon="copy")
        self.btn_copy.setFixedSize(160, 48)
        self.btn_copy.setCursor(Qt.PointingHandCursor)
        self.btn_copy.clicked.connect(self._emit_copy)

        self.btn_regen = TactileButton("Regenerate", icon="regen")
        self.btn_regen.setFixedSize(160, 48)
        self.btn_regen.setCursor(Qt.PointingHandCursor)
        self.btn_regen.clicked.connect(self._emit_regen)

        self.btn_save = TactileButton("Save PNG", icon="save")
        self.btn_save.setFixedSize(160, 48)
        self.btn_save.setCursor(Qt.PointingHandCursor)
        self.btn_save.clicked.connect(self._emit_save)

        layout.addWidget(self.btn_copy)
        layout.addWidget(self.btn_regen)
        layout.addWidget(self.btn_save)

    def _emit_copy(self):
        try:
            self.copy_clicked.emit()
        except Exception as exc:
            logging.error("Copy signal error: %s", exc)

    def _emit_regen(self):
        try:
            self.regen_clicked.emit()
        except Exception as exc:
            logging.error("Regen signal error: %s", exc)

    def _emit_save(self):
        try:
            self.save_clicked.emit()
        except Exception as exc:
            logging.error("Save signal error: %s", exc)

    def set_arabic_text(self, text):
        self.arabic_text = text
