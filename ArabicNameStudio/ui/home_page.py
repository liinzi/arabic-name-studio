"""
Landing page for Arabic Calligraphy AI Pro.
"""
import math
import logging
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QHBoxLayout, QGraphicsOpacityEffect,
)
from PySide6.QtCore import (
    Qt, Signal, QTimer, QPropertyAnimation, QEasingCurve, QEvent, QRectF, QPointF, Property,
)
from PySide6.QtGui import (
    QColor, QFont, QFontMetricsF, QPainter, QPen, QRadialGradient,
    QLinearGradient, QPainterPath,
)
from ui.particles import ParticleWidget
from ui.golden_veins import VeinField
from ui.generate_button import GenerateButton
from ui.audio_manager import AudioManager
from ui.theme import make_star_tile, gold_leaf_gradient, font_display, font_ui


class SparkIcon(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(22, 22)

    def paintEvent(self, event):
        from ui.generate_button import _sparkle
        p = QPainter(self)
        try:
            _sparkle(p, QRectF(self.rect()), QColor(233, 200, 122, 220))
        except Exception as exc:
            logging.error("SparkIcon: %s", exc)
        finally:
            if p.isActive():
                p.end()


class LuxuryInput(QWidget):
    generate_clicked = Signal(str)

    def __init__(self, audio_mgr, parent=None):
        super().__init__(parent)
        self.audio = audio_mgr
        self._focused = False
        self._glow = 0.0
        self._init_ui()
        self.glow_anim = QPropertyAnimation(self, b"glow_val")
        self.glow_anim.setDuration(260)
        self.glow_anim.setEasingCurve(QEasingCurve.OutCubic)

    def _get_glow(self):
        return self._glow

    def _set_glow(self, v):
        self._glow = v
        self.update()

    glow_val = Property(float, _get_glow, _set_glow)

    def _init_ui(self):
        self.setFixedHeight(74)
        self.setMaximumWidth(720)
        self.setMinimumWidth(480)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(26, 0, 10, 0)
        layout.setSpacing(14)
        self.icon = SparkIcon()
        self.field = QLineEdit()
        self.field.setPlaceholderText("Enter a name or phrase in English…")
        self.field.setStyleSheet("""
            QLineEdit { background: transparent; border: none; color: #F5ECDB;
              font-size: 21px; padding: 0px;
              selection-background-color: rgba(201,162,79,0.35); }
            QLineEdit::placeholder { color: rgba(214,196,168,0.45); }
        """)
        self.field.textChanged.connect(self._on_text)
        self.field.returnPressed.connect(self._fire)
        self.field.installEventFilter(self)
        self.btn = GenerateButton("Generate")
        self.btn.setEnabled(False)
        self.btn.clicked.connect(self._fire)
        layout.addWidget(self.icon)
        layout.addWidget(self.field, 1)
        layout.addWidget(self.btn)

    def eventFilter(self, obj, event):
        if obj is self.field:
            if event.type() == QEvent.FocusIn:
                self._focused = True
                self.glow_anim.stop(); self.glow_anim.setStartValue(self._glow)
                self.glow_anim.setEndValue(1.0); self.glow_anim.start()
                if self.audio:
                    self.audio.play_click()
            elif event.type() == QEvent.FocusOut:
                self._focused = False
                self.glow_anim.stop(); self.glow_anim.setStartValue(self._glow)
                self.glow_anim.setEndValue(0.0); self.glow_anim.start()
        return super().eventFilter(obj, event)

    def _on_text(self, t):
        self.btn.setEnabled(bool(t.strip()))
        if t.strip():
            self.btn.set_state("default")

    def _fire(self):
        t = self.field.text().strip()
        if t:
            if self.audio:
                self.audio.play_click()
            self.generate_clicked.emit(t)

    def get_text(self):
        return self.field.text().strip()

    def set_text(self, text):
        self.field.setText(text)

    def set_button_state(self, s):
        self.btn.set_state(s)

    def paintEvent(self, event):
        p = QPainter(self)
        try:
            p.setRenderHint(QPainter.RenderHint.Antialiasing)
            r = QRectF(self.rect())
            radius = 22.0
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(0, 0, 0, 60))
            p.drawRoundedRect(r.adjusted(6, 10, -6, -2), radius, radius)
            body = QLinearGradient(0, 0, 0, r.height())
            body.setColorAt(0.0, QColor(78, 51, 32, int(150 + self._glow * 40)))
            body.setColorAt(1.0, QColor(38, 24, 15, int(180 + self._glow * 30)))
            p.setBrush(body)
            p.setPen(QPen(QColor(201, 162, 79, int(70 + self._glow * 130)), 1.4))
            p.drawRoundedRect(r.adjusted(1, 1, -1, -1), radius, radius)
            if self._glow > 0.01:
                g = QRadialGradient(r.center(), r.width() * 0.6)
                g.setColorAt(0.0, QColor(233, 200, 122, int(28 * self._glow)))
                g.setColorAt(1.0, QColor(233, 200, 122, 0))
                p.setPen(Qt.NoPen)
                p.setBrush(g)
                p.drawRoundedRect(r, radius, radius)
        except Exception as exc:
            logging.error("LuxuryInput: %s", exc)
        finally:
            if p.isActive():
                p.end()


