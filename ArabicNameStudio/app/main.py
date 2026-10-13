"""
Application entry point. Installs a luxury font stack and robust startup
diagnostics: every stage is logged to the terminal and any uncaught exception
prints a full traceback to stderr, so the application can never fail silently.
"""
import sys
import os
import logging
import traceback
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QFontDatabase, QFont

os.environ["QT_LOGGING_RULES"] = "*.debug=false;qt.qpa.*=false"


def _setup_logging():
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "logs")
    os.makedirs(log_dir, exist_ok=True)
    logging.basicConfig(
        filename=os.path.join(log_dir, "app.log"),
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )


def _log(msg):
    # Mirror startup progress to the terminal so failures are never silent.
    print(msg, flush=True)
    logging.info(msg)


def _exception_hook(exctype, value, tb):
    # Log to file AND print the full traceback to stderr: never fail silently.
    logging.error("Uncaught exception", exc_info=(exctype, value, tb))
    sys.stderr.write("\n[ERROR] Uncaught exception (startup/runtime):\n")
    traceback.print_exception(exctype, value, tb, file=sys.stderr)
    sys.stderr.flush()


def _install_fonts():
    display = QFont("Seravek", 12, QFont.Medium)
    display.setStyleHint(QFont.Serif)
    ui = QFont("Optima", 11, QFont.Normal)
    ui.setStyleHint(QFont.SansSerif)
    return display, ui


def run_app():
    _setup_logging()
    sys.excepthook = _exception_hook

    _log("[INFO] Starting application...")

    _log("[INFO] Initializing QApplication...")
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    _log("[INFO] Loading fonts...")
    display_font, ui_font = _install_fonts()
    app.setFont(ui_font)

    loaded_font_family = "Arial"
    font_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "fonts")
    if os.path.isdir(font_dir):
        for font_file in sorted(os.listdir(font_dir)):
            if font_file.lower().endswith((".ttf", ".otf")):
                font_id = QFontDatabase.addApplicationFont(os.path.join(font_dir, font_file))
                if font_id != -1:
                    families = QFontDatabase.applicationFontFamilies(font_id)
                    if families:
                        loaded_font_family = families[0]
                        _log("[INFO] Loaded font: %s" % loaded_font_family)

    _log("[INFO] Loading UI modules...")
    from ui.main_window import MainWindow

    _log("[INFO] Creating MainWindow...")
    window = MainWindow(loaded_font_family)

    _log("[INFO] Showing MainWindow...")
    window.show()

    _log("[INFO] Starting Qt Event Loop...")
    sys.exit(app.exec())
