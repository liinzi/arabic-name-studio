"""
Arabic Name Intelligence v4 (pure Python).
Adds broad surname/nisba/regional coverage and an Arabic-aware phonetic engine
that drops short vowels (Arabic omits them), keeps long vowels, and vocalizes
initial/final vowels - so unknown names read as natural consonantal Arabic.
Priority: VIP exact -> VIP partial -> canonical DB -> linguistic -> fuzzy ->
(Qwen) -> improved phonetic. Harakat on by default (set_harakat(False) off).
"""
import re
import json

def norm(s):
    s = (s or "").strip().lower()
    s = re.sub(r"['`.,]", " ", s)
    s = re.sub(r"[-_]", " ", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()

def _lev(a, b, cap=3):
    if abs(len(a) - len(b)) >= cap:
        return cap
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]

TITLES_DROP = {"mr", "mrs", "ms", "miss", "dr", "doctor", "prof", "professor",
               "sir", "master", "eng", "engineer", "barrister", "zo", "esq"}

WORD_VOC = {
    "محمد": "مُحَمَّد", "أحمد": "أَحْمَد", "محمود": "مَحْمُود", "يوسف": "يُوسُف",
    "علي": "عَلِيّ", "حسن": "حَسَن", "حسين": "حُسَيْن", "خالد": "خَالِد", "عمر": "عُمَر",
    "إبراهيم": "إِبْرَاهِيم", "إسماعيل": "إِسْمَاعِيل", "مريم": "مَرْيَم", "فاطمة": "فَاطِمَة",
    "عائشة": "عَائِشَة", "خديجة": "خَدِيجَة", "زينب": "زَيْنَب", "مصطفى": "مُصْطَفَى",
    "عبد": "عَبْدُ", "الله": "اللَّهُ", "الرحمن": "الرَّحْمَنِ", "الرحيم": "الرَّحِيمِ",
    "الحميد": "الْحَمِيدِ", "الصمد": "الصَّمَدِ", "السلام": "السَّلَامِ", "العزيز": "الْعَزِيزِ",
    "الكريم": "الْكَرِيمِ", "الملك": "الْمَلِكِ", "القدير": "الْقَدِيرِ", "اللطيف": "اللَّطِيفِ",
    "الناصر": "النَّاصِرِ", "الفتاح": "الْفَتَّاحِ", "الغفار": "الْغَفَّارِ", "المجيد": "الْمَجِيدِ",
    "العليم": "الْعَلِيمِ", "الحكيم": "الْحَكِيمِ", "الرزاق": "الرَّزَّاقِ", "الوهاب": "الْوَهَّابِ",
    "التواب": "التَّوَّابِ", "الشكور": "الشَّكُورِ", "الغفور": "الْغَفُورِ", "الرؤوف": "الرَّؤُوفِ",
    "الودود": "الْوَدُودِ", "الحفيظ": "الْحَفِيظِ", "السميع": "السَّمِيعِ", "البصير": "الْبَصِيرِ",
    "الجليل": "الْجَلِيلِ", "الكبير": "الْكَبِيرِ", "الخالق": "الْخَالِقِ", "الغني": "الْغَنِيِّ",
    "الهادي": "الْهَادِي", "النور": "النُّورِ", "الرشيد": "الرَّشِيدِ", "الصبور": "الصَّبُورِ",
    "الواحد": "الْوَاحِدِ", "الأحد": "الْأَحَدِ", "القيوم": "الْقَيُّومِ", "الماجد": "الْمَاجِدِ",
    "الحاج": "الْحَاجُّ", "الشيخ": "الشَّيْخُ", "الإمام": "الْإِمَامُ", "حنفي": "حَنَفِيّ",
}