class TypingSubtitle(QLabel):
    PHRASES = [
        "Transform Any Name Into Timeless Arabic Calligraphy.",
        "Intelligent Recognition of Every Spelling Variation.",
        "From Ahmed to أَحْمَد - Automatically.",
        "Museum-Quality Calligraphy in One to Two Seconds.",
        "Full Names, Titles and Phrases - Beautifully Adapted.",
        "Where Technology Meets Timeless Tradition.",
    ]

    def __init__(self, parent=None):
        super().__init__("", parent)
        self.setAlignment(Qt.AlignCenter)
        self.setFixedWidth(780)
        self.setFixedHeight(30)
        self.setFont(font_ui(16))
        self.setStyleSheet("color: rgba(214,196,168,0.92); background: transparent;")
        self._idx = 0
        self._char = len(self.PHRASES[0])
        self._mode = "pause_init"
        self._cursor = True
        self._render()
        self._tick_timer = QTimer(self)
        self._tick_timer.timeout.connect(self._tick)
        self._blink_timer = QTimer(self)
        self._blink_timer.timeout.connect(self._blink)

    def _render(self):
        txt = self.PHRASES[self._idx][: self._char]
        cur = "|" if self._cursor else " "
        self.setText(txt + cur)

    def _blink(self):
        self._cursor = not self._cursor
        self._render()

    def _tick(self):
        ph = self.PHRASES[self._idx]
        if self._mode == "type":
            self._char += 1
            if self._char > len(ph):
                self._mode = "pause"
                self._tick_timer.setInterval(1500)
            else:
                self._tick_timer.setInterval(52)
        elif self._mode == "pause":
            self._mode = "delete"
            self._tick_timer.setInterval(34)
        elif self._mode == "delete":
            self._char -= 1
            if self._char < 0:
                self._idx = (self._idx + 1) % len(self.PHRASES)
                self._char = 0
                self._mode = "type"
                self._tick_timer.setInterval(320)
            else:
                self._tick_timer.setInterval(30)
        elif self._mode == "pause_init":
            self._mode = "delete"
            self._tick_timer.setInterval(1200)
        self._render()

    def start_typing(self):
        self._idx = 0
        self._char = len(self.PHRASES[0])
        self._mode = "delete"
        self._cursor = True
        self._render()
        self._tick_timer.setInterval(60)
        self._tick_timer.start()
        self._blink_timer.setInterval(520)
        self._blink_timer.start()

    def stop_typing(self):
        self._tick_timer.stop()
        self._blink_timer.stop()


