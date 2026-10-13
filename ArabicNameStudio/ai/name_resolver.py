"""
3-tier resolver with speed optimizations: tier-1 now uses the transliterator's
dictionary-only `known()` (instant, correct canonical forms) before touching the
model; the model uses a smaller max_tokens budget for lower latency. Harakat-aware,
deterministic, background worker, graceful degradation, terminal diagnostics.
"""
import os
import re
import json
import glob
import time
import queue
import logging
import threading
import importlib.util
from collections import OrderedDict
from PySide6.QtCore import QObject, QThread, Signal, QCoreApplication

log = logging.getLogger("ai.model")

_VERBOSE = os.environ.get("ARABIC_STUDIO_AI_VERBOSE", "1").strip().lower() not in ("0", "false", "no", "off")


def ai_print(msg):
    if _VERBOSE:
        print("[AI] " + msg, flush=True)
    log.info(msg)


def ai_print_always(msg):
    print("[AI] " + msg, flush=True)
    log.info(msg)


_LATIN_RE = re.compile("[A-Za-z]")
_ARABIC_RE = re.compile("[؀-]")
_THINK_RE = re.compile(r"<think>.*?</think>", re.S)
_ALLOWED_CLS = {"canonical_arabic", "transliteration", "fallback"}

SYSTEM = """You are the linguistic reasoning engine inside Arabic Calligraphy AI Pro.
Your sole responsibility is determining the most correct Arabic representation of an English input.
Rules:
1. If the input is an Arabic/Islamic personal name (in any English spelling), return the fully vocalized canonical Arabic spelling with correct tashkeel, e.g. Ahmed -> أَحْمَد, Muhammad -> مُحَمَّدٌ, Abdul Hameed -> عَبْدُ الْحَمِيدِ.
2. Treat all spelling variants, hyphens, spacing and regional forms as equivalent when they refer to the same Arabic name.
3. For multi-word/full names, translate EACH component to its canonical Arabic and join with spaces, e.g. Muhammad Ali -> مُحَمَّدٌ عَلِي.
4. If the input is a common English word/phrase (not a name), return its correct concise Arabic translation (Mode 2), without tashkeel.
5. Never invent unusual spellings when a standard spelling exists.
6. Use proper structural orthography (hamza, madda, maqsura, ta marbuta, shadda, long vowels).
7. Always deterministic. Never explain.
Return ONLY valid JSON, no markdown, no thinking, using exactly:
{"classification":"canonical_arabic|transliteration","arabic":"...","confidence":0.00-1.00}"""


def clean(s):
    if not isinstance(s, str):
        return ""
    return re.sub(r"\s+", " ", s).strip()


def _clamp01(v):
    try:
        v = float(v)
    except Exception:
        return 0.0
    return max(0.0, min(1.0, v))


def _valid_arabic(s):
    return bool(s) and len(s) <= 400 and _ARABIC_RE.search(s) and not _LATIN_RE.search(s)


def _parse(text):
    if not text:
        return None
    text = _THINK_RE.sub("", text)
    i = text.find("{")
    j = text.rfind("}")
    if i < 0 or j <= i:
        return None
    try:
        obj = json.loads(text[i:j + 1])
    except Exception:
        return None
    arabic = clean(obj.get("arabic", ""))
    if not _valid_arabic(arabic):
        return None
    cls = str(obj.get("classification", "transliteration")).strip().lower()
    if cls not in _ALLOWED_CLS:
        cls = "transliteration"
    return {"classification": cls, "arabic": arabic, "confidence": _clamp01(obj.get("confidence", 0.0))}


def engine_status(model_dir=None):
    if model_dir is None:
        model_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")
    llama_ok = importlib.util.find_spec("llama_cpp") is not None
    gguf = None
    override = os.environ.get("ARABIC_STUDIO_MODEL", "").strip()
    if override and os.path.isfile(override):
        gguf = override
    elif os.path.isdir(model_dir):
        cands = sorted(glob.glob(os.path.join(model_dir, "*.gguf")))
        for c in cands:
            if "Q4_K_M" in os.path.basename(c):
                gguf = c
                break
        if gguf is None and cands:
            gguf = cands[0]
    return {"llama": llama_ok, "gguf": gguf, "model_dir": model_dir}


