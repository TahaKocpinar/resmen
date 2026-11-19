import unittest

from resmen import mevzuat

PAGE = """<html><body><div>
<p>Süreli fesih</p>
<p>Madde<br>17 - Belirsiz süreli iş sözleşmelerinin feshinden önce durumun diğer
tarafa bildirilmesi gerekir.[12]</p>
<p>Geçici</p><p>Madde 1 - Diğer mevzuatta 1475 sayılı İş Kanununa yapılan atıflar bu Kanuna yapılmış sayılır.</p>
<p>MADDE 18/B- (Ek:28/3/2023-7445/37 md.) Arabulucuya başvurulmuş olması dava şartıdır.</p>
<p>Ek Madde 2 – İşçiye on gün ücretli izin verilir.</p>
<p>[1] 2/7/2018 tarihli ve 700 sayılı KHK ile değiştirilmiştir.</p>
<p>[2] 22/4/2026 tarihli ve 7578 sayılı Kanunla değiştirilmiştir.</p>
</div></body></html>"""


class SplitTest(unittest.TestCase):
    def setUp(self):
        self.arts = mevzuat.split_articles(mevzuat.to_text(PAGE))

    def test_keys(self):
        self.assertEqual(list(self.arts), ["17", "geçici 1", "18/B", "ek 2", "dipnotlar"])

    def test_article_body_stops_before_next_heading(self):
        self.assertIn("bildirilmesi gerekir", self.arts["17"])
        self.assertNotIn("1475", self.arts["17"])

    def test_footnotes_are_split_from_last_article(self):
        self.assertNotIn("700 sayılı", self.arts["ek 2"])
        self.assertIn("7578 sayılı", self.arts["dipnotlar"])

    def test_uppercase_turkish_prefix(self):
        # "GEÇİCİ".lower() would give "geçi̇ci̇" with combining dots.
        self.assertEqual(mevzuat.article_key("GEÇİCİ ", "3"), "geçici 3")
        self.assertEqual(mevzuat.article_key("EK\n", "1"), "ek 1")
        self.assertEqual(mevzuat.article_key(None, "18/B"), "18/B")


class NormalizeTest(unittest.TestCase):
    def test_whitespace_footnotes_and_dashes(self):
        a = mevzuat.normalize("tarafa\nbildirilmesi   gerekir.[12] 7/15754 – x")
        self.assertEqual(a, "tarafa bildirilmesi gerekir. 7/15754 - x")

    def test_curly_quotes(self):
        self.assertEqual(mevzuat.normalize("“beş” ibaresi ‘on’"), '"beş" ibaresi \'on\'')


if __name__ == "__main__":
    unittest.main()
