"""
Brand integration with guaranteed visibility. Uses the real logo if present at
assets/logo.png; otherwise generates an elegant procedural gold crest so branding
is always clearly visible. Layered composition: ambient glow + right-anchored
large crest + faint centered crest + crisp corner badge. Non-interactive.
"""
import os
import math
from PySide6.QtWidgets import QWidget
from PySide6.QtGui import (QImage, QPixmap, QColor, QPainter, QRadialGradient,
                           QPainterPath, QPen)
from PySide6.QtCore import Qt

LOGO_CANDIDATES = ["assets/logo.png", "assets/logo.jpg", "assets/logo.jpeg",
                   "logo.png", "logo.jpg", "logo.jpeg"]
GOLD = QColor(212, 175, 55)


def find_logo(base_dir):
    for c in LOGO_CANDIDATES:
        p = os.path.join(base_dir, c)
        if os.path.isfile(p):
            return p
    return None


def _remove_white_bg(img):
    img = img.convertToFormat(QImage.Format.Format_ARGB32)
    try:
        import numpy as np
        w, h = img.width(), img.height()
        bpl = img.bytesPerLine()
        ptr = img.bits(); ptr.setsize(h * bpl)
        arr = np.frombuffer(ptr, dtype=np.uint8).reshape(h, bpl)
        rgba = arr[:, :w * 4].reshape(h, w, 4).astype(np.int16)
        white = (rgba[:, :, 0] > 235) & (rgba[:, :, 1] > 235) & (rgba[:, :, 2] > 235)
        rgba[:, :, 3] = np.where(white, 0, rgba[:, :, 3])
        arr[:, :w * 4] = rgba.astype(np.uint8).reshape(h, w * 4)
        return img
    except Exception:
        for y in range(img.height()):
            for x in range(img.width()):
                c = img.pixelColor(x, y)
                if c.red() > 235 and c.green() > 235 and c.blue() > 235:
                    c.setAlpha(0); img.setPixelColor(x, y, c)
        return img


def _star_path(cx, cy, r):
    p = QPainterPath()
    for i in range(10):
        ang = -math.pi / 2 + i * math.pi / 5
        rr = r if i % 2 == 0 else r * 0.45
        x, y = cx + rr * math.cos(ang), cy + rr * math.sin(ang)
        if i == 0:
            p.moveTo(x, y)
        else:
            p.lineTo(x, y)
    p.closeSubpath()
    return p


def _procedural_crest():
    """Elegant gold crest fallback mirroring the organization's emblem language."""
    S = 560
    img = QImage(S, S, QImage.Format.Format_ARGB32)
    img.fill(QColor(0, 0, 0, 0))
    p = QPainter(img)
    try:
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        # shield
        sh = QPainterPath()
        sh.moveTo(S * 0.5, S * 0.05)
        sh.lineTo(S * 0.87, S * 0.19)
        sh.lineTo(S * 0.87, S * 0.52)
        sh.cubicTo(S * 0.87, S * 0.78, S * 0.68, S * 0.90, S * 0.5, S * 0.97)
        sh.cubicTo(S * 0.32, S * 0.90, S * 0.13, S * 0.78, S * 0.13, S * 0.52)
        sh.lineTo(S * 0.13, S * 0.19)
        sh.closeSubpath()
        p.setPen(QPen(GOLD, 16)); p.setBrush(Qt.NoBrush); p.drawPath(sh)
        p.setPen(QPen(GOLD, 5)); p.drawPath(sh)
        # quadrant dividers
        p.setPen(QPen(GOLD, 6))
        p.drawLine(int(S * 0.5), int(S * 0.10), int(S * 0.5), int(S * 0.92))
        p.drawLine(int(S * 0.18), int(S * 0.5), int(S * 0.82), int(S * 0.5))
        p.setPen(Qt.NoPen); p.setBrush(GOLD)
        # crescent + star (top-left)
        outer = QPainterPath(); outer.addEllipse(S * 0.26, S * 0.26, S * 0.18, S * 0.18)
        inner = QPainterPath(); inner.addEllipse(S * 0.31, S * 0.25, S * 0.15, S * 0.15)
        p.drawPath(outer.subtracted(inner))
        p.drawPath(_star_path(S * 0.40, S * 0.35, S * 0.045))
        # open book (top-right)
        bk = QPainterPath()
        bk.moveTo(S * 0.60, S * 0.30); bk.cubicTo(S * 0.66, S * 0.26, S * 0.72, S * 0.26, S * 0.78, S * 0.30)
        bk.lineTo(S * 0.78, S * 0.42); bk.cubicTo(S * 0.72, S * 0.38, S * 0.66, S * 0.38, S * 0.60, S * 0.42)
        bk.closeSubpath()
        p.drawPath(bk)
        p.setPen(QPen(GOLD, 5)); p.drawLine(int(S * 0.69), int(S * 0.28), int(S * 0.69), int(S * 0.40))
        # three stars (bottom-left)
        for (cx, cy) in ((0.32, 0.62), (0.40, 0.70), (0.30, 0.76)):
            p.drawPath(_star_path(S * cx, S * cy, S * 0.035))
        # tree (bottom-right)
        p.drawEllipse(S * 0.62, S * 0.60, S * 0.16, S * 0.13)
        p.drawRect(S * 0.685, S * 0.72, S * 0.03, S * 0.10)
    finally:
        if p.isActive():
            p.end()
    return img