VIP_PEOPLE = [
    {"full": "دوسونمو مصباح جامعو",
     "aliases": ["dosunmu misbaah jaamiu", "dosunmu misbah jamiu", "misbaah jaamiu"],
     "components": [
         (["dosunmu", "dosonmu"], "دوسونمو"),
         (["misbaah", "misbah", "misba"], "مصباح"),
         (["jaamiu", "jamiu", "jamio"], "جامعو")]},
    {"full": "سلطان حنفي",
     "aliases": ["sultan hanafi", "sultan hanafi zo", "sultan hanafi z o"],
     "components": [
         (["sultan"], "سلطان"),
         (["hanafi", "hanafi", "hanfy"], "حنفي")]},
    {"full": "الحاج كاظم إيغي",
     "aliases": ["alhaji kazeem ige", "kazeem ige"],
     "components": [
         (["alhaji"], "الحاج"),
         (["kazeem", "kadhim", "kazim"], "كاظم"),
         (["ige"], "إيغي")]},
    {"full": "الحاج ميكائيل أنوفي",
     "aliases": ["alhaji mikaheel anofi", "mikaheel anofi"],
     "components": [
         (["alhaji"], "الحاج"),
         (["mikaheel", "mikaeel"], "ميكائيل"),
         (["anofi", "anoffi"], "أنوفي")]},
    {"full": "الشيخ حبيب أدي ووي",
     "aliases": ["shaykh habeeb adewuyi", "habeeb adewuyi"],
     "components": [
         (["shaykh", "sheikh"], "الشيخ"),
         (["habeeb", "habib"], "حبيب"),
         (["adewuyi"], "أدي ووي")]},
    {"full": "الإمام سني ك يوسف",
     "aliases": ["imam sanni k yusuf", "imam sanni yusuf", "sanni k yusuf"],
     "components": [
         (["imam"], "الإمام"),
         (["sanni", "sani"], "سني"),
         (["k"], "ك"),
         (["yusuf"], "يوسف")]},
    {"full": "إسماعيل أديبيسي",
     "aliases": ["ismail adebisi", "mr ismail adebisi"],
     "components": [
         (["ismail"], "إسماعيل"),
         (["adebisi"], "أديبيسي")]},
    {"full": "عبد الله إبراهيم",
     "aliases": ["abdullah ibrahim", "mr abdullah ibrahim"],
     "components": [
         (["abdullah", "abdallah"], "عبد الله"),
         (["ibrahim", "ibraheem"], "إبراهيم")]},
]

ABD_PREFIXES = sorted(["abdul", "abdel", "abdur", "abdoul", "abdus", "abd", "abdl"],
                      key=len, reverse=True)

ASMA = [
    ("الرحمن", ["rahman", "rehman"]), ("الرحيم", ["raheem", "rahim"]),
    ("الملك", ["malik", "malek"]), ("السلام", ["salam", "salem"]),
    ("العزيز", ["aziz", "azez"]), ("الحميد", ["hameed", "hamid"]),
    ("الكريم", ["karim", "kareem"]), ("الغفور", ["ghafour", "ghafur"]),
    ("الغفار", ["ghaffar", "ghafar"]), ("الرزاق", ["razzaq", "razaq"]),
    ("الفتاح", ["fattah", "fatah"]), ("العليم", ["alim", "aleem"]),
    ("الحكيم", ["hakim", "hakeem"]), ("اللطيف", ["latif", "lateef"]),
    ("الودود", ["wadood", "wadud"]), ("المجيد", ["majid", "majeed"]),
    ("الواحد", ["wahid", "wahed"]), ("الأحد", ["ahad"]), ("الصمد", ["samad", "samed"]),
    ("القادر", ["qadir", "qader"]), ("القيوم", ["qayyum", "qayoum"]),
    ("الماجد", ["majid", "majed"]), ("الرشيد", ["rashid", "rasheed"]),
    ("الصبور", ["sabour", "sabur"]), ("الهادي", ["hadi"]), ("النور", ["noor", "nur"]),
    ("الخالق", ["khaliq", "khaleq"]), ("الباري", ["bari"]), ("المصور", ["musawwir"]),
    ("الوهاب", ["wahhab", "wahab"]), ("التواب", ["tawwab", "tawab"]),
    ("الرؤوف", ["rauf", "raouf"]), ("العفو", ["afuw", "afuww"]),
    ("السميع", ["samee", "sami"]), ("البصير", ["basir", "baseer"]),
    ("الجليل", ["jalil", "jaleel"]), ("الكبير", ["kabir", "kabeer"]),
    ("الحفيظ", ["hafiz", "hafeez"]), ("الوكيل", ["wakil", "wakeel"]),
    ("المتين", ["matin", "mateen"]), ("الولي", ["wali", "walee"]),
    ("الشكور", ["shakoor", "shakur"]), ("العلي", ["ali", "aliy"]),
    ("العظيم", ["azim", "azeem"]), ("الحليم", ["halim", "haleem"]),
    ("الخبير", ["khabir", "khabeer"]), ("العدل", ["adl", "adil"]), ("الحكم", ["hakam"]),
]

