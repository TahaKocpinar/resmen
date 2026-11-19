from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

from . import hesap
from .kaynak import Repo


def _date(s: str) -> dt.date:
    try:
        return dt.date.fromisoformat(s)
    except ValueError:
        d, m, y = s.replace("/", ".").split(".")
        return dt.date(int(y), int(m), int(d))


def _root(args) -> Path:
    if args.kok:
        return Path(args.kok)
    here = Path.cwd()
    for p in (here, *here.parents):
        if (p / "kaynaklar" / "pinler.toml").exists():
            return p
    return Path(__file__).resolve().parent.parent


def _print_result(repo: Repo, s: hesap.Sonuc) -> None:
    width = max(len(k) for k, _ in s.satirlar)
    print(s.baslik)
    for k, v in s.satirlar:
        print(f"  {k:<{width}}  {v}")
    for n in s.notlar:
        print(f"  * {n}")
    print("Dayanak:")
    seen = dict.fromkeys((repo.label(repo.pins[p]), repo.link(repo.pins[p])) for p in s.dayanak)
    for label, link in seen:
        print(f"  - {label}  {link}")


def cmd_kontrol(repo: Repo, args) -> int:
    probs = repo.check(_date(args.tarih) if args.tarih else None)
    for p in probs:
        print(p)
    errors = sum(p.level == "hata" for p in probs)
    quotes = sum(len(p.quotes) for p in repo.pins.values())
    print(f"{len(repo.pins)} pin, {quotes} alıntı, {len(repo.guides())} rehber: "
          f"{errors} hata, {len(probs) - errors} uyarı")
    return 1 if errors else 0


def cmd_guncelle(repo: Repo, args) -> int:
    report = repo.refresh(write=args.yaz)
    bad = [r for r in report if r["durum"] not in ("aynı", "yeni")]
    lines = []
    for r in report:
        extra = f"  ({', '.join(r['pinler'])})" if r.get("pinler") else ""
        lines.append(f"{r['durum']:>16}  {r['kaynak']}{extra}")
        if r.get("ayrinti"):
            lines.append(f"{'':>18}{r['ayrinti']}")
    print("\n".join(lines))
    if args.rapor:
        md = ["| Durum | Kaynak | Pinler |", "|---|---|---|"]
        md += [f"| {r['durum']} | {r['kaynak']} | {', '.join(r.get('pinler', []))} |" for r in bad]
        for r in bad:
            if r.get("diff"):
                md += ["", f"### {r['kaynak']}", "", "```diff", r["diff"].rstrip(), "```"]
        Path(args.rapor).write_text("\n".join(md) + "\n", encoding="utf-8")
    changed = [r for r in bad if r["durum"] != "erişilemedi"]
    return 1 if changed else 0


def cmd_dipnot(repo: Repo, args) -> int:
    for p in repo.write_blocks():
        print("güncellendi:", p.relative_to(repo.root))
    return 0


def cmd_json(repo: Repo, args) -> int:
    out = {
        "uretildi": dt.date.today().isoformat(),
        "pinler": [
            {"id": p.id, "kaynak": repo.label(p), "url": repo.link(p), "alinti": p.quotes}
            for p in repo.pins.values()
        ],
        "parametreler": {
            k: [{**r, "baslangic": r["baslangic"].isoformat(), "bitis": r["bitis"].isoformat()} for r in v]
            for k, v in repo.params.items()
        },
        "rehberler": [
            {"dosya": g.relative_to(repo.root).as_posix(), "metin": g.read_text(encoding="utf-8")}
            for g in repo.guides()
        ],
    }
    json.dump(out, sys.stdout, ensure_ascii=False, indent=1)
    print()
    return 0


def cmd_hesap(repo: Repo, args) -> int:
    try:
        if args.cmd == "kidem":
            s = hesap.kidem(repo, _date(args.giris), _date(args.cikis), args.ucret)
        elif args.cmd == "ihbar":
            s = hesap.ihbar(repo, _date(args.giris), _date(args.cikis), args.ucret)
        elif args.cmd == "izin":
            s = hesap.izin(repo, _date(args.giris), _date(args.cikis), args.kullanilan,
                           _date(args.dogum) if args.dogum else None, args.ucret)
        elif args.cmd == "issizlik":
            s = hesap.issizlik(repo, args.kazanc, args.gun, _date(args.tarih) if args.tarih else None)
        else:
            s = hesap.kira(repo, args.bedel, args.oran, args.yil)
    except (LookupError, ValueError) as e:
        print(f"resmen: {e}", file=sys.stderr)
        return 2
    _print_result(repo, s)
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="resmen", description="Kaynaklı rehber araçları.")
    ap.add_argument("--kok", help="depo kökü (varsayılan: bulunduğun klasör)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    k = sub.add_parser("kontrol", help="alıntıları, dipnotları ve parametreleri çevrimdışı denetle")
    k.add_argument("--tarih", help="'bugün' yerine kullanılacak tarih")
    g = sub.add_parser("guncelle", help="kaynakları canlı metinle karşılaştır")
    g.add_argument("--yaz", action="store_true", help="değişen maddelerin kopyasını kaydet")
    g.add_argument("--rapor", help="değişiklik raporunu Markdown olarak yaz")
    sub.add_parser("dipnot", help="rehberlerdeki dipnot ve tablo bloklarını yeniden üret")
    sub.add_parser("json", help="pinleri, parametreleri ve rehberleri JSON olarak yaz")

    for name in ("kidem", "ihbar"):
        p = sub.add_parser(name, help=f"{name} tazminatı")
        p.add_argument("--giris", required=True, help="işe giriş (2019-03-04 ya da 04.03.2019)")
        p.add_argument("--cikis", required=True, help="son çalışılan gün")
        p.add_argument("--ucret", required=True, type=float, help="aylık giydirilmiş brüt ücret")
    p = sub.add_parser("izin", help="yıllık izin hakkı ve kullanılmayan izin ücreti")
    p.add_argument("--giris", required=True)
    p.add_argument("--cikis", required=True)
    p.add_argument("--kullanilan", type=int, default=0, help="kullanılan toplam gün")
    p.add_argument("--dogum", help="doğum tarihi (18 altı / 50 üstü kuralı için)")
    p.add_argument("--ucret", type=float, help="aylık brüt ücret")
    p = sub.add_parser("issizlik", help="işsizlik ödeneği")
    p.add_argument("--kazanc", required=True, type=float, help="son 4 ayın aylık ortalama brüt kazancı")
    p.add_argument("--gun", required=True, type=int, help="son 3 yıldaki prim günü")
    p.add_argument("--tarih", help="ödeme dönemi (varsayılan: bugün)")
    p = sub.add_parser("kira", help="kira artışı üst sınırı")
    p.add_argument("--bedel", required=True, type=float)
    p.add_argument("--oran", required=True, type=float, help="TÜFE 12 aylık ortalama değişim, yüzde")
    p.add_argument("--yil", type=int, help="kira ilişkisinin süresi (yıl)")

    args = ap.parse_args(argv)
    repo = Repo.load(_root(args))
    handler = {"kontrol": cmd_kontrol, "guncelle": cmd_guncelle, "dipnot": cmd_dipnot, "json": cmd_json}
    return handler.get(args.cmd, cmd_hesap)(repo, args)