def load_processed_logo(base_dir):
    path = find_logo(base_dir)
    if path:
        proc = os.path.join(os.path.dirname(path), "logo_processed.png")
        try:
            if os.path.isfile(proc) and os.path.getmtime(proc) >= os.path.getmtime(path):
                img = QImage(proc)
                if not img.isNull():
                    return img
            img = QImage(path)
            if not img.isNull():
                if max(img.width(), img.height()) > 800:
                    img = img.scaled(800, 800, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                img = _remove_white_bg(img)
                img.save(proc)
                return img
        except Exception:
            pass
    return _procedural_crest()  # guaranteed fallback


class BrandOverlay(QWidget):
    def __init__(self, base_dir, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._wm = QPixmap.fromImage(load_processed_logo(base_dir))

    def showEvent(self, e):
        self.raise_()
        super().showEvent(e)

    def paintEvent(self, event):
        if self._wm.isNull():
            return
        p = QPainter(self)
        try:
            p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
            p.setRenderHint(QPainter.RenderHint.Antialiasing)
            w, h = self.width(), self.height()
            if w < 40 or h < 40:
                return

            # ambient glow
            glow = QRadialGradient(w * 0.5, h * 0.5, min(w, h) * 0.6)
            glow.setColorAt(0.0, QColor(212, 175, 55, 30))
            glow.setColorAt(0.6, QColor(212, 175, 55, 12))
            glow.setColorAt(1.0, QColor(212, 175, 55, 0))
            p.setPen(Qt.NoPen); p.setBrush(glow); p.drawRect(0, 0, w, h)

            # large right-anchored crest, partially cropped (clearly visible)
            big = self._wm.scaledToHeight(int(h * 0.85), Qt.SmoothTransformation)
            p.setOpacity(0.16)
            p.drawPixmap(w - int(big.width() * 0.72), int((h - big.height()) / 2), big)

            # faint centered crest for balance
            mid = self._wm.scaledToHeight(int(min(w, h) * 0.6), Qt.SmoothTransformation)
            p.setOpacity(0.08)
            p.drawPixmap(int((w - mid.width()) / 2), int((h - mid.height()) / 2), mid)

            # crisp glowing corner badge
            badge = self._wm.scaledToHeight(96, Qt.SmoothTransformation)
            bx, by = w - badge.width() - 26, 22
            bg = QRadialGradient(bx + badge.width() / 2.0, by + badge.height() / 2.0, 110)
            bg.setColorAt(0.0, QColor(212, 175, 55, 50))
            bg.setColorAt(1.0, QColor(212, 175, 55, 0))
            p.setOpacity(1.0); p.setBrush(bg); p.setPen(Qt.NoPen)
            p.drawRect(bx - 70, by - 70, badge.width() + 140, badge.height() + 140)
            p.setOpacity(0.70)
            p.drawPixmap(bx, by, badge)
            p.setOpacity(1.0)
        except Exception:
            pass
        finally:
            if p.isActive():
                p.end()