MALE = [
    ("محمد", ["muhammad", "mohammed", "mohamed", "mohamad", "muhammed", "mohammad", "mohd"]),
    ("أحمد", ["ahmed", "ahmad", "ahmet"]), ("محمود", ["mahmoud", "mahmood", "mahmud"]),
    ("يوسف", ["yusuf", "yousef", "yousuf", "youssef"]), ("علي", ["ali", "ally"]),
    ("حسن", ["hassan", "hasan"]), ("حسين", ["hussein", "husain", "hussain", "husayn"]),
    ("خالد", ["khalid", "khaled", "kalid"]), ("عمر", ["omar", "umar", "umer"]),
    ("إبراهيم", ["ibrahim", "ibraheem"]), ("إسماعيل", ["ismail", "ismael"]),
    ("عبدالله", ["abdullah", "abdallah"]), ("عبدالرحمن", ["abdulrahman", "abdelrahman", "abdurrahman"]),
    ("عبدالحميد", ["abdulhameed", "abdulhamid", "abdelhamid"]),
    ("كريم", ["karim", "kareem"]), ("رشيد", ["rashid", "rashed", "rasheed"]),
    ("سعيد", ["saeed", "said", "sayeed"]), ("طارق", ["tariq", "tarek"]),
    ("ياسر", ["yasser", "yaser", "yasir"]), ("ماجد", ["majed", "majid"]),
    ("وليد", ["waleed", "walid"]), ("فهد", ["fahad", "fahd"]), ("سلطان", ["sultan"]),
    ("ناصر", ["nasser", "naser"]), ("أنس", ["anas"]), ("أسامة", ["osama", "usama"]),
    ("زيد", ["zaid", "zayd"]), ("سلمان", ["salman"]), ("عادل", ["adel", "adil"]),
    ("جمال", ["jamal"]), ("نبيل", ["nabil"]), ("سمير", ["samir", "sameer"]),
    ("هشام", ["hisham", "hesham"]), ("أمير", ["amir", "ameer", "emir"]),
    ("باسم", ["bassem", "basim"]), ("رامي", ["rami", "ramy"]), ("تامر", ["tamer", "tamir"]),
    ("حسام", ["hossam", "hosam"]), ("محسن", ["mohsen", "muhsin"]),
    ("فاروق", ["farouk", "farooq"]), ("منصور", ["mansour", "mansoor"]),
    ("إلياس", ["ilyas", "elias"]), ("هارون", ["harun", "haroon"]),
    ("لقمان", ["luqman", "lokman"]), ("قاسم", ["qasim", "kasim", "qassem"]),
    ("عباس", ["abbas"]), ("جعفر", ["jaafar", "jafar"]), ("كاظم", ["kadhim", "kazim", "kazeem"]),
    ("مهدي", ["mahdi", "mehdi"]), ("رضا", ["reza", "rida"]), ("صادق", ["sadiq", "sadeq"]),
    ("حيدر", ["haider", "haidar", "heydar"]), ("مرتضى", ["murtada", "murtadha", "murtaza"]),
    ("البخاري", ["bukhari"]), ("الغزالي", ["ghazali", "ghazzali"]),
    ("الشافعي", ["shafii", "shafiei"]), ("النووي", ["nawawi"]), ("الرازي", ["razi"]),
    ("ابن خلدون", ["khaldun", "khaldoun"]), ("ابن سينا", ["sina"]),
]
FEMALE = [
    ("فاطمة", ["fatima", "fatimah", "fatma"]), ("عائشة", ["aisha", "ayesha", "aishah", "aysha"]),
    ("خديجة", ["khadija", "khadijah", "khadeeja"]), ("مريم", ["maryam", "mariam", "meriam"]),
    ("زينب", ["zainab", "zeynab", "zaynab"]), ("حفصة", ["hafsah", "hafsa"]),
    ("سارة", ["sarah", "sara"]), ("نور", ["noor", "nur", "nour"]),
    ("ليلى", ["layla", "leila", "laila", "lila"]), ("هدى", ["huda"]),
    ("مها", ["maha"]), ("ريم", ["reem", "rim"]), ("داليا", ["dalia", "dahlia"]),
    ("لمياء", ["lamia"]), ("أسماء", ["asma", "asmaa"]), ("هبة", ["heba", "hiba"]),
    ("دينا", ["dina", "deena"]), ("نادين", ["nadine", "nadeen"]), ("مايا", ["maya"]),
    ("رانيا", ["rania", "ranya"]), ("أميرة", ["amira", "ameera"]), ("سلمى", ["salma", "selma"]),
    ("ياسمين", ["yasmin", "yasmeen"]), ("صفية", ["safiyah", "safiya", "sofiyah", "sofiya"]),
    ("رقية", ["ruqayya", "ruqaiya"]), ("سكينة", ["sakina", "sakeena"]),
    ("آمنة", ["amina", "ameena", "aminah"]), ("حليمة", ["halima", "haleema"]),
    ("سمية", ["sumaya", "sumayya"]), ("أروى", ["arwa"]), ("إيمان", ["iman", "eiman"]),
    ("جنى", ["jana"]), ("لينا", ["lina", "leena"]), ("ملاك", ["malak"]),
]
# surnames / nisba / regional (West-African, Middle-Eastern, South-Asian, etc.)
EXTRA = [
    ("حنفي", ["hanafi", "hanofi", "hanfy", "hanafi", "anafi"]),
    ("أنوفي", ["anofi", "anofi", "anoffi", "anofi"]),
    ("عالية", ["aleeyah", "aaliyah", "aliyah", "aleah", "aliah", "aaliya", "aliya", "aleeya", "aaliya"]),
    ("أديبيسي", ["adebisi", "adebisi"]),
    ("أدي ووي", ["adewuyi", "adewuyi"]),
    ("إيغي", ["ige", "igeh"]),
    ("دوسونمو", ["dosunmu", "dosonmu"]),
    ("كاظم", ["kazeem", "kadhim", "kazim"]),
    ("مصباح", ["misbaah", "misbah", "misba"]),
    ("جامعو", ["jaamiu", "jamiu", "jamio"]),
    ("ميكائيل", ["mikaheel", "mikaeel", "mikaheel"]),
    ("سني", ["sanni", "sani"]),
    ("المالكي", ["maliki"]), ("الحنبلي", ["hanbali"]),
    ("غباداموسي", ["gbadamosi"]), ("اولورونيسولا", ["olorunnisola"]),
    ("أديولا", ["adeola"]), ("باباتوندي", ["babatunde", "babatunji"]),
    ("أبوبكر", ["abubakar", "abubakar", "abubaker"]),
    ("عثمان", ["usman", "usman", "othman", "usmanu"]),
    ("موسى", ["musa", "musa", "moussa"]), ("بello", ["bello", "bello"]),
    ("دانجوم", ["danjuma", "danjuma"]), ("ساني", ["sani", "sani"]),
    ("إدريس", ["idris", "idris", "idriss"]), ("مريم", ["maryam"]),
    ("أمينو", ["aminu", "aminu"]), ("كابو", ["kabir", "kabiru"]),
]

