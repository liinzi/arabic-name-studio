import logging
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QGraphicsOpacityEffect
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve, Property
from PySide6.QtGui import QPainter, QColor, QRadialGradient
from ui.glass_card import PresentationCard
from ui.action_bar import ActionBar

class PresentationPage(QWidget):
    back_requested = Signal()

    def __init__(self, arabic_font="Arial", parent=None):
        super().__init__(parent)
        self.arabic_font = arabic_font
        self._alpha = 0.0
        self._setup()

    def _setup(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(40, 32, 40, 32)
        root.setSpacing(24)

        # back button
        self.btn_back = QPushButton("←  Home")
        self.btn_back.setFixedSize(100, 38)
        self.btn_back.setCursor(Qt.PointingHandCursor)
        self.btn_back.setStyleSheet("""
            QPushButton {
                background: rgba(255,255,255,0.04);
                border: 1px solid rgba(255,255,255,0.08);
                border-radius: 10px; color: rgba(245,245,247,0.6);
                font-size: 13px; font-weight: 500;
            }
            QPushButton:hover {
                background: rgba(255,255,255,0.09);
                color: #f5f5f7; border-color: rgba(255,255,255,0.18);
            }
        """)
        self.btn_back.clicked.connect(self.back_requested.emit)
        root.addWidget(self.btn_back, alignment=Qt.AlignLeft | Qt.AlignTop)

        # card
        self.card = PresentationCard(self.arabic_font)
        self.card.setMinimumHeight(340)
        root.addWidget(self.card, stretch=1)

        # actions
        self.actions = ActionBar()
        self.actions.set_card_ref(self.card)
        root.addWidget(self.actions)

    def show_result(self, arabic_text):
        self.card.set_text(arabic_text)
        self.actions.set_arabic_text(arabic_text)
        self._play_entrance()
        self.card.start_animation()

    def _play_entrance(self):
        self._alpha = 0.0
        self._anim = QPropertyAnimation(self, b"alpha")
        self._anim.setDuration(700)
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)
        self._anim.start()

    def get_alpha(self): return self._alpha
    def set_alpha(self, v):
        self._alpha = v
        self.card.setGraphicsEffect(self._op(v))
        self.actions.setGraphicsEffect(self._op(max(0, v-0.3)*1.43))
    alpha = Property(float, get_alpha, set_alpha)

    @staticmethod
    def _op(a):
        e = QGraphicsOpacityEffect()
        e.setOpacity(max(0.0, min(1.0, a)))
        return e

    def paintEvent(self, ev):
        p = QPainter(self)
        try:
            p.fillRect(self.rect(), QColor("#0a0a0f"))
            rg = QRadialGradient(self.rect().center(), self.width()*0.5)
            rg.setColorAt(0, QColor(212,175,55,6))
            rg.setColorAt(1, QColor(0,0,0,0))
            p.setPen(Qt.NoPen); p.setBrush(rg); p.drawRect(self.rect())
        except Exception:
            pass
        finally:
            if p.isActive(): p.end()