class HomePage(QWidget):
    generate_requested = Signal(str)

    def __init__(self, audio_mgr, parent=None):
        super().__init__(parent)
        self.audio = audio_mgr
        self._anims = []
        self._pattern = make_star_tile(200, QColor(214, 176, 96, 95))
        self._pattern2 = make_star_tile(300, QColor(176, 134, 70, 70))
        self._drift = 0.0
        self._veins = VeinField(200, seed=7, max_veins=20, intensity=1.0)
        self._drift_timer = QTimer(self)
        self._drift_timer.timeout.connect(self._tick_drift)
        self._init_ui()

    def _init_ui(self):
        self.particles = ParticleWidget(55, self)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(60, 40, 60, 40)
        layout.setSpacing(0)
        layout.setAlignment(Qt.AlignCenter)
        layout.addStretch(1)

        self.eyebrow = QLabel("A R A B I C   C A L L I G R A P H Y   A I   P R O")
        self.eyebrow.setAlignment(Qt.AlignCenter)
        self.eyebrow.setStyleSheet("color: rgba(233,200,122,0.85); font-size: 13px; letter-spacing: 4px;")
        layout.addWidget(self.eyebrow)
        layout.addSpacing(18)

        self.title = QLabel("Arabic Calligraphy AI Pro")
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setFont(font_display(50, QFont.Medium))
        self.title.setStyleSheet("color: #F5ECDB; background: transparent;")
        layout.addWidget(self.title)
        layout.addSpacing(14)

        self.tagline = QLabel("Understand the name. Correct it. Render it as art.")
        self.tagline.setAlignment(Qt.AlignCenter)
        self.tagline.setFont(font_ui(17))
        self.tagline.setStyleSheet("color: rgba(233,200,122,0.8); background: transparent;")
        layout.addWidget(self.tagline)
        layout.addSpacing(18)

        self.subtitle = TypingSubtitle()
        layout.addWidget(self.subtitle)
        layout.setAlignment(self.subtitle, Qt.AlignHCenter)
        layout.addSpacing(40)

        self.input = LuxuryInput(self.audio)
        self.input.generate_clicked.connect(self.generate_requested)
        layout.addWidget(self.input, 0, Qt.AlignCenter)
        layout.addStretch(1)

        for w in (self.eyebrow, self.title, self.tagline, self.subtitle, self.input):
            fx = QGraphicsOpacityEffect(w)
            w.setGraphicsEffect(fx)
            fx.setOpacity(0.0)

    def set_button_state(self, s):
        self.input.set_button_state(s)

    def _tick_drift(self):
        self._drift += 0.12
        self.update()

    def showEvent(self, event):
        super().showEvent(event)
        self.particles.setGeometry(self.rect())
        self.input.set_button_state("default")
        if not self._drift_timer.isActive():
            self._drift_timer.start(40)
        QTimer.singleShot(80, self._entrance)
        QTimer.singleShot(1800, self._maybe_start_typing)

    def _maybe_start_typing(self):
        if self.isVisible():
            self.subtitle.start_typing()

    def hideEvent(self, event):
        self._drift_timer.stop()
        self.subtitle.stop_typing()
        super().hideEvent(event)

    def resizeEvent(self, event):
        self.particles.setGeometry(self.rect())
        super().resizeEvent(event)

    def paintEvent(self, event):
        p = QPainter(self)
        try:
            p.setRenderHint(QPainter.RenderHint.Antialiasing)
            p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
            r = self.rect()
            base = QLinearGradient(0, 0, 0, r.height())
            base.setColorAt(0.0, QColor(40, 23, 10))
            base.setColorAt(0.5, QColor(26, 14, 6))
            base.setColorAt(1.0, QColor(15, 8, 3))
            p.fillRect(r, base)

            dx1 = -int(self._drift % 200)
            dy1 = -int((self._drift * 0.5) % 200)
            p.save()
            p.setOpacity(0.55 + 0.12 * math.sin(self._drift * 0.02))
            p.drawTiledPixmap(r.adjusted(dx1 - 200, dy1 - 200, 200, 200), self._pattern)
            p.restore()

            self._veins.advance_and_paint(p, r, dx1, dy1)

            p.save()
            p.setOpacity(0.40 + 0.10 * math.sin(self._drift * 0.013 + 1.0))
            dx2 = int((self._drift * 0.6) % 300)
            dy2 = -int((self._drift * 0.3) % 300)
            p.drawTiledPixmap(r.adjusted(dx2 - 300, dy2 - 300, 300, 300), self._pattern2)
            p.restore()

            vg = QRadialGradient(QPointF(r.center()), max(r.width(), r.height()) * 0.8)
            vg.setColorAt(0.0, QColor(0, 0, 0, 0))
            vg.setColorAt(0.7, QColor(0, 0, 0, 0))
            vg.setColorAt(1.0, QColor(8, 4, 2, 150))
            p.fillRect(r, vg)
            pool = QRadialGradient(QPointF(r.center().x(), r.center().y() - 40), r.width() * 0.5)
            pool.setColorAt(0.0, QColor(120, 84, 44, 36))
            pool.setColorAt(1.0, QColor(120, 84, 44, 0))
            p.fillRect(r, pool)
        except Exception as exc:
            logging.error("HomePage paint: %s", exc)
        finally:
            if p.isActive():
                p.end()

    def _entrance(self):
        for a in self._anims:
            a.stop()
        self._anims.clear()
        targets = [self.eyebrow, self.title, self.tagline, self.subtitle, self.input]
        delays = [0, 150, 350, 500, 800]
        durs = [900, 1000, 900, 900, 900]
        for w, delay, dur in zip(targets, delays, durs):
            fx = w.graphicsEffect()
            if isinstance(fx, QGraphicsOpacityEffect):
                fx.setOpacity(0.0)
                a = QPropertyAnimation(fx, b"opacity")
                a.setDuration(dur)
                a.setStartValue(0.0)
                a.setEndValue(1.0)
                a.setEasingCurve(QEasingCurve.OutCubic)
                self._anims.append(a)
                QTimer.singleShot(delay, a.start)
        QTimer.singleShot(1600, self.input.field.setFocus)

    def get_input_text(self):
        return self.input.get_text()

    def set_input_text(self, text):
        self.input.set_text(text)