# ---------------------------------------------------------------- build
ALIAS = {}
CONF = {}
ATTR_SUFFIX = {}
FUZZ_INDEX = {}
VIP_ALIAS = {}
COMP_INDEX = {}
VIP = []

def _put(alias, canon, conf):
    a = norm(alias)
    for key in (a, a.replace(" ", "")):
        if not key:
            continue
        if key not in ALIAS or conf > CONF.get(key, 0):
            ALIAS[key] = canon
            CONF[key] = conf

def _expand(v):
    return [x for x in {v, v.replace("ee", "i"), v.replace("oo", "u"), v.replace("ou", "u")} if x]

for canon, variants in MALE:
    for v in variants:
        for e in _expand(v):
            _put(e, canon, 0.99)
for canon, variants in FEMALE:
    for v in variants:
        for e in _expand(v):
            _put(e, canon, 0.99)
for canon, variants in EXTRA:
    for v in variants:
        for e in _expand(v):
            _put(e, canon, 0.99)
for canon, variants in ASMA:
    for v in variants:
        ATTR_SUFFIX[v] = canon
        for e in _expand(v):
            ATTR_SUFFIX.setdefault(e, canon)
            for abd in ABD_PREFIXES:
                _put(abd + " " + e, "عبد " + canon, 0.99)
                _put(abd + e, "عبد " + canon, 0.98)
for i, person in enumerate(VIP_PEOPLE):
    VIP.append(person)
    for a in person.get("aliases", []):
        VIP_ALIAS[norm(a)] = person["full"]
    for ci, (vars_, ar) in enumerate(person["components"]):
        for v in vars_:
            COMP_INDEX.setdefault(norm(v), []).append((i, ci))
for key in ALIAS:
    FUZZ_INDEX.setdefault(key[:2], []).append(key)

