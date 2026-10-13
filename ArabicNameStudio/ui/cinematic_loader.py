from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt, QTimer
import logging

class CinematicLoader(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # CRITICAL FIX: Removed setWindowFlags to keep it as an internal overlay
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent;")
        
        self.layout = QVBoxLayout(self)
        self.label = QLabel("Understanding pronunciation...")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("""
            color: white; font-size: 22px; font-weight: 300;
            background-color: rgba(15, 15, 19, 230);
            border: 1px solid rgba(212, 175, 55, 0.2);
            border-radius: 20px; padding: 40px 60px;
        """)
        self.layout.addWidget(self.label)
        
        self.stages = [
            "Understanding pronunciation...",
            "Building Arabic representation...",
            "Optimizing composition...",
            "Selecting artistic style...",
            "Rendering masterpiece..."
        ]
        self.current_stage = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.next_stage)
        
    def start(self):
        self.current_stage = 0
        self.update_text()
        self.resize(self.parent().size() if self.parent() else self.size())
        self.raise_()
        self.show()
        self.timer.start(800)
        
    def resizeEvent(self, event):
        if self.parent():
            self.setGeometry(self.parent().rect())
        super().resizeEvent(event)
        
    def next_stage(self):
        self.current_stage += 1
        if self.current_stage >= len(self.stages):
            self.timer.stop()
            self.hide()
        else:
            self.update_text()
            
    def update_text(self):
        try:
            self.label.setText(self.stages[self.current_stage])
        except Exception as e:
            logging.error(f"Loader text error: {e}")
