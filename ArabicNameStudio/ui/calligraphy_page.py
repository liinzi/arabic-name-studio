"""
Calligraphy gallery page with a balanced, premium layout: back bar, centered
render card (sane dimensions), style selector below the card, action bar below
that - no overlap, proper spacing, adaptive card sizing.
"""
import math
import logging
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGraphicsOpacityEffect, QFileDialog,
)
from PySide6.QtCore import Qt, Signal, QTimer, QPropertyAnimation, QEasingCurve, QPointF
from PySide6.QtGui import QColor, QPainter, QLinearGradient, QRadialGradient
from ui.glass_card import PresentationCard
from ui.action_bar import ActionBar, TactileButton
from ui.style_selector import StyleBar
from ui.golden_veins import VeinField
from ui.audio_manager import AudioManager
from ui.theme import make_star_tile
from rendering.styles import DEFAULT

log = logging.getLogger("ui.gallery")


class CalligraphyPage(QWidget):
    back_requested = Signal()
    style_changed = Signal(object)

    def __init__(self, font_family="Arial", audio_mgr=None, parent=None):
        super().__init__(parent)
        self.font_family = font_family
        self.audio = audio_mgr
        self._anims = []
        self.current_style = DEFAULT
        self._pattern = make_star_tile(200, QColor(214, 176, 96, 95))
        self._pattern2 = make_star_tile(300, QColor(176, 134, 70, 70))
        self._veins = VeinField(200, seed=11, max_veins=8, intensity=0.45)
        self._drift = 0.0
        self._drift_timer = QTimer(self)
        self._drift_timer.timeout.connect(self._tick_drift)
        self._init_ui()

    def _tick_drift(self):
        self._drift += 0.10
        self.update()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(48, 26, 48, 22)
        layout.setSpacing(0)

        top = QHBoxLayout()
        top.setContentsMargins(6, 0, 6, 0)
        self.btn_back = TactileButton("Back", icon="back")
        self.btn_back.setFixedSize(116, 44)
        self.btn_back.clicked.connect(self._on_back)
        top.addWidget(self.btn_back)
        top.addStretch()
        layout.addLayout(top)
        layout.addSpacing(6)

        layout.addStretch(1)

        self.card = PresentationCard(self.font_family)
        self.card.setMinimumSize(800, 440)
        self.card.setMaximumSize(1200, 640)
        layout.addWidget(self.card, 0, Qt.AlignHCenter)
        layout.addSpacing(16)

        self.styles = StyleBar()
        self.styles.set_current(DEFAULT["id"])
        self.styles.chosen.connect(self._on_style)
        layout.addWidget(self.styles, 0, Qt.AlignHCenter)
        layout.addSpacing(12)

        self.actions = ActionBar()
        self.actions.copy_clicked.connect(self._copy)
        self.actions.regen_clicked.connect(self._regen)
        self.actions.save_clicked.connect(self._save)
        layout.addWidget(self.actions, 0, Qt.AlignHCenter)

        layout.addStretch(1)

        for w in (self.btn_back, self.styles, self.actions):
            fx = QGraphicsOpacityEffect(w)
            w.setGraphicsEffect(fx)
            fx.setOpacity(0.0)

    def _adapt_card(self, n):
        if n > 140:
            self.card.setMinimumSize(900, 520); self.card.setMaximumSize(1200, 680)
        elif n > 60:
            self.card.setMinimumSize(860, 480); self.card.setMaximumSize(1200, 660)
        elif n > 24:
            self.card.setMinimumSize(820, 460); self.card.setMaximumSize(1200, 650)
        else:
            self.card.setMinimumSize(800, 440); self.card.setMaximumSize(1200, 640)

    def showEvent(self, event):
        super().showEvent(event)
        if not self._drift_timer.isActive():
            self._drift_timer.start(40)

    def hideEvent(self, event):
        self._drift_timer.stop()
        super().hideEvent(event)

    def paintEvent(self, event):
        p = QPainter(self)
        try:
            p.setRenderHint(QPainter.RenderHint.Antialiasing)
            p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
            r = self.rect()
            g = QLinearGradient(0, 0, 0, r.height())
            g.setColorAt(0.0, QColor(36, 21, 11))
            g.setColorAt(1.0, QColor(16, 9, 4))
            p.fillRect(r, g)
            dx1 = -int(self._drift % 200); dy1 = -int((self._drift * 0.5) % 200)
            p.save(); p.setOpacity(0.55 + 0.12 * math.sin(self._drift * 0.02))
            p.drawTiledPixmap(r.adjusted(dx1 - 200, dy1 - 200, 200, 200), self._pattern); p.restore()
            self._veins.advance_and_paint(p, r, dx1, dy1)
            p.save(); p.setOpacity(0.40 + 0.10 * math.sin(self._drift * 0.013 + 1.0))
            dx2 = int((self._drift * 0.6) % 300); dy2 = -int((self._drift * 0.3) % 300)
            p.drawTiledPixmap(r.adjusted(dx2 - 300, dy2 - 300, 300, 300), self._pattern2); p.restore()
            vg = QRadialGradient(QPointF(r.center()), max(r.width(), r.height()) * 0.85)
            vg.setColorAt(0.0, QColor(0, 0, 0, 0)); vg.setColorAt(0.78, QColor(0, 0, 0, 0))
            vg.setColorAt(1.0, QColor(6, 3, 1, 130))
            p.fillRect(r, vg)
        except Exception as exc:
            log.error("gallery paint: %s", exc)
        finally:
            if p.isActive():
                p.end()

    def _on_style(self, preset):
        self.current_style = preset
        self.card.calligraphy.set_style(preset, animate=True)
        if self.audio:
            self.audio.play_click()
        self.style_changed.emit(preset)

    def _on_back(self):
        if self.audio:
            self.audio.play_click()
        self.back_requested.emit()

    def show_result(self, arabic_text):
        self._adapt_card(len(arabic_text))
        self.card.calligraphy.set_style(self.current_style, animate=False)
        self.card.set_text(arabic_text)
        self.actions.set_arabic_text(arabic_text)
        QTimer.singleShot(80, self._entrance)
        QTimer.singleShot(450, self.card.start_animation)
        if self.audio:
            QTimer.singleShot(1400, self.audio.play_chime)

    def _entrance(self):
        for a in self._anims:
            a.stop()
        self._anims.clear()
        for w, delay in ((self.btn_back, 0), (self.styles, 300), (self.actions, 600)):
            fx = w.graphicsEffect()
            if isinstance(fx, QGraphicsOpacityEffect):
                fx.setOpacity(0.0)
                a = QPropertyAnimation(fx, b"opacity")
                a.setDuration(800); a.setStartValue(0.0); a.setEndValue(1.0)
                a.setEasingCurve(QEasingCurve.OutCubic)
                self._anims.append(a)
                QTimer.singleShot(delay, a.start)

    def _copy(self):
        if self.audio: self.audio.play_click()
        try:
            from PySide6.QtWidgets import QApplication
            QApplication.clipboard().setText(self.actions.arabic_text)
        except Exception as exc:
            log.error("copy: %s", exc)

    def _regen(self):
        if self.audio: self.audio.play_click()
        self.card.start_animation()

    def _save(self):
        if self.audio: self.audio.play_click()
        try:
            path, _ = QFileDialog.getSaveFileName(
                self, "Save Calligraphy", "calligraphy.png", "PNG Files (*.png);;All Files (*)")
            if path:
                pixmap = self.card.grab()
                if pixmap.save(path, "PNG"):
                    log.info("saved %s", path)
                else:
                    log.error("save failed %s", path)
        except Exception as exc:
            log.error("save: %s", exc)