# ---------------------------------------------------------------- phonetic (Arabic-aware)
CONS = {'b': 'ب', 'p': 'ب', 't': 'ت', 'd': 'د', 'r': 'ر', 'n': 'ن', 'm': 'م', 'l': 'ل',
        's': 'س', 'z': 'ز', 'f': 'ف', 'v': 'ف', 'g': 'ج', 'j': 'ج', 'k': 'ك', 'q': 'ك',
        'c': 'ك', 'w': 'و', 'y': 'ي', 'h': 'ه', 'x': 'خ', 'ʃ': 'ش', 'θ': 'ث',
        'ð': 'ذ', 'ɣ': 'غ', 'tʃ': 'تش'}
LONG = {'I': 'ي', 'U': 'و', 'A': 'ا', 'AY': 'ي'}
INIT = {'a': 'ا', 'e': 'إ', 'i': 'إ', 'o': 'أ', 'u': 'أ'}
FINAL = {'a': 'ى', 'e': 'ي', 'i': 'ي', 'o': 'و', 'u': 'و'}

# ---------------------------------------------------------------- engine
class Transliterator:
    def __init__(self):
        self.names = ALIAS
        self.part2 = ATTR_SUFFIX
        self.phrases = VIP_ALIAS
        self.vip = VIP_ALIAS
        self.harakat = True
        self._memo = {}

    def set_harakat(self, on):
        self.harakat = bool(on)

    def vocalize(self, text):
        if not self.harakat or not text:
            return text
        return " ".join(WORD_VOC.get(w, w) for w in text.split())

    def _split_abd(self, token):
        for p in ABD_PREFIXES:
            if token.startswith(p):
                rest = token[len(p):]
                if rest in ATTR_SUFFIX:
                    return ("عبد " + ATTR_SUFFIX[rest], 0.98)
                if rest.startswith("ul") and rest[2:] in ATTR_SUFFIX:
                    return ("عبد " + ATTR_SUFFIX[rest[2:]], 0.97)
        return None

    def _fuzzy(self, t):
        if len(t) < 5:
            return None
        best, bestd = None, 3
        for k in FUZZ_INDEX.get(t[:2], []):
            if abs(len(k) - len(t)) > 2:
                continue
            d = _lev(t, k, 3)
            if d < bestd:
                bestd, best = d, k
        if best is not None and bestd <= 2:
            return ALIAS[best], max(0.55, 0.92 - 0.15 * bestd)
        return None

    def _vip_partial(self, toks):
        vip = None
        matched = []
        for t in toks:
            cands = COMP_INDEX.get(t)
            if not cands:
                return None
            chosen = None
            for (i, ci) in cands:
                if vip is None or i == vip:
                    chosen = (i, ci)
                    vip = i
                    break
            if chosen is None:
                return None
            matched.append(chosen)
        if not matched or vip is None:
            return None
        person = VIP[vip]
        idxs = sorted(set(ci for (_, ci) in matched))
        return " ".join(person["components"][ci][1] for ci in idxs), 1.0

    def search(self, text, limit=20):
        t = norm(text)
        out = []
        if t in ALIAS:
            out.append(("exact", ALIAS[t], CONF[t]))
        for key, canon in ALIAS.items():
            if len(out) >= limit:
                break
            if key.startswith(t) or t.startswith(key):
                out.append(("prefix", canon, CONF[key]))
            elif key.endswith(t) or t.endswith(key):
                out.append(("suffix", canon, CONF[key]))
        fz = self._fuzzy(t)
        if fz:
            out.append(("fuzzy", fz[0], fz[1]))
        return out

    def known_with_conf(self, text):
        t = norm(text)
        if not t:
            return None, 0.0
        if t in self._memo:
            return self._memo[t]
        res = self._recognize(t)
        self._memo[t] = res
        return res

    def _recognize(self, t):
        if t in VIP_ALIAS:
            return VIP_ALIAS[t], 1.0
        for key in (t, t.replace(" ", "")):
            if key in ALIAS:
                return ALIAS[key], CONF[key]
        toks = [x for x in t.split() if x not in TITLES_DROP]
        vp = self._vip_partial(toks)
        if vp:
            return vp
        fz = self._fuzzy(t.replace(" ", ""))
        if fz:
            return fz
        out, confs = [], []
        i = 0
        n = len(toks)
        while i < n:
            hit = None
            two = " ".join(toks[i:i + 2]) if i + 1 < n else None
            if two and two in ALIAS:
                hit = (ALIAS[two], CONF[two]); i += 2
            elif toks[i] in ALIAS:
                hit = (ALIAS[toks[i]], CONF[toks[i]]); i += 1
            elif toks[i] in ("abu", "abou") and i + 1 < n and self._one(toks[i + 1]):
                hit = ("أبو " + self._one(toks[i + 1]), 0.95); i += 2
            elif toks[i] in ("ibn", "bin") and i + 1 < n and self._one(toks[i + 1]):
                hit = ("ابن " + self._one(toks[i + 1]), 0.95); i += 2
            elif toks[i] == "bint" and i + 1 < n and self._one(toks[i + 1]):
                hit = ("بنت " + self._one(toks[i + 1]), 0.95); i += 2
            elif toks[i] in ("al", "el") and i + 1 < n and self._one(toks[i + 1]):
                hit = ("ال" + self._one(toks[i + 1]), 0.93); i += 2
            else:
                sp = self._split_abd(toks[i])
                if sp:
                    hit = sp; i += 1
                else:
                    fz = self._fuzzy(toks[i])
                    if fz:
                        hit = fz; i += 1
                    else:
                        return None, 0.0
            out.append(hit[0]); confs.append(hit[1])
        return " ".join(out), min(confs)

    def _one(self, tok):
        if tok in ALIAS:
            return ALIAS[tok]
        sp = self._split_abd(tok)
        return sp[0] if sp else None

    def known(self, text):
        ar, conf = self.known_with_conf(text)
        if ar and conf >= 0.9:
            return self.vocalize(ar)
        return None

    def is_name_mode(self, text):
        ar, conf = self.known_with_conf(text)
        if ar:
            return True
        toks = [x for x in norm(text).split() if x not in TITLES_DROP]
        if not toks or len(toks) > 6:
            return False
        known = sum(1 for tok in toks if tok in ALIAS or self._split_abd(tok) or tok in COMP_INDEX)
        return (known / float(len(toks))) >= 0.5

    def transliterate(self, text):
        t = norm(text)
        if not t:
            return ""
        ar, conf = self.known_with_conf(t)
        if ar:
            return self.vocalize(ar)
        toks = [x for x in t.split() if x not in TITLES_DROP]
        out = []
        i = 0
        n = len(toks)
        while i < n:
            two = " ".join(toks[i:i + 2]) if i + 1 < n else None
            if two and two in ALIAS:
                out.append(ALIAS[two]); i += 2; continue
            if toks[i] in ALIAS:
                out.append(ALIAS[toks[i]]); i += 1; continue
            sp = self._split_abd(toks[i])
            if sp:
                out.append(sp[0]); i += 1; continue
            out.append(self._phonetic(toks[i])); i += 1
        return self.vocalize(" ".join(out))

    def _phonetic(self, text):
        t = text.lower()
        t = (t.replace("sh", "ʃ").replace("kh", "x").replace("th", "θ").replace("gh", "ɣ")
              .replace("dh", "ð").replace("ch", "tʃ").replace("ph", "f")
              .replace("ee", "I").replace("oo", "U").replace("aa", "A").replace("ou", "U")
              .replace("ay", "AY").replace("ei", "AY"))
        n = len(t)
        out = []
        for i, ch in enumerate(t):
            if ch in LONG:
                out.append(LONG[ch]); continue
            if ch in "aeiou":
                if i == 0:
                    out.append(INIT[ch])
                elif i == n - 1:
                    out.append(FINAL[ch])
                continue
            out.append(CONS.get(ch, ""))
        s = "".join(out).replace("اا", "ا").replace("يي", "ي").replace("وو", "و")
        return s or text

    def load_json(self, path):
        try:
            with open(path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            added = 0
            for entry in data:
                canon = entry.get("canonical_arabic", "")
                conf = float(entry.get("confidence_score", 0.99) or 0.99)
                if not canon:
                    continue
                for v in (entry.get("name_variations", []) + entry.get("alternative_spellings", [])):
                    _put(v, canon, conf)
                    added += 1
            for key in ALIAS:
                FUZZ_INDEX.setdefault(key[:2], []).append(key)
            self._memo.clear()
            return added
        except Exception:
            return 0

    def stats(self):
        return {"alias_keys": len(ALIAS), "vip": len(VIP), "vip_aliases": len(VIP_ALIAS),
                "asma": len(ASMA), "male": len(MALE), "female": len(FEMALE),
                "extra": len(EXTRA), "vocalized_words": len(WORD_VOC)}
