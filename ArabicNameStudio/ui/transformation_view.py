import random, math, logging
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QTimer, QPointF, Signal
from PySide6.QtGui import QPainter, QColor, QFont, QRadialGradient, QPen

class _Glyph:
    __slots__ = ("ch","x","y","tx","ty","a","s","delay")
    def __init__(self, ch, x, y, tx, ty, delay):
        self.ch = ch; self.x = x; self.y = y
        self.tx = tx; self.ty = ty
        self.a = 0.0; self.s = 0.3; self.delay = delay

class TransformationView(QWidget):
    finished = Signal(str)

    def __init__(self, arabic_font="Arial", parent=None):
        super().__init__(parent)
        self.arabic_font = arabic_font
        self._phase = 0          # 0=english, 1=dissolve, 2=arabic, 3=done
        self._t = 0.0
        self._timer = QTimer(self); self._timer.timeout.connect(self._step)
        self._en_text = ""; self._ar_text = ""
        self._glyphs = []
        self._particles = []

    def start(self, en, ar):
        self._en_text = en; self._ar_text = ar
        self._phase = 0; self._t = 0.0
        self._glyphs.clear(); self._particles.clear()
        cx, cy = self.width()/2, self.height()/2
        # arabic target positions
        n = len(ar)
        for i, ch in enumerate(ar):
            tx = cx + (i - n/2 + 0.5) * 52
            ty = cy + random.uniform(-20, 20)
            sx = random.uniform(0, self.width())
            sy = random.uniform(0, self.height())
            self._glyphs.append(_Glyph(ch, sx, sy, tx, ty, i * 0.06))
        # particles
        for _ in range(60):
            self._particles.append({
                "x": cx + random.uniform(-180,180),
                "y": cy + random.uniform(-60,60),
                "vx": random.uniform(-1.5,1.5),
                "vy": random.uniform(-1.5,1.5),
                "r": random.uniform(1,3),
                "a": random.randint(40,120),
            })
        self._timer.start(28)

    def _step(self):
        self._t += 0.028
        if self._phase == 0 and self._t > 1.2:
            self._phase = 1; self._t = 0.0
        elif self._phase == 1 and self._t > 1.8:
            self._phase = 2; self._t = 0.0
        elif self._phase == 2 and self._t > 1.6:
            self._phase = 3; self._timer.stop()
            self.finished.emit(self._ar_text)
        # update glyphs
        for g in self._glyphs:
            if self._phase >= 2:
                dt = max(0, self._t - g.delay)
                ease = min(1.0, dt / 0.8)
                ease = ease * ease * (3 - 2 * ease)  # smoothstep
                g.x += (g.tx - g.x) * ease * 0.18
                g.y += (g.ty - g.y) * ease * 0.18
                g.a = min(1.0, g.a + 0.04)
                g.s = min(1.0, g.s + 0.03)
        # update particles
        for p in self._particles:
            p["x"] += p["vx"]; p["y"] += p["vy"]
            p["vx"] *= 0.99; p["vy"] *= 0.99
        self.update()

    def paintEvent(self, ev):
        painter = QPainter(self)
        try:
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setRenderHint(QPainter.TextAntialiasing)
            painter.fillRect(self.rect(), QColor("#0a0a0f"))

            cx, cy = self.width()/2, self.height()/2

            # ambient glow
            rg = QRadialGradient(cx, cy, 220)
            rg.setColorAt(0, QColor(212,175,55, 18))
            rg.setColorAt(1, QColor(0,0,0,0))
            painter.setPen(Qt.NoPen); painter.setBrush(rg)
            painter.drawRect(self.rect())

            # particles
            for p in self._particles:
                a = p["a"] if self._phase < 3 else max(0, p["a"] - 80)
                painter.setBrush(QColor(212,175,55, a))
                painter.drawEllipse(QPointF(p["x"], p["y"]), p["r"], p["r"])

            # phase 0: english text
            if self._phase == 0:
                fade = min(1.0, self._t / 0.5)
                painter.setPen(QColor(245, 245, 247, int(255 * fade)))
                painter.setFont(QFont("Arial", 36, QFont.Light))
                painter.drawText(self.rect(), Qt.AlignCenter, self._en_text)

            # phase 1: dissolve english
            elif self._phase == 1:
                fade = max(0.0, 1.0 - self._t / 1.0)
                blur = int(self._t * 12)
                painter.setPen(QColor(245, 245, 247, int(255 * fade)))
                painter.setFont(QFont("Arial", 36 + blur, QFont.Light))
                painter.drawText(self.rect(), Qt.AlignCenter, self._en_text)

                # stage label
                la = min(1.0, max(0, self._t - 0.5)) * 255
                painter.setPen(QColor(212,175,55, int(la)))
                painter.setFont(QFont("Arial", 14))
                painter.drawText(
                    self.rect().adjusted(0, 120, 0, 0), Qt.AlignHCenter,
                    "Transforming into Arabic…"
                )

            # phase 2: arabic assembly
            elif self._phase >= 2:
                painter.setLayoutDirection(Qt.RightToLeft)
                font = QFont(self.arabic_font, 64, QFont.Bold)
                font.setStyleHint(QFont.Serif)
                painter.setFont(font)
                for g in self._glyphs:
                    a = int(255 * g.a)
                    painter.setPen(QColor("#D4AF37"))
                    painter.setOpacity(g.a)
                    sz = 64 * g.s
                    f2 = QFont(self.arabic_font, int(sz), QFont.Bold)
                    f2.setStyleHint(QFont.Serif)
                    painter.setFont(f2)
                    painter.drawText(
                        int(g.x - sz), int(g.y - sz/2), int(sz*2), int(sz*2),
                        Qt.AlignCenter, g.ch
                    )
                painter.setOpacity(1.0)

        except Exception as e:
            logging.getLogger("Studio").error("Transform paint: %s", e)
        finally:
            if painter.isActive(): painter.end()
