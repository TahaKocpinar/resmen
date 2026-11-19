"""Calculators. Every result carries the pin ids it rests on."""
from __future__ import annotations

import calendar
import datetime as dt
from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal

from .kaynak import Repo, _tl

KURUS = Decimal("0.01")


@dataclass
class Sonuc:
    baslik: str
    satirlar: list[tuple[str, str]] = field(default_factory=list)
    dayanak: list[str] = field(default_factory=list)
    notlar: list[str] = field(default_factory=list)
    tutar: Decimal | None = None


def para(x: Decimal) -> str:
    return _tl(float(x)) + " TL"


def tl(x) -> Decimal:
    return Decimal(str(x)).quantize(KURUS, ROUND_HALF_UP)


def param(repo: Repo, name: str, on: dt.date) -> dict:
    for row in repo.params.get(name, []):
        if row["baslangic"] <= on <= row["bitis"]:
            return row
    known = sorted(repo.params.get(name, []), key=lambda r: r["baslangic"])
    span = f"{known[0]['baslangic']} – {known[-1]['bitis']}" if known else "hiç değer yok"
    raise LookupError(f"{name}: {on} için kayıtlı değer yok (kayıtlı aralık: {span})")


def hizmet_suresi(giris: dt.date, cikis: dt.date) -> tuple[int, int, int]:
    """Years, months, days of service, counting both the first and the last day."""
    if cikis < giris:
        raise ValueError("çıkış tarihi giriş tarihinden önce")
    end = cikis + dt.timedelta(days=1)
    y, m, d = end.year - giris.year, end.month - giris.month, end.day - giris.day
    if d < 0:
        prev = end.month - 1 or 12
        prev_year = end.year if end.month > 1 else end.year - 1
        d += calendar.monthrange(prev_year, prev)[1]
        m -= 1
    if m < 0:
        y, m = y - 1, m + 12
    return y, m, d


def sure_metni(y: int, m: int, d: int) -> str:
    return f"{y} yıl {m} ay {d} gün"


def kidem(repo: Repo, giris: dt.date, cikis: dt.date, ucret) -> Sonuc:
    y, m, d = hizmet_suresi(giris, cikis)
    ucret = tl(ucret)
    tavan_row = param(repo, "kidem_tavani", cikis)
    tavan = tl(tavan_row["tutar"])
    esas = min(ucret, tavan)
    s = Sonuc("Kıdem tazminatı", dayanak=["1475-14-otuz-gun", "1475-14-artan-sure", tavan_row["kaynak"]])
    s.satirlar.append(("Hizmet süresi", sure_metni(y, m, d)))
    s.satirlar.append(("Fesih tarihindeki tavan", para(tavan)))
    s.satirlar.append(("Hesaba esas ücret", para(esas) + (" (tavana indirildi)" if esas < ucret else "")))
    if y < 1:
        s.tutar = Decimal(0)
        s.satirlar.append(("Kıdem tazminatı", "hak yok: en az bir tam yıl gerekir"))
        return s
    brut = tl(esas * y + esas * m / 12 + esas * d / 365)
    damga = tl(brut * Decimal(str(param(repo, "damga_vergisi_orani", cikis)["tutar"])))
    s.tutar = brut - damga
    s.satirlar += [("Brüt", para(brut)), ("Damga vergisi", "−" + para(damga)), ("Net", para(s.tutar))]
    s.dayanak.append(param(repo, "damga_vergisi_orani", cikis)["kaynak"])
    s.notlar.append("Ücret giydirilmiş brüt ücrettir: düzenli ödenen yol, yemek, ikramiye gibi ödemeler dahil.")
    s.notlar.append("Kıdem tazminatından gelir vergisi kesilmez, yalnız damga vergisi kesilir.")
    return s


def ihbar_hafta(giris: dt.date, cikis: dt.date) -> int:
    y, m, d = hizmet_suresi(giris, cikis)
    months = y * 12 + m
    if months < 6:
        return 2
    if months < 18:
        return 4
    if months < 36:
        return 6
    return 8


def ihbar(repo: Repo, giris: dt.date, cikis: dt.date, ucret) -> Sonuc:
    hafta = ihbar_hafta(giris, cikis)
    ucret = tl(ucret)
    brut = tl(ucret / 30 * 7 * hafta)
    s = Sonuc("İhbar tazminatı (bildirim süresi ücreti)", dayanak=["4857-17-sureler", "4857-17-tazminat"])
    s.satirlar += [
        ("Hizmet süresi", sure_metni(*hizmet_suresi(giris, cikis))),
        ("Bildirim süresi", f"{hafta} hafta"),
        ("Brüt", para(brut)),
    ]
    s.tutar = brut
    s.notlar.append("İhbar tazminatından gelir vergisi ve damga vergisi kesilir; gelir vergisi yıl içindeki kümülatif matraha bağlı olduğu için burada hesaplanmaz.")
    s.notlar.append("Süre sınırlarında (tam 6 ay, 18 ay, 36 ay) bir üst dilim uygulanır.")
    return s


def izin_hakki(hizmet_yili: int, yas: int | None) -> int:
    gun = 14 if hizmet_yili <= 5 else 20 if hizmet_yili < 15 else 26
    if yas is not None and (yas <= 18 or yas >= 50):
        gun = max(gun, 20)
    return gun


