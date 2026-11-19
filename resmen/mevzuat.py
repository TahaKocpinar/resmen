"""Fetch Turkish legislation from mevzuat.gov.tr and split it into articles."""
from __future__ import annotations

import html
import re
import time
import urllib.error
import urllib.request

BASE = "https://www.mevzuat.gov.tr"
# The public page wraps the text in an iframe; this is the iframe's own URL.
IFRAME = BASE + "/anasayfa/MevzuatFihristDetayIframe?MevzuatTur={tur}&MevzuatNo={no}&MevzuatTertip={tertip}"
PAGE = BASE + "/mevzuat?MevzuatNo={no}&MevzuatTur={tur}&MevzuatTertip={tertip}"
UA = "Mozilla/5.0 (compatible; resmen; +https://github.com/TahaKocpinar/resmen)"

_ARTICLE = re.compile(
    r"(?:^|\n)[ \t]*((?:ek|geçici)[ \t\n]+)?madde[ \t\n]+(\d+(?:/[A-ZÇĞİÖŞÜ])?)[ \t]*[-–—]",
    re.IGNORECASE,
)

_NOTES = re.compile(r"\n\[1\] ")


def page_url(no: str, tur: int = 1, tertip: int = 5) -> str:
    return PAGE.format(no=no, tur=tur, tertip=tertip)


def fetch(no: str, tur: int = 1, tertip: int = 5, attempts: int = 5, timeout: int = 60) -> str:
    # mevzuat.gov.tr drops a fair share of connections; backing off and retrying
    # is enough in practice, it rarely needs more than three tries.
    url = IFRAME.format(no=no, tur=tur, tertip=tertip)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    last: Exception | None = None
    for i in range(attempts):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read().decode("utf-8", errors="replace")
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            last = e
            time.sleep(min(2**i, 20))
    raise RuntimeError(f"mevzuat.gov.tr: {no} could not be fetched ({last})")


def to_text(page: str) -> str:
    page = re.sub(r"<(script|style)\b.*?</\1>", " ", page, flags=re.S | re.I)
    page = re.sub(r"<(br|p|/p|div|/div|tr|/tr)\b[^>]*>", "\n", page, flags=re.I)
    text = html.unescape(re.sub(r"<[^>]+>", "", page))
    text = re.sub(r"[ \t\xa0\u200b]+", " ", text)
    return re.sub(r"\n\s*\n+", "\n", text).strip()


def article_key(prefix: str | None, number: str) -> str:
    # str.lower() turns "GEÇİCİ" into "geçi̇ci̇" (i + combining dot), so the
    # prefix is classified instead of lowercased.
    prefix = (prefix or "").strip()
    if not prefix:
        return number
    return ("ek " if prefix[:2].upper() == "EK" else "geçici ") + number


def split_articles(text: str) -> dict[str, str]:
    """Map article keys ("17", "ek 3", "geçici 1", "18/B", "dipnotlar") to their text.

    Each slice runs to the next article heading, so it may end with the
    caption of the following article; quotes never span that far.
    """
    matches = list(_ARTICLE.finditer(text))
    out: dict[str, str] = {}
    notes = _NOTES.search(text, matches[-1].end()) if matches else None
    tail = notes.start() if notes else len(text)
    for i, m in enumerate(matches):
        key = article_key(m.group(1), m.group(2).upper())
        end = matches[i + 1].start() if i + 1 < len(matches) else tail
        out.setdefault(key, text[m.start():end].strip())
    if notes:
        # Amendment footnotes ("[24] 22/4/2026 tarihli ve 7578 sayılı Kanunun ...")
        # are the only place that says which law changed a sentence and when.
        out["dipnotlar"] = text[notes.start():].strip()
    return out


def normalize(s: str) -> str:
    """Whitespace- and footnote-insensitive form used for quote matching."""
    s = re.sub(r"\[\d+\]", "", s)
    s = s.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    s = re.sub(r"[-–—]", "-", s)
    return re.sub(r"\s+", " ", s).strip()
