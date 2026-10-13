"""
Museum Calligraphy Style Selector. The scroll viewport and inner container are
made transparent (no default grey auto-fill) so the component sits natively on
the brown field; chips use the brown/gold language with hover, press and active
states preserved.
"""
from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QScrollArea
from PySide6.QtCore import Signal, Qt, QSize
from rendering.styles import STYLES

CHIP_QSS = """
QPushButton {
  background: rgba(46,29,16,190);
  color: rgba(245,236,219,0.9);
  border: 1px solid rgba(201,162,79,90);
  border-radius: 14px;
  padding: 8px 16px;
  font-size: 12px;
}
QPushButton:hover {
  background: rgba(70,45,24,210);
  border: 1px solid rgba(233,200,122,200);
  color: #F4E0B0;
}
QPushButton:pressed { background: rgba(90,60,30,230); }
QPushButton[active="true"] {
  background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #E8C777, stop:1 #B8862F);
  color: #241509;
  border: 1px solid #F4E0B0;
  font-weight: bold;
}
"""


class StyleBar(QWidget):
    chosen = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent;")
        self._buttons = {}

        self._scroll = QScrollArea(self)
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._scroll.setFixedHeight(52)
        self._scroll.setAutoFillBackground(False)
        self._scroll.viewport().setAutoFillBackground(False)
        self._scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        inner = QWidget()
        inner.setAutoFillBackground(False)
        inner.setStyleSheet("background: transparent;")
        lay = QHBoxLayout(inner)
        lay.setContentsMargins(4, 4, 4, 4)
        lay.setSpacing(10)
        for st in STYLES:
            b = QPushButton(st["label"])
            b.setStyleSheet(CHIP_QSS)
            b.setCursor(Qt.PointingHandCursor)
            b.setFixedHeight(40)
            b.setProperty("active", "false")
            b.clicked.connect(lambda _=False, s=st: self._pick(s))
            lay.addWidget(b)
            self._buttons[st["id"]] = b
        lay.addStretch(1)
        self._scroll.setWidget(inner)

        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(self._scroll)

    def _pick(self, st):
        self.set_current(st["id"])
        self.chosen.emit(st)

    def set_current(self, sid):
        for i, b in self._buttons.items():
            b.setProperty("active", "true" if i == sid else "false")
            b.style().unpolish(b)
            b.style().polish(b)

    def sizeHint(self):
        return QSize(600, 52)
