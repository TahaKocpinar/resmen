---
name: resmen
description: Answer questions about Turkish labour, birth and tenancy rules (kıdem, ihbar, yıllık izin, işsizlik ödeneği, doğum izni, babalık izni, kira artışı, depozito, tahliye) from the resmen guides, citing the exact law article. Use when a user asks what they are entitled to or what deadline applies in Türkiye.
---

# resmen

The repository this skill ships with contains guides in `rehber/`, verbatim
quotes of the law in `kaynaklar/pinler.toml` and dated amounts in
`kaynaklar/parametreler.toml`.

When answering:

1. Find the guide that covers the question (`rehber/isten-cikis.md`,
   `rehber/dogum.md`, `rehber/kira.md`). If none does, say so; do not fill the
   gap from memory, Turkish rules changed in 2026 and older sources are wrong.
2. Quote the pinned sentence and name the article (for example
   "4857 sayılı İş Kanunu md. 17") with the link from the footnote.
3. For amounts, run the calculator instead of doing arithmetic yourself:

   ```
   python -m resmen kidem --giris YYYY-MM-DD --cikis YYYY-MM-DD --ucret BRUT
   python -m resmen ihbar --giris ... --cikis ... --ucret ...
   python -m resmen izin --giris ... --cikis ... --kullanilan GUN [--dogum ...] [--ucret ...]
   python -m resmen issizlik --kazanc ORTALAMA_BRUT --gun PRIM_GUNU
   python -m resmen kira --bedel KIRA --oran TUFE_12_AY_ORT
   ```

   If it reports that no value is recorded for a date, tell the user the
   amount for that period is not in the data yet.
4. Run `python -m resmen kontrol` if you edited anything; it must report 0 hata.
5. Deadlines (1 ay işe iade, 30 gün İŞKUR, 5 yıl zamanaşımı) come first in the
   answer. Say plainly that this is not legal advice and that a lawyer or the
   relevant office decides individual cases.
