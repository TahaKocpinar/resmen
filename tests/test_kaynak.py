import datetime as dt
import shutil
import tempfile
import textwrap
import unittest
from pathlib import Path

from resmen.kaynak import Repo, quote_in

ROOT = Path(__file__).resolve().parent.parent


def make_repo(pins: str, guide: str, params: str = "", article: str = "Madde 17 - Bildirim şartına uymayan taraf tazminat öder.") -> Path:
    d = Path(tempfile.mkdtemp())
    (d / "kaynaklar" / "metin" / "4857").mkdir(parents=True)
    (d / "rehber").mkdir()
    (d / "kaynaklar" / "kanunlar.toml").write_text('[4857]\nad = "İş Kanunu"\n', encoding="utf-8")
    (d / "kaynaklar" / "pinler.toml").write_text(textwrap.dedent(pins), encoding="utf-8")
    (d / "kaynaklar" / "parametreler.toml").write_text(textwrap.dedent(params), encoding="utf-8")
    (d / "kaynaklar" / "metin" / "4857" / "17.txt").write_text(article, encoding="utf-8")
    (d / "rehber" / "a.md").write_text(textwrap.dedent(guide), encoding="utf-8")
    return d


PIN = """
[[pin]]
id = "p17"
kanun = "4857"
madde = "17"
alinti = "Bildirim şartına uymayan taraf tazminat öder."
"""

GUIDE = """
# A

Bildirim süresine uymayan öder [^p17].

<!-- resmen:dipnotlar -->
<!-- /resmen -->
"""


class CheckTest(unittest.TestCase):
    def tearDown(self):
        for d in getattr(self, "dirs", []):
            shutil.rmtree(d, ignore_errors=True)

    def repo(self, *a, **kw) -> Repo:
        d = make_repo(*a, **kw)
        self.dirs = getattr(self, "dirs", []) + [d]
        repo = Repo.load(d)
        repo.write_blocks()
        return repo

    def errors(self, repo: Repo, **kw) -> list[str]:
        return [p.msg for p in repo.check(**kw) if p.level == "hata"]

    def test_clean_repo(self):
        repo = self.repo(PIN, GUIDE)
        self.assertEqual(repo.check(), [])
        text = (repo.root / "rehber" / "a.md").read_text(encoding="utf-8")
        self.assertIn("[^p17]: 4857 sayılı İş Kanunu, md. 17: “Bildirim şartına uymayan taraf tazminat öder.”", text)

    def test_quote_not_in_text(self):
        repo = self.repo(PIN.replace("tazminat öder", "ceza öder"), GUIDE)
        self.assertEqual(self.errors(repo), ["alıntı kayıtlı metinde geçmiyor"])

    def test_unknown_reference(self):
        repo = self.repo(PIN, GUIDE.replace("[^p17]", "[^p17] [^yok]"))
        self.assertIn("[^yok] pinler.toml'da tanımlı değil", self.errors(repo))

    def test_stale_footnotes(self):
        repo = self.repo(PIN, GUIDE)
        g = repo.root / "rehber" / "a.md"
        g.write_text(g.read_text(encoding="utf-8").replace("tazminat öder.”", "x”"), encoding="utf-8")
        self.assertEqual(self.errors(repo), ["dipnot/tablo blokları eski (resmen dipnot)"])

    def test_overlapping_periods_and_expiry(self):
        params = """
        [[tavan]]
        baslangic = 2026-01-01
        bitis = 2026-06-30
        tutar = 1.0
        kaynak = "p17"

        [[tavan]]
        baslangic = 2026-06-01
        bitis = 2026-12-31
        tutar = 2.0
        kaynak = "p17"
        """
        repo = self.repo(PIN, GUIDE, params)
        probs = repo.check(today=dt.date(2027, 1, 5))
        msgs = [p.msg for p in probs]
        self.assertIn("2026-01-01 ve 2026-06-01 dönemleri çakışıyor", msgs)
        self.assertIn("son değer 2026-12-31 tarihinde bitti, yenisi eklenmeli", msgs)

    def test_refresh_reports_changed_article_and_broken_quote(self):
        repo = self.repo(PIN, GUIDE)
        page = "<p>Madde 17 - Bildirim şartına uymayan taraf iki kat tazminat öder.</p><p>Madde 18 - x</p>"
        report = repo.refresh(fetch_law=lambda *a: page)
        self.assertEqual(report[0]["durum"], "alıntı bozuldu")
        self.assertEqual(report[0]["pinler"], ["p17"])
        self.assertIn("+Madde 17 - Bildirim şartına uymayan taraf iki kat tazminat öder.", report[0]["diff"])

    def test_refresh_same_text_different_layout(self):
        repo = self.repo(PIN, GUIDE)
        page = "<p>Madde\n17 -   Bildirim şartına\nuymayan taraf tazminat öder.[3]</p>"
        self.assertEqual(repo.refresh(fetch_law=lambda *a: page)[0]["durum"], "aynı")

    def test_refresh_survives_dead_source(self):
        repo = self.repo(PIN, GUIDE)

        def boom(*a):
            raise RuntimeError("bağlantı koptu")

        report = repo.refresh(fetch_law=boom)
        self.assertEqual(report[0]["durum"], "erişilemedi")


class RealDataTest(unittest.TestCase):
    """The shipped guides, pins and snapshots must be consistent."""

    @classmethod
    def setUpClass(cls):
        cls.repo = Repo.load(ROOT)

    def test_no_errors(self):
        errors = [str(p) for p in self.repo.check(today=dt.date(2026, 11, 19)) if p.level == "hata"]
        self.assertEqual(errors, [])

    def test_pre_2026_maternity_wording_would_fail(self):
        # The wording most guides still quote; Law 7578 replaced it in April 2026.
        old = "doğumdan önce sekiz ve doğumdan sonra sekiz hafta olmak üzere toplam onaltı haftalık süre"
        md74 = self.repo.snapshot(self.repo.pins["4857-74-dogum"])
        self.assertFalse(quote_in(old, md74))
        self.assertTrue(quote_in(self.repo.pins["4857-74-dogum"].alinti, md74))

    def test_every_guide_has_sources(self):
        for g in self.repo.guides():
            self.assertIn("<!-- resmen:dipnotlar -->", g.read_text(encoding="utf-8"), g.name)


if __name__ == "__main__":
    unittest.main()
