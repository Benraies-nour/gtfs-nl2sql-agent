"""Normalization of a place name: the search form shared by user input and the database.

Lowercase, no accents or punctuation, Arabic → Latin, arabizi, articles and
unambiguous abbreviations. It is only used to match texts: the names shown
to the agent and to the user are always the database ones.
"""
import re
import unicodedata

# Arabic → Latin, the way Tunisian names are written in the database (ج → j, ش → ch…).
_ARABIC = {
    "ا": "a", "أ": "a", "إ": "a", "آ": "a", "ء": "", "ؤ": "ou", "ئ": "i",
    "ب": "b", "ت": "t", "ث": "th", "ج": "j", "ح": "h", "خ": "kh", "د": "d",
    "ذ": "dh", "ر": "r", "ز": "z", "س": "s", "ش": "ch", "ص": "s", "ض": "dh",
    "ط": "t", "ظ": "dh", "ع": "a", "غ": "gh", "ف": "f", "ق": "k", "ك": "k",
    "ل": "l", "م": "m", "ن": "n", "ه": "h", "ة": "a", "و": "ou", "ي": "i",
    "ى": "a", "ـ": "",
}
_ARABIC_ARTICLE = re.compile(r"(?<![؀-ۿ])ال")
_ARABIC_DIACRITICS = re.compile(r"[ً-ْ]")

# Arabizi: a lone digit attached to a letter ("9ayrawen", "7ammam").
# Real numbers ("ligne 21", "kilometre 17") are left untouched.
_ARABIZI = {"2": "a", "3": "a", "5": "kh", "7": "h", "9": "q"}
_ARABIZI_DIGIT = re.compile(r"(?<=[a-z])[23579](?!\d)|(?<!\d)[23579](?=[a-z])")

# Only unambiguous abbreviations are expanded (whole word).
_ABBREVIATIONS = {"kai": "kairouan", "kair": "kairouan", "s": "sidi", "med": "mohamed"}
_M_ALI = re.compile(r"\bm ali\b")

_ARTICLE_WORDS = {"el", "al", "l"}
# Article attached to the word: elfahs → fahs, essaied → saied, ennasr → nasr,
# echatt → chatt, ejbil → jbil. "el" + vowel is kept (eleves).
_GLUED_ARTICLE = re.compile(
    r"^(?:el(?=[b-df-hj-np-tv-z][a-z]{2})|e([b-df-hj-np-tv-z])\1|e(?=ch)|e(?=j))"
)
_ELIDED_L = re.compile(r"\bl['’]")


def normalize(text: str) -> str:
    """Search form of a name: lowercase, no accents or articles."""
    if not text:
        return ""
    text = _ARABIC_DIACRITICS.sub("", text)
    text = _ARABIC_ARTICLE.sub(" el ", text)
    text = "".join(_ARABIC.get(ch, ch) for ch in text)

    text = unicodedata.normalize("NFKD", text.lower())
    text = "".join(ch for ch in text if not unicodedata.combining(ch))

    text = _ARABIZI_DIGIT.sub(lambda m: _ARABIZI[m.group(0)], text)
    text = _ELIDED_L.sub(" ", text)
    text = text.replace("'", "").replace("’", "")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    text = _M_ALI.sub("mohamed ali", text)

    words = []
    for word in text.split():
        if word in _ARTICLE_WORDS:
            continue
        word = _ABBREVIATIONS.get(word, word)
        words.append(_GLUED_ARTICLE.sub(lambda m: m.group(1) or "", word, count=1))
    return " ".join(words)
