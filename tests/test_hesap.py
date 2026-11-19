import datetime as dt
import io
import unittest
from contextlib import redirect_stderr, redirect_stdout
from decimal import Decimal
from pathlib import Path

from resmen import hesap
from resmen.cli import main
from resmen.kaynak import Repo

ROOT = Path(__file__).resolve().parent.parent
D = dt.date


class ServiceTest(unittest.TestCase):
    def test_exact_year_counts_last_day(self):
        self.assertEqual(hesap.hizmet_suresi(D(2020, 1, 1), D(2020, 12, 31)), (1, 0, 0))

    def test_borrow_days(self):
        self.assertEqual(hesap.hizmet_suresi(D(2019, 3, 4), D(2026, 11, 13)), (7, 8, 10))
        self.assertEqual(hesap.hizmet_suresi(D(2024, 1, 15), D(2024, 3, 10)), (0, 1, 25))

    def test_single_day(self):
        self.assertEqual(hesap.hizmet_suresi(D(2026, 5, 5), D(2026, 5, 5)), (0, 0, 1))

    def test_reversed(self):
        with self.assertRaises(ValueError):
            hesap.hizmet_suresi(D(2026, 5, 5), D(2026, 5, 4))


class RulesTest(unittest.TestCase):
    def test_notice_weeks_at_boundaries(self):
        start = D(2020, 1, 1)
        cases = [(D(2020, 6, 29), 2), (D(2020, 6, 30), 4), (D(2021, 6, 29), 4), (D(2021, 6, 30), 6),
                 (D(2022, 12, 30), 6), (D(2022, 12, 31), 8)]
        for end, weeks in cases:
            self.assertEqual(hesap.ihbar_hafta(start, end), weeks, end)

    def test_leave_days(self):
        self.assertEqual([hesap.izin_hakki(y, 30) for y in (1, 5, 6, 14, 15)], [14, 14, 20, 20, 26])
        self.assertEqual(hesap.izin_hakki(1, 18), 20)
        self.assertEqual(hesap.izin_hakki(2, 50), 20)
        self.assertEqual(hesap.izin_hakki(16, 55), 26)

    def test_unemployment_duration(self):
        self.assertEqual([hesap.issizlik_suresi(g) for g in (599, 600, 899, 900, 1079, 1080)],
                         [0, 180, 180, 240, 240, 300])


class CalculatorTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo = Repo.load(ROOT)

    def test_severance_below_ceiling(self):
        s = hesap.kidem(self.repo, D(2019, 3, 4), D(2026, 11, 13), 52000)
        self.assertEqual(dict(s.satirlar)["Brüt"], "400.091,32 TL")
        self.assertEqual(s.tutar, Decimal("397054.63"))

    def test_severance_ceiling_follows_termination_date(self):
        h1 = hesap.kidem(self.repo, D(2020, 1, 1), D(2026, 6, 30), 200000)
        h2 = hesap.kidem(self.repo, D(2020, 1, 1), D(2026, 7, 1), 200000)
        self.assertIn("64.948,77", dict(h1.satirlar)["Hesaba esas ücret"])
        self.assertIn("73.729,87", dict(h2.satirlar)["Hesaba esas ücret"])

    def test_severance_needs_one_year(self):
        s = hesap.kidem(self.repo, D(2026, 1, 1), D(2026, 12, 30), 50000)
        self.assertEqual(s.tutar, 0)

    def test_severance_outside_known_periods(self):
        with self.assertRaises(LookupError):
            hesap.kidem(self.repo, D(2015, 1, 1), D(2020, 12, 31), 50000)

    def test_notice_pay(self):
        s = hesap.ihbar(self.repo, D(2019, 3, 4), D(2026, 11, 13), 52000)
        self.assertEqual(s.tutar, Decimal("97066.67"))

    def test_unused_leave_with_age_rule(self):
        s = hesap.izin(self.repo, D(2019, 3, 4), D(2026, 11, 13), 70, D(1988, 6, 10), 52000)
        self.assertEqual(dict(s.satirlar)["Hak edilen toplam izin"], "110 gün")
        self.assertEqual(s.tutar, Decimal("69333.33"))
        young = hesap.izin(self.repo, D(2020, 1, 1), D(2023, 1, 1), 0, D(2003, 6, 1))
        self.assertEqual(dict(young.satirlar)["Hak edilen toplam izin"], "54 gün")  # 20 + 20 + 14

    def test_unemployment_cap(self):
        s = hesap.issizlik(self.repo, 100000, 1080, D(2026, 12, 1))
        self.assertEqual(dict(s.satirlar)["Aylık brüt ödenek"], "26.424,00 TL")
        s = hesap.issizlik(self.repo, 48000, 1080, D(2026, 12, 1))
        self.assertEqual(s.tutar, Decimal("19054.27"))

    def test_unemployment_not_enough_days(self):
        self.assertEqual(hesap.issizlik(self.repo, 48000, 400, D(2026, 12, 1)).tutar, 0)

    def test_rent(self):
        s = hesap.kira(self.repo, 20000, 35)
        self.assertEqual(s.tutar, Decimal("27000.00"))
        self.assertIn("%35", dict(s.satirlar)["TÜFE 12 aylık ortalama değişim"])
        self.assertIn("6098-344-bes-yil", hesap.kira(self.repo, 20000, 35, 6).dayanak)


class CliTest(unittest.TestCase):
    def run_cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = main(["--kok", str(ROOT), *argv])
        return code, out.getvalue(), err.getvalue()

    def test_kidem_prints_sources(self):
        code, out, _ = self.run_cli("kidem", "--giris", "04.03.2019", "--cikis", "2026-11-13", "--ucret", "52000")
        self.assertEqual(code, 0)
        self.assertIn("Net                      397.054,63 TL", out)
        self.assertIn("1475 sayılı (eski) İş Kanunu, md. 14", out)

    def test_bad_dates(self):
        code, _, err = self.run_cli("ihbar", "--giris", "2026-01-02", "--cikis", "2026-01-01", "--ucret", "1")
        self.assertEqual(code, 2)
        self.assertIn("çıkış tarihi", err)

    def test_kontrol(self):
        code, out, _ = self.run_cli("kontrol", "--tarih", "2026-11-19")
        self.assertEqual(code, 0)
        self.assertIn("0 hata", out)


if __name__ == "__main__":
    unittest.main()
