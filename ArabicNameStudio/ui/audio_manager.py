"""
Synthesized audio: UI click, completion chime, and a layered cinematic
transformation soundscape (ascending whoosh + metallic resonance + particle
sparkle + soft shimmer) with baked fade-in/out, generated in memory so the app
stays fully offline. Single QAudioSink with reset-before-start and busy windows.
"""
import math
import random
import logging
from PySide6.QtCore import QBuffer, QIODevice, QTimer
from PySide6.QtMultimedia import QAudioFormat, QAudioSink

log = logging.getLogger("ai.audio")


class AudioManager:
    def __init__(self):
        self.sink = None
        self.click_buffer = None
        self.chime_buffer = None
        self.transform_buffer = None
        self.enabled = False
        self._busy = False
        self._busy_timer = QTimer()
        self._busy_timer.setSingleShot(True)
        self._busy_timer.timeout.connect(self._clear_busy)
        try:
            fmt = QAudioFormat()
            fmt.setSampleRate(44100)
            fmt.setChannelCount(1)
            fmt.setSampleFormat(QAudioFormat.Int16)
            self.sink = QAudioSink(fmt)
            self.click_buffer = self._make_buffer(self._gen_click())
            self.chime_buffer = self._make_buffer(self._gen_chime())
            self.enabled = True
        except Exception as exc:
            log.warning("Audio unavailable: %s", exc)
            self.enabled = False

    def _clear_busy(self):
        self._busy = False

    def _make_buffer(self, data):
        b = QBuffer()
        b.setData(bytes(data))
        b.open(QIODevice.ReadOnly)
        return b

    # -- existing short cues ------------------------------------------------
    def _gen_click(self):
        sr = 44100
        n = int(sr * 0.035)
        out = bytearray()
        for i in range(n):
            t = i / sr
            v = int(32767 * math.exp(-t * 120) * math.sin(2 * math.pi * 180 * t) * 0.15)
            out += v.to_bytes(2, "little", signed=True)
        return out

    def _gen_chime(self):
        sr = 44100
        n = int(sr * 0.9)
        out = bytearray()
        freqs = [523.25, 659.25, 783.99]
        for i in range(n):
            t = i / sr
            s = sum(math.sin(2 * math.pi * f * t) * (0.5 ** k) for k, f in enumerate(freqs))
            v = int(32767 * math.exp(-t * 3.5) * s * 0.12)
            v = max(-32768, min(32767, v))
            out += v.to_bytes(2, "little", signed=True)
        return out

    # -- layered transformation soundscape (lazy-built) ---------------------
    def _gen_transform(self):
        sr = 44100
        dur = 4.4
        n = int(sr * dur)
        rng = random.Random(42)
        # sparkle events (start, freq, amp)
        twinkles = [(rng.uniform(0.2, dur - 0.6), rng.uniform(1800, 6200), rng.uniform(0.02, 0.06))
                    for _ in range(60)]
        partials = [(523.0, 0.05, 1.4), (784.0, 0.04, 1.8), (1244.0, 0.03, 2.2), (1867.0, 0.02, 2.6)]
        fade_in = int(0.4 * sr)
        fade_out = int(0.7 * sr)
        lp = 0.0
        buf = bytearray()
        for i in range(n):
            t = i / sr
            # ascending whoosh: one-pole low-pass noise, rising cutoff + arch env
            cutoff = 0.02 + 0.23 * (i / float(n))
            lp += cutoff * (rng.uniform(-1, 1) - lp)
            whoosh = lp * 0.22 * (math.sin(math.pi * min(1.0, t / dur)) ** 1.5)
            # metallic resonance
            metal = sum(a * math.exp(-t / d) * math.sin(2 * math.pi * f * t) for f, a, d in partials)
            # shimmer sparkle
            spark = 0.0
            for st, sf, sa in twinkles:
                if t > st:
                    dt = t - st
                    spark += sa * math.exp(-dt * 22) * math.sin(2 * math.pi * sf * dt)
            s = whoosh + metal * 0.6 + spark
            # baked fade in/out
            if i < fade_in:
                s *= i / float(fade_in)
            if i > n - fade_out:
                s *= (n - i) / float(fade_out)
            v = int(max(-32768, min(32767, s * 32767 * 0.5)))
            buf += v.to_bytes(2, "little", signed=True)
        return buf

    def _play(self, b, window_ms):
        if not self.enabled or self.sink is None or b is None:
            return
        try:
            self.sink.reset()
            self._busy = True
            b.seek(0)
            self.sink.start(b)
            self._busy_timer.setInterval(window_ms)
            self._busy_timer.start()
        except Exception as exc:
            self._busy = False
            log.warning("audio skipped: %s", exc)

    def play_click(self):
        self._play(self.click_buffer, 60)

    def play_chime(self):
        self._play(self.chime_buffer, 950)

    def play_transform(self):
        if self.transform_buffer is None:
            try:
                self.transform_buffer = self._make_buffer(self._gen_transform())
            except Exception as exc:
                log.warning("transform audio build failed: %s", exc)
                return
        self._play(self.transform_buffer, 4400)

    def play_shimmer(self):
        self.play_click()
