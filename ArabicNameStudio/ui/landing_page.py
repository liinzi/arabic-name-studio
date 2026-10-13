import random, math, logging
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QHBoxLayout
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QPointF, Property
from PySide6.QtGui import (
    QPainter, QColor, QPen, QRadialGradient, QFont,
    QGraphicsDropShadowEffect, QPainterPath,
)

class _Particle:
    __slots__ = ("x","y","vx","vy","r","a")
    def __init__(self, w, h):
        self.x = random.uniform(0, w)
        self.y = random.uniform(0, h)
        self.vx = random.uniform(-0.15, 0.15)
        self.vy = random.uniform(-0.25, -0.05)
        self.r = random.uniform(1.0, 2.5)
        self.a = random.randint(15, 45)
    def step(self, w, h):
        self.x += self.vx; self.y += self.vy
        if self.y < -10: self.y = h + 10; self.x = random.uniform(0, w)
        if self.x < -10: self.x = w + 10
        if self.x > w + 10: self.x = -10

class LandingPage(QWidget):
    generate_requested = __import__("PySide6").QtCore.Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._intro_alpha = 0.0
        self._particles = [_Particle(1000, 700) for _ in range(30)]
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(33)
        self._placeholder_names = ["Abdullah", "Sophia", "Muhammad", "Olivia", "Khalid", "Emma"]
        self._ph_idx = 0
        self._ph_char = 0
        self._ph_dir = 1
        self._ph_timer = QTimer(self)
        self._ph_timer.timeout.connect(self._cycle_placeholder)
        self._setup_ui()
        self._play_intro()

    # --- intro animation ---
    def _play_intro(self):
        self._intro_anim = QPropertyAnimation(self, b"intro_alpha")
        self._intro_anim.setDuration(1200)
        self._intro_anim.setStartValue(0.0)
        self._intro_anim.setEndValue(1.0)
        self._intro_anim.setEasingCurve(QEasingCurve.OutCubic)
        self._intro_anim.start()
        QTimer.singleShot(600, self._ph_timer.start(120))

    def get_intro_alpha(self): return self._intro_alpha
    def set_intro_alpha(self, v):
        self._intro_alpha = v
        self.title_lbl.setGraphicsEffect(self._make_opacity(v))
        self.sub_lbl.setGraphicsEffect(self._make_opacity(max(0, v - 0.2) * 1.25))
        self.input_row.setGraphicsEffect(self._make_opacity(max(0, v - 0.4) * 1.67))
        self.update()
    intro_alpha = Property(float, get_intro_alpha, set_intro_alpha)

    @staticmethod
    def _make_opacity(a):
        from PySide6.QtWidgets import QGraphicsOpacityEffect
        e = QGraphicsOpacityEffect()
        e.setOpacity(max(0.0, min(1.0, a)))
        return e

    # --- placeholder typing ---
    def _cycle_placeholder(self):
        name = self._placeholder_names[self._ph_idx]
        if self._ph_dir == 1:
            self._ph_char += 1
            if self._ph_char > len(name):
                self._ph_dir = -1
                self._ph_timer.setInterval(1200)
                return
        else:
            self._ph_char -= 1
            if self._ph_char <= 0:
                self._ph_dir = 1
                self._ph_idx = (self._ph_idx + 1) % len(self._placeholder_names)
                self._ph_timer.setInterval(120)
                return
        self.input_field.setPlaceholderText(self._placeholder_names[self._ph_idx][:self._ph_char] + "│")

    # --- UI ---
    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(60, 50, 60, 50)
        root.setAlignment(Qt.AlignCenter)
        root.setSpacing(0)

        self.title_lbl = QLabel("Arabic Name Studio")
        self.title_lbl.setAlignment(Qt.AlignCenter)
        self.title_lbl.setStyleSheet(
            "font-size:46px; font-weight:200; color:#f5f5f7; letter-spacing:3px;"
        )

        self.sub_lbl = QLabel("Transform any name into elegant Arabic calligraphy")
        self.sub_lbl.setAlignment(Qt.AlignCenter)
        self.sub_lbl.setStyleSheet(
            "font-size:16px; color:rgba(245,245,247,0.5); margin-top:12px;"
        )

        # input row
        self.input_row = QWidget()
        ir = QHBoxLayout(self.input_row)
        ir.setContentsMargins(0, 36, 0, 0)
        ir.setSpacing(0)
        ir.setAlignment(Qt.AlignCenter)

        self.input_field = QLineEdit()
        self.input_field.setFixedWidth(420)
        self.input_field.setFixedHeight(56)
        self.input_field.setAlignment(Qt.AlignCenter)
        self.input_field.setStyleSheet("""
            QLineEdit {
                background: rgba(255,255,255,0.04);
                border: 1px solid rgba(255,255,255,0.09);
                border-top-left-radius: 14px; border-bottom-left-radius: 14px;
                border-top-right-radius: 0px; border-bottom-right-radius: 0px;
                padding: 0 24px; color: #f5f5f7; font-size: 18px;
            }
            QLineEdit:focus {
                border: 1px solid rgba(212,175,55,0.55);
                background: rgba(255,255,255,0.07);
            }
        """)
        self.input_field.returnPressed.connect(self._emit)
        self.input_field.textChanged.connect(self._check)

        self.btn = QPushButton("✦  Generate")
        self.btn.setFixedHeight(56)
        self.btn.setFixedWidth(150)
        self.btn.setCursor(Qt.PointingHandCursor)
        self.btn.setEnabled(False)
        self.btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #D4AF37,stop:1 #AA7C11);
                border: none;
                border-top-right-radius: 14px; border-bottom-right-radius: 14px;
                color: #0a0a0f; font-size: 16px; font-weight: 700;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #E5C158,stop:1 #BB8D22);
            }
            QPushButton:disabled {
                background: rgba(255,255,255,0.04); color: rgba(255,255,255,0.2);
            }
        """)
        self.btn.clicked.connect(self._emit)
        sh = QGraphicsDropShadowEffect()
        sh.setBlurRadius(24); sh.setColor(QColor(212,175,55,80)); sh.setOffset(0,8)
        self.btn.setGraphicsEffect(sh)

        ir.addWidget(self.input_field)
        ir.addWidget(self.btn)

        root.addWidget(self.title_lbl)
        root.addWidget(self.sub_lbl)
        root.addWidget(self.input_row)

    def _check(self, t):
        self.btn.setEnabled(bool(t.strip()))
    def _emit(self):
        t = self.input_field.text().strip()
        if t:
            self._ph_timer.stop()
            self.generate_requested.emit(t)

    # --- particles ---
    def _tick(self):
        for p in self._particles:
            p.step(self.width(), self.height())
        self.update()

    def paintEvent(self, ev):
        painter = QPainter(self)
        try:
            painter.setRenderHint(QPainter.Antialiasing)
            # background
            painter.fillRect(self.rect(), QColor("#0a0a0f"))
            # subtle radial glow
            rg = QRadialGradient(self.rect().center(), self.width()*0.55)
            rg.setColorAt(0, QColor(212, 175, 55, 8))
            rg.setColorAt(1, QColor(0, 0, 0, 0))
            painter.setPen(Qt.NoPen); painter.setBrush(rg)
            painter.drawRect(self.rect())
            # particles
            for p in self._particles:
                painter.setPen(Qt.NoPen)
                painter.setBrush(QColor(212, 175, 55, p.a))
                painter.drawEllipse(QPointF(p.x, p.y), p.r, p.r)
        except Exception:
            pass
        finally:
            if painter.isActive(): painter.end()