class _Worker(QThread):
    resolved = Signal(str, str, str, float)

    def __init__(self, q, stop, dictionary, rulebased_fn, model_dir):
        super().__init__()
        self._q = q
        self._stop = stop
        self._dict = dictionary or {}
        self._rb = rulebased_fn
        self._model_dir = model_dir
        self._llm = None
        self._state = None

    def run(self):
        while not self._stop.is_set():
            try:
                job = self._q.get(timeout=0.4)
            except queue.Empty:
                continue
            if job is None:
                break
            kind = job[0]
            try:
                if kind == "load":
                    self._ensure_loaded()
                elif kind == "resolve":
                    _, reqid, name = job
                    d = self._resolve(name)
                    self.resolved.emit(name, d["arabic"], d["classification"], float(d["confidence"]))
            except Exception as exc:
                log.error("worker job failed: %s", exc)
                if kind == "resolve":
                    _, reqid, name = job
                    d = self._rulebased(name)
                    self.resolved.emit(name, d["arabic"], d["classification"], float(d["confidence"]))

    def _rulebased(self, name):
        try:
            arabic = clean(self._rb(name))
        except Exception as exc:
            log.error("rule-based fallback failed: %s", exc)
            arabic = ""
        return {"arabic": arabic or name, "classification": "fallback", "confidence": 0.0}

    def _find_gguf(self):
        override = os.environ.get("ARABIC_STUDIO_MODEL", "").strip()
        if override and os.path.isfile(override):
            return override
        if not os.path.isdir(self._model_dir):
            return None
        cands = sorted(glob.glob(os.path.join(self._model_dir, "*.gguf")))
        for c in cands:
            if "Q4_K_M" in os.path.basename(c):
                return c
        return cands[0] if cands else None

    def _ensure_loaded(self):
        if self._state is not None:
            return self._state
        ai_print_always("Loading Qwen3-0.6B...")
        try:
            os.environ.setdefault("LLAMA_LOG_LEVEL", "error")
            from llama_cpp import Llama
            path = self._find_gguf()
            if not path:
                raise FileNotFoundError("no .gguf in %s" % self._model_dir)
            self._llm = Llama(model_path=path, n_ctx=1024, n_batch=512,
                              n_threads=max(1, os.cpu_count() or 2), verbose=False)
            self._state = True
            ai_print_always("Qwen3-0.6B loaded successfully | %s" % os.path.basename(path))
            ai_print_always("Inference engine ready (deterministic JSON decoding).")
        except Exception as exc:
            self._llm = None
            self._state = False
            ai_print_always("model unavailable: %s | using dictionary + rule-based fallback" % exc)
            log.warning("AI model unavailable: %s", exc)
        return self._state

    def _chat(self, msgs):
        base = dict(messages=msgs, temperature=0.05, top_p=0.85, repeat_penalty=1.05,
                    seed=12345, max_tokens=120)
        try:
            r = self._llm.create_chat_completion(response_format={"type": "json_object"}, **base)
        except TypeError:
            r = self._llm.create_chat_completion(**base)
        return r["choices"][0]["message"]["content"]

    def _resolve(self, name):
        ai_print("inference started | input: %s" % name)
        if not self._ensure_loaded():
            d = self._rulebased(name)
            ai_print("fallback used (rule-based) | input: %s | arabic: %s" % (name, d["arabic"]))
            return d
        try:
            user = 'Input: "%s"\nReturn only the JSON object. No markdown. No thinking.\n/no_think' % name
            msgs = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": user}]
            raw = self._chat(msgs)
            parsed = _parse(raw)
            if parsed:
                ai_print("model output | input: %s | arabic: %s | class: %s | conf: %.3f"
                         % (name, parsed["arabic"], parsed["classification"], parsed["confidence"]))
                return parsed
            ai_print("model output invalid | input: %s | using fallback" % name)
        except Exception as exc:
            log.error("model inference failed for %s: %s", name, exc)
            ai_print("model inference error | input: %s | using fallback" % name)
        d = self._rulebased(name)
        ai_print("fallback used (rule-based) | input: %s | arabic: %s" % (name, d["arabic"]))
        return d


class NameResolver(QObject):
    resolved = Signal(str, str, str, float)

    def __init__(self, dictionary=None, rulebased_fn=None, known_fn=None, model_dir=None, parent=None):
        super().__init__(parent)
        self._dict = dictionary or {}
        self._rb = rulebased_fn or (lambda n: n)
        self._known = known_fn
        self._model_dir = model_dir or os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")
        self._cache = OrderedDict()
        self._prov = {}
        self._q = queue.Queue()
        self._stop = threading.Event()
        self._worker = _Worker(self._q, self._stop, self._dict, self._rb, self._model_dir)
        self._worker.resolved.connect(self._on_worker_resolved)
        self._worker.start()

    def _cache_put(self, k, v):
        self._cache[k] = v
        self._cache.move_to_end(k)
        while len(self._cache) > 1024:
            self._cache.popitem(last=False)

    def cache_set(self, name, arabic):
        if arabic:
            self._cache_put(name, arabic)

    def provenance(self, name):
        return self._prov.get(name, "unknown")

    def _on_worker_resolved(self, name, arabic, cls, conf):
        if arabic:
            self._cache_put(name, arabic)
        self._prov[name] = "model" if cls in ("canonical_arabic", "transliteration") else "fallback"
        self.resolved.emit(name, arabic, cls, conf)

    def fast_or_cached(self, name):
        if name in self._cache:
            self._prov[name] = "cache"
            return self._cache[name]
        if self._known:
            try:
                d = self._known(name)
            except Exception:
                d = None
            if d:
                self._prov[name] = "dictionary"
                self._cache_put(name, d)
                return d
        return ""

    def resolve_async(self, name, reqid):
        self._q.put(("resolve", reqid, name))

    def warmup(self):
        self._q.put(("load",))

    def wait_loaded(self, timeout=180.0):
        deadline = time.time() + timeout
        while self._worker._state is None and time.time() < deadline:
            QCoreApplication.processEvents()
            time.sleep(0.02)
        return self._worker._state

    def resolve_sync(self, name, timeout=180.0):
        box = {"arabic": None, "cls": None, "conf": None, "done": False}

        def slot(n, a, c, conf):
            if n == name and not box["done"]:
                box["arabic"] = a
                box["cls"] = c
                box["conf"] = conf
                box["done"] = True

        self.resolved.connect(slot)
        try:
            self.resolve_async(name, 0)
            deadline = time.time() + timeout
            while not box["done"] and time.time() < deadline:
                QCoreApplication.processEvents()
                time.sleep(0.01)
        finally:
            try:
                self.resolved.disconnect(slot)
            except Exception:
                pass
        box["source"] = self.provenance(name)
        return box

    def shutdown(self):
        self._stop.set()
        try:
            self._q.put(None)
        except Exception:
            pass
        try:
            self._worker.wait(2000)
        except Exception:
            pass
