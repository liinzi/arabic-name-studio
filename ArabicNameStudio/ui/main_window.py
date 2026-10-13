"""
Main window for Arabic Calligraphy AI Pro with brand watermark layer.
"""
import os
import logging
from PySide6.QtWidgets import QWidget, QVBoxLayout, QStackedWidget
from PySide6.QtCore import Qt, QTimer
from ai.transliterator import Transliterator
from ai.name_resolver import NameResolver, engine_status, ai_print, ai_print_always
from ui.home_page import HomePage
from ui.calligraphy_page import CalligraphyPage
from ui.transform_overlay import TransformOverlay
from ui.audio_manager import AudioManager
from ui.brand import BrandOverlay

log = logging.getLogger("ui.main")

_SOURCE_LABEL = {"model": "AI model", "fallback": "rule-based fallback",
                 "dictionary": "dictionary", "cache": "cache", "rule-based": "rule-based"}


class MainWindow(QWidget):
    def __init__(self, font_family="Arial"):
        super().__init__()
        self.font_family = font_family
        self.transliterator = Transliterator()
        self.audio = AudioManager()
        self.resolver = NameResolver(dictionary=self.transliterator.names,
                                     rulebased_fn=self.transliterator.transliterate,
                                     known_fn=self.transliterator.known)
        self.resolver.resolved.connect(self._on_resolved)
        self._generating = False
        self._current_name = ""
        self._results = {}
        self._req = 0

        self.setWindowTitle("Arabic Calligraphy AI Pro")
        self.resize(1240, 860)
        self.setMinimumSize(980, 720)
        self.setObjectName("mainWindow")
        self.setStyleSheet("QWidget#mainWindow { background-color: #18100a; }")

        self._init_ui()
        self._ai_banner()
        QTimer.singleShot(1200, self.resolver.warmup)

    def _ai_banner(self):
        st = engine_status()
        ai_print_always("Arabic Calligraphy AI Pro - initializing reasoning engine...")
        ai_print_always("llama-cpp-python: %s" % ("available" if st["llama"] else "NOT installed"))
        ai_print_always("model file: %s" % (os.path.basename(st["gguf"]) if st["gguf"]
                                            else ("NOT found in %s" % st["model_dir"])))
        if st["llama"] and st["gguf"]:
            ai_print_always("reasoning engine: warming up (background)...")
        else:
            ai_print_always("reasoning engine: dictionary + rule-based tiers active.")
            ai_print_always("Run install_ai_engine.py to enable the AI model.")

    def _init_ui(self):
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.stack = QStackedWidget()
        self.home = HomePage(self.audio)
        self.home.generate_requested.connect(self._on_generate)
        self.gallery = CalligraphyPage(self.font_family, self.audio)
        self.gallery.back_requested.connect(self._on_back)
        self.gallery.style_changed.connect(self._on_style_changed)
        self.stack.addWidget(self.home)
        self.stack.addWidget(self.gallery)
        layout.addWidget(self.stack)

        # brand watermark above pages, below transform overlay, non-interactive
        self.brand = BrandOverlay(root, self)
        self.brand.setGeometry(self.rect())

        self.overlay = TransformOverlay(self)
        self.overlay.transformation_complete.connect(self._on_transform_done)
        self.overlay.hide()

    def _on_style_changed(self, preset):
        self._last_style = preset

    def resizeEvent(self, event):
        self.brand.setGeometry(self.rect())
        self.overlay.setGeometry(self.rect())
        super().resizeEvent(event)

    def closeEvent(self, event):
        try:
            self.resolver.shutdown()
        except Exception as exc:
            log.error("resolver shutdown: %s", exc)
        super().closeEvent(event)

    def _on_generate(self, name):
        if self._generating:
            return
        self._generating = True
        self._current_name = name
        self.home.set_button_state("loading")
        preview = self.resolver.fast_or_cached(name)
        self._req += 1
        self.overlay.setGeometry(self.rect())
        self.overlay.start(name, preview)
        if self.audio:
            self.audio.play_transform()
        self.resolver.resolve_async(name, self._req)

    def _on_resolved(self, name, arabic, cls, conf):
        self._results[name] = arabic
        log.info("resolved[%s] class=%s conf=%.3f arabic=%s", name, cls, conf, arabic)

    def _on_transform_done(self):
        name = self._current_name
        try:
            self.home.set_button_state("success")
            QTimer.singleShot(1500, lambda: self.home.set_button_state("default"))
            arabic = self._results.get(name)
            if arabic:
                source = self.resolver.provenance(name)
            else:
                arabic = self.resolver.fast_or_cached(name)
                source = self.resolver.provenance(name) if arabic else None
                if not arabic:
                    arabic = self.transliterator.transliterate(name)
                    source = "rule-based"
            label = _SOURCE_LABEL.get(source, source or "rule-based")
            ai_print("passing to calligraphy renderer | input: %s | source: %s | arabic: %s"
                     % (name, label, arabic))
            self.stack.setCurrentWidget(self.gallery)
            self.gallery.show_result(arabic)
            ai_print("rendering completed successfully.")
        except Exception as exc:
            log.error("generation failed: %s", exc)
            self.stack.setCurrentWidget(self.home)
        finally:
            self._generating = False

    def _on_back(self):
        self.stack.setCurrentWidget(self.home)
