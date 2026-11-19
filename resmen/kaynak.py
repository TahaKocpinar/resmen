"""Pins: verbatim quotes from official texts that every claim in the guides points to."""
from __future__ import annotations

import datetime as dt
import difflib
import re
import shutil
import subprocess
import tempfile
import tomllib
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

from . import mevzuat

REF = re.compile(r"\[\^([A-Za-z0-9_-]+)\]")
FOOTDEF = re.compile(r"^\[\^[^\]]+\]:.*$", re.M)
BLOCK = re.compile(r"(<!-- resmen:(\S+) -->\n)(.*?)(<!-- /resmen -->)", re.S)


@dataclass
class Pin:
    id: str
    alinti: str | list[str]
    kanun: str | None = None
    madde: str | None = None
    url: str | None = None
    baslik: str | None = None

    @property
    def is_law(self) -> bool:
        return self.kanun is not None

    @property
    def quotes(self) -> list[str]:
        return [self.alinti] if isinstance(self.alinti, str) else list(self.alinti)


@dataclass
class Problem:
    level: str  # "hata" fails the check, "uyarı" does not
    where: str
    msg: str

    def __str__(self) -> str:
        return f"{self.level}: {self.where}: {self.msg}"


@dataclass
class Repo:
    root: Path
    kanunlar: dict[str, dict] = field(default_factory=dict)
    pins: dict[str, Pin] = field(default_factory=dict)
    params: dict[str, list[dict]] = field(default_factory=dict)

    @classmethod
    def load(cls, root: Path | str) -> "Repo":
        root = Path(root)
        k = root / "kaynaklar"
        repo = cls(root)
        repo.kanunlar = {str(no): v for no, v in _toml(k / "kanunlar.toml").items()}
        for raw in _toml(k / "pinler.toml").get("pin", []):
            pin = Pin(**raw)
            if pin.id in repo.pins:
                raise ValueError(f"pinler.toml: '{pin.id}' iki kez tanımlı")
            repo.pins[pin.id] = pin
        repo.params = _toml(k / "parametreler.toml")
        return repo

    # snapshots -----------------------------------------------------------

    def snapshot_path(self, pin: Pin) -> Path:
        base = self.root / "kaynaklar" / "metin"
        if pin.is_law:
            return base / pin.kanun / (_slug(pin.madde) + ".txt")
        return base / "web" / (pin.id + ".txt")

    def snapshot(self, pin: Pin) -> str | None:
        p = self.snapshot_path(pin)
        return p.read_text(encoding="utf-8") if p.exists() else None

    def label(self, pin: Pin) -> str:
        if pin.is_law:
            ad = self.kanunlar.get(pin.kanun, {}).get("ad", "")
            if pin.madde == "dipnotlar":
                return f"{pin.kanun} sayılı {ad}, değişiklik dipnotları"
            kind, _, no = pin.madde.rpartition(" ")
            return f"{pin.kanun} sayılı {ad}, " + (f"{kind} md. {no}" if kind else f"md. {no}")
        return pin.baslik or pin.url

    def link(self, pin: Pin) -> str:
        if pin.is_law:
            k = self.kanunlar.get(pin.kanun, {})
            return mevzuat.page_url(pin.kanun, k.get("tur", 1), k.get("tertip", 5))
        return pin.url

    # guides --------------------------------------------------------------

    def guides(self) -> list[Path]:
        return sorted((self.root / "rehber").glob("*.md"))

    def render_blocks(self, text: str) -> str:
        refs = _ordered_refs(text)

        def fill(m: re.Match) -> str:
            kind = m.group(2)
            if kind == "dipnotlar":
                body = "".join(self.footnote(i) + "\n" for i in refs if i in self.pins)
            elif kind.startswith("tablo:"):
                body = self.table(kind.split(":", 1)[1])
            else:
                return m.group(0)
            return m.group(1) + body + m.group(4)

        return BLOCK.sub(fill, text)

    def footnote(self, pid: str) -> str:
        pin = self.pins[pid]
        quote = " … ".join(_squash(q) for q in pin.quotes)
        return f"[^{pid}]: {self.label(pin)}: “{quote}” ([kaynak]({self.link(pin)}))"

    def table(self, name: str) -> str:
        rows = self.params.get(name)
        if not rows:
            return f"<!-- '{name}' parametresi yok -->\n"
        out = ["| Dönem | Tutar (TL) | Kaynak |", "|---|---:|---|"]
        for r in sorted(rows, key=lambda r: r["baslangic"], reverse=True):
            pin = self.pins.get(r["kaynak"])
            src = f"[{self.label(pin)}]({self.link(pin)})" if pin else r["kaynak"]
            out.append(f"| {_d(r['baslangic'])} – {_d(r['bitis'])} | {_tl(r['tutar'])} | {src} |")
        return "\n".join(out) + "\n"

    def write_blocks(self) -> list[Path]:
        changed = []
        for g in self.guides():
            old = g.read_text(encoding="utf-8")
            new = self.render_blocks(old)
            if new != old:
                g.write_text(new, encoding="utf-8")
                changed.append(g)
        return changed

    # offline check -------------------------------------------------------

    def check(self, today: dt.date | None = None) -> list[Problem]:
        today = today or dt.date.today()
        probs: list[Problem] = []
        for pin in self.pins.values():
            where = f"pin {pin.id}"
            if pin.is_law and pin.kanun not in self.kanunlar:
                probs.append(Problem("hata", where, f"kanunlar.toml'da {pin.kanun} yok"))
                continue
            if not pin.is_law and not pin.url:
                probs.append(Problem("hata", where, "ne kanun/madde ne url verilmiş"))
                continue
            text = self.snapshot(pin)
            if text is None:
                probs.append(Problem("hata", where, f"kopya yok: {self.snapshot_path(pin).relative_to(self.root)} (resmen guncelle --yaz)"))
            elif not quote_in(pin.alinti, text):
                probs.append(Problem("hata", where, "alıntı kayıtlı metinde geçmiyor"))

        used: set[str] = set()
        for g in self.guides():
            text = g.read_text(encoding="utf-8")
            name = g.relative_to(self.root).as_posix()
            for pid in _ordered_refs(text):
                used.add(pid)
                if pid not in self.pins:
                    probs.append(Problem("hata", name, f"[^{pid}] pinler.toml'da tanımlı değil"))
            if self.render_blocks(text) != text:
                probs.append(Problem("hata", name, "dipnot/tablo blokları eski (resmen dipnot)"))

        for name, rows in self.params.items():
            rows = sorted(rows, key=lambda r: r["baslangic"])
            for r in rows:
                used.add(r["kaynak"])
                if r["kaynak"] not in self.pins:
                    probs.append(Problem("hata", f"parametre {name}", f"kaynak '{r['kaynak']}' tanımlı değil"))
                if r["bitis"] < r["baslangic"]:
                    probs.append(Problem("hata", f"parametre {name}", f"{r['baslangic']} dönemi ters"))
            for a, b in zip(rows, rows[1:]):
                if b["baslangic"] <= a["bitis"]:
                    probs.append(Problem("hata", f"parametre {name}", f"{a['baslangic']} ve {b['baslangic']} dönemleri çakışıyor"))
                elif b["baslangic"] != a["bitis"] + dt.timedelta(days=1):
                    probs.append(Problem("uyarı", f"parametre {name}", f"{a['bitis']} ile {b['baslangic']} arası boş"))
            if rows and rows[-1]["bitis"] < today:
                probs.append(Problem("uyarı", f"parametre {name}", f"son değer {rows[-1]['bitis']} tarihinde bitti, yenisi eklenmeli"))

        for pid in sorted(set(self.pins) - used):
            probs.append(Problem("uyarı", f"pin {pid}", "hiçbir rehberde kullanılmıyor"))
        return probs

    # online refresh ------------------------------------------------------

    def refresh(self, write: bool = False, fetch_law=mevzuat.fetch, fetch_url=None) -> list[dict]:
        """Compare snapshots with the live sources. Returns one dict per source."""
        fetch_url = fetch_url or _fetch_url
        report: list[dict] = []
        by_law: dict[str, list[Pin]] = {}
        for pin in self.pins.values():
            if pin.is_law:
                by_law.setdefault(pin.kanun, []).append(pin)

        for no, pins in sorted(by_law.items()):
            k = self.kanunlar.get(no, {})
            try:
                arts = mevzuat.split_articles(mevzuat.to_text(fetch_law(no, k.get("tur", 1), k.get("tertip", 5))))
            except Exception as e:  # a dead source is reported, not fatal
                report.append({"kaynak": f"{no} sayılı Kanun", "durum": "erişilemedi", "ayrinti": str(e)})
                continue
            for madde in sorted({p.madde for p in pins}, key=_article_order):
                name = f"{no} dipnotlar" if madde == "dipnotlar" else f"{no} md. {madde}"
                item = {"kaynak": name, "pinler": [], "diff": ""}
                live = arts.get(madde)
                group = [p for p in pins if p.madde == madde]
                if live is None:
                    item.update(durum="madde bulunamadı", pinler=[p.id for p in group])
                    report.append(item)
                    continue
                old = self.snapshot(group[0])
                broken = [p.id for p in group if not quote_in(p.alinti, live)]
                if old is not None and mevzuat.normalize(old) == mevzuat.normalize(live):
                    item["durum"] = "aynı"
                else:
                    item["durum"] = "yeni" if old is None else "değişti"
                    if old is not None:
                        item["diff"] = _diff(old, live, f"{no}/{madde}")
                    if write:
                        path = self.snapshot_path(group[0])
                        path.parent.mkdir(parents=True, exist_ok=True)
                        path.write_text(live + "\n", encoding="utf-8")
                if broken:
                    item["durum"] = "alıntı bozuldu"
                    item["pinler"] = broken
                report.append(item)

        for pin in (p for p in self.pins.values() if not p.is_law):
            item = {"kaynak": pin.url, "pinler": []}
            try:
                live = fetch_url(pin.url)
            except Exception as e:
                item.update(durum="erişilemedi", ayrinti=str(e))
                report.append(item)
                continue
            if quote_in(pin.alinti, live):
                item["durum"] = "aynı" if self.snapshot(pin) is not None else "yeni"
                if write and self.snapshot(pin) is None:
                    path = self.snapshot_path(pin)
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text(_excerpt(pin, live), encoding="utf-8")
            else:
                item.update(durum="alıntı bozuldu", pinler=[pin.id])
            report.append(item)
        return report


