"""
Standardized six-style library. Each style carries distinct handwriting
parameters (vscale proportion, shear slant, stroke weight, spacing density) so
switching yields an immediately noticeable transformation even when the original
font file is not installed; when a real family IS installed it is used as-is.
"""
from PySide6.QtGui import QColor, QFont

ROYAL = [(0.0, "#FFE9B0"), (0.22, "#F4CE72"), (0.5, "#D9A441"), (0.8, "#A66E1E"), (1.0, "#7E5214")]
CHAMPAGNE = [(0.0, "#FFF6DC"), (0.3, "#F6DFA4"), (0.6, "#E0BC6A"), (1.0, "#9C752F")]
DEEP = [(0.0, "#F4CE72"), (0.4, "#C58A2C"), (0.75, "#8A5717"), (1.0, "#5E3A0F")]
INK = [(0.0, "#2A2018"), (0.5, "#171009"), (1.0, "#0B0703")]


def _s(id, label, fonts, palette, **kw):
    d = dict(id=id, label=label, fonts=fonts, size=1.0, vscale=1.0, shear=0.0,
             weight=QFont.Bold, spacing=100, body="gold", brushed=True,
             medallion=False, flourish=True, orn=1.0, palette=palette,
             accent=QColor(233, 200, 122))
    d.update(kw)
    return d


STYLES = [
    # Thuluth: tall, majestic, strong verticals
    _s("thuluth", "Thuluth", ["Thuluth", "Ijazah", "Aref Ruqaa", "Amiri"], ROYAL,
       vscale=1.16, shear=0.0, weight=QFont.Bold, spacing=100, flourish=True),
    # Cocon Next Arabic: modern, clean, geometric-modern
    _s("cocon", "Cocon Next Arabic", ["Cocon Next Arabic", "Cocon", "Cairo", "Almarai", "Amiri"],
       CHAMPAGNE, vscale=0.98, shear=0.0, weight=QFont.DemiBold, spacing=108,
       brushed=True, flourish=False, orn=0.6),
    # Naskh: classical, readable, balanced
    _s("naskh", "Naskh", ["Naskh", "Amiri", "Noto Naskh Arabic", "Scheherazade New"], ROYAL,
       vscale=1.0, shear=0.0, weight=QFont.Medium, spacing=100, flourish=False, orn=0.7),
    # Diwani: flowing, slanted, elegant curves
    _s("diwani", "Diwani", ["Diwani", "Diwani Kufi", "Aref Ruqaa", "Amiri"], CHAMPAGNE,
       vscale=1.06, shear=0.18, weight=QFont.Bold, spacing=94, flourish=True, orn=1.1),
    # Ijazah: tall manuscript style
    _s("ijazah", "Ijazah", ["Ijazah", "Thuluth", "Amiri"], ROYAL,
       vscale=1.12, shear=0.06, weight=QFont.Bold, spacing=100, flourish=True),
    # Maghrebi: rounded, regional, lighter
    _s("maghrebi", "Maghrebi", ["Maghrebi", "Scheherazade New", "Lateef", "Amiri"], DEEP,
       vscale=1.05, shear=0.10, weight=QFont.Medium, spacing=98, flourish=True),
]

DEFAULT = STYLES[0]


def by_id(sid):
    for s in STYLES:
        if s["id"] == sid:
            return s
    return DEFAULT