def izin(repo: Repo, giris: dt.date, cikis: dt.date, kullanilan: int = 0,
         dogum: dt.date | None = None, ucret=None) -> Sonuc:
    tam_yil = hizmet_suresi(giris, cikis)[0]
    s = Sonuc("Yıllık ücretli izin", dayanak=["4857-53-sureler", "4857-53-yas"])
    toplam = 0
    for i in range(1, tam_yil + 1):
        yildonumu = _add_years(giris, i)
        yas = _age(dogum, yildonumu) if dogum else None
        toplam += izin_hakki(i, yas)
    kalan = max(toplam - kullanilan, 0)
    s.satirlar += [("Tamamlanan hizmet yılı", str(tam_yil)), ("Hak edilen toplam izin", f"{toplam} gün"),
                   ("Kullanılan", f"{kullanilan} gün"), ("Kullanılmayan", f"{kalan} gün")]
    if ucret is not None:
        s.tutar = tl(tl(ucret) / 30 * kalan)
        s.satirlar.append(("Kullanılmayan izin ücreti (brüt)", para(s.tutar)))
        s.dayanak.append("4857-59-ucret")
    if dogum is None:
        s.notlar.append("Doğum tarihi verilmedi: 18 yaş altı ve 50 yaş üstü için en az 20 gün kuralı uygulanmadı.")
    s.notlar.append("Yer altı işlerinde süreler dörder gün artar; sözleşme daha fazlasını verebilir.")
    return s


def issizlik_suresi(prim_gun: int) -> int:
    return 300 if prim_gun >= 1080 else 240 if prim_gun >= 900 else 180 if prim_gun >= 600 else 0


def issizlik(repo: Repo, kazanc, prim_gun: int, tarih: dt.date | None = None) -> Sonuc:
    tarih = tarih or dt.date.today()
    asgari_row = param(repo, "asgari_ucret_brut", tarih)
    asgari = tl(asgari_row["tutar"])
    kazanc = tl(kazanc)
    hesap = tl(kazanc * Decimal("0.40"))
    tavan = tl(asgari * Decimal("0.80"))
    aylik = min(hesap, tavan)
    gun = issizlik_suresi(prim_gun)
    s = Sonuc("İşsizlik ödeneği", dayanak=["4447-50-yuzde-kirk", "4447-50-tavan", "4447-50-sureler", asgari_row["kaynak"]])
    s.satirlar += [("Son 4 ayın aylık ortalama brüt kazancı", para(kazanc)),
                   ("%40", para(hesap)), ("Tavan (brüt asgari ücretin %80'i)", para(tavan))]
    if gun == 0:
        s.tutar = Decimal(0)
        s.satirlar.append(("Ödenek", "hak yok: son 3 yılda en az 600 gün prim gerekir"))
        return s
    damga_row = param(repo, "damga_vergisi_orani", tarih)
    damga = tl(aylik * Decimal(str(damga_row["tutar"])))
    s.tutar = aylik - damga
    s.dayanak += ["4447-50-damga", damga_row["kaynak"]]
    s.satirlar += [("Aylık brüt ödenek", para(aylik)), ("Damga vergisi", "−" + para(damga)),
                   ("Aylık net", para(s.tutar)), ("Süre", f"{gun} gün ({gun // 30} ay)"),
                   ("Toplam net", para(tl(s.tutar * gun / 30)))]
    s.notlar.append("Ayrıca son 120 gün kesintisiz prim ve 51. maddedeki çıkış nedenlerinden biri gerekir (istifa çoğu durumda hak vermez).")
    s.notlar.append("Başvuru, iş sözleşmesinin bittiği günü izleyen 30 gün içinde İŞKUR'a yapılmalı; geciken gün sayısı süreden düşülür.")
    return s


def kira(repo: Repo, bedel, oran, sozlesme_yili: int | None = None) -> Sonuc:
    bedel = tl(bedel)
    oran = Decimal(str(oran))
    yeni = tl(bedel * (1 + oran / 100))
    s = Sonuc("Kira artışı üst sınırı", dayanak=["6098-344-tufe"])
    s.satirlar += [("Mevcut kira", para(bedel)), ("TÜFE 12 aylık ortalama değişim", f"%{oran}"),
                   ("Yeni kira en fazla", para(yeni)), ("Artış en fazla", para(yeni - bedel))]
    s.tutar = yeni
    if sozlesme_yili is not None and sozlesme_yili >= 5:
        s.dayanak.append("6098-344-bes-yil")
        s.notlar.append("Kira ilişkisi 5 yılı geçtiyse ev sahibi, emsal kiralara göre belirleme için dava açabilir; sınır bu durumda bağlayıcı değildir.")
    s.notlar.append("Oran, kira yılının başladığı aydan önceki ay için TÜİK'in açıkladığı on iki aylık ortalama TÜFE değişimidir.")
    return s


def _add_years(d: dt.date, n: int) -> dt.date:
    try:
        return d.replace(year=d.year + n)
    except ValueError:  # 29 February
        return d.replace(year=d.year + n, day=28)


def _age(born: dt.date, on: dt.date) -> int:
    return on.year - born.year - ((on.month, on.day) < (born.month, born.day))