def quote_in(quote: str | list[str], text: str) -> bool:
    quotes = [quote] if isinstance(quote, str) else quote
    norm = mevzuat.normalize(text)
    return all(mevzuat.normalize(q) in norm for q in quotes)


def _excerpt(pin: Pin, text: str, margin: int = 160) -> str:
    # Only the neighbourhood of each quote is kept: enough to re-check offline
    # without copying whole third-party documents into the repository.
    norm = mevzuat.normalize(text)
    parts = [f"# {pin.url}", f"# alındı: {dt.date.today().isoformat()}"]
    for q in pin.quotes:
        i = norm.find(mevzuat.normalize(q))
        parts.append("… " + norm[max(i - margin, 0): i + len(mevzuat.normalize(q)) + margin] + " …")
    return "\n".join(parts) + "\n"


def _fetch_url(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": mevzuat.UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        data = r.read()
        ctype = r.headers.get("Content-Type", "")
    if url.lower().endswith(".pdf") or "pdf" in ctype:
        if not shutil.which("pdftotext"):
            raise RuntimeError("PDF kaynak için pdftotext (poppler-utils) gerekli")
        with tempfile.NamedTemporaryFile(suffix=".pdf") as f:
            f.write(data)
            f.flush()
            return subprocess.run(["pdftotext", "-layout", f.name, "-"], capture_output=True, text=True, check=True).stdout
    return mevzuat.to_text(data.decode("utf-8", errors="replace"))


def _toml(path: Path) -> dict:
    with open(path, "rb") as f:
        return tomllib.load(f)


def _slug(madde: str) -> str:
    return madde.replace("geçici", "gecici").replace(" ", "-").replace("/", "-")


def _article_order(madde: str) -> tuple:
    m = re.search(r"\d+", madde)
    return (0 if madde[0].isdigit() else 1, int(m.group()) if m else 0, madde)


def _ordered_refs(text: str) -> list[str]:
    body = FOOTDEF.sub("", BLOCK.sub("", text))
    seen: dict[str, None] = {}
    for m in REF.finditer(body):
        seen.setdefault(m.group(1), None)
    return list(seen)


def _diff(old: str, new: str, name: str) -> str:
    wrap = lambda s: re.sub(r"\s+", " ", s).replace(". ", ".\n").splitlines(keepends=True)
    return "".join(difflib.unified_diff(wrap(old), wrap(new), f"kayıtlı/{name}", f"güncel/{name}", n=1))


def _squash(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def _d(d: dt.date) -> str:
    return d.strftime("%d.%m.%Y")


def _tl(x: float) -> str:
    s = f"{x:,.2f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")
