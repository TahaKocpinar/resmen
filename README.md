# resmen

**İşten çıkarılma, doğum ve kira için Türkçe, kaynaklı bir rehber. Her hukuki cümle kanunun resmî metninden birebir bir alıntıya bağlı; alıntılar her hafta mevzuat.gov.tr'ye karşı yeniden denetleniyor.**

[![test](https://github.com/TahaKocpinar/resmen/actions/workflows/test.yml/badge.svg)](https://github.com/TahaKocpinar/resmen/actions/workflows/test.yml)
![pin](https://img.shields.io/badge/alıntı-66-2b6cb0)
![kaynak](https://img.shields.io/badge/kaynak-7%20kanun%20·%204%20resmî%20belge-2b6cb0)
![lisans](https://img.shields.io/badge/lisans-MIT-555)

[English](#english)

Mevzuat değişiyor, rehberler değişmiyor. 22 Nisan 2026 tarihli 7578 sayılı Kanun doğum sonrası izni 8 haftadan 16 haftaya, babalık iznini 5 günden 10 güne çıkardı; bundan önce yazılmış her rehber artık yanlış. Kıdem tavanı yılda iki kez değişiyor ve ikincil kaynaklar birbirini tutmuyor: arama sonuçlarında çıkan bir hukuk bürosu yazısı 2025'in ilk yarısı için 47.486,51 TL diyor, ÇSGB'nin kendi tablosu 46.655,43 TL.

resmen bu yüzden cümleyi değil kaynağı saklıyor. Rehberdeki her hukuki cümlenin sonunda bir dipnot var; dipnot, kanun maddesinden kopyalanmış bir alıntıya ve maddenin kendisine gidiyor. Madde değişip alıntı metinden düşerse CI kırmızıya dönüyor ve haftalık iş akışı farkı gösteren bir issue açıyor.

> Hukuki danışmanlık değildir. Kendi durumun için avukata, İŞKUR'a ya da ilgili kuruma danış. Yanlış bir şey görürsen kaynağıyla birlikte [issue aç](https://github.com/TahaKocpinar/resmen/issues/new/choose).

## Hangi soru, hangi sayfa

| Soru | Sayfa |
|---|---|
| İşten çıkarıldım ya da ayrılıyorum. Hangi süreler işliyor, kıdem, ihbar, izin ücreti ve işsizlik ödeneği ne kadar? | [rehber/isten-cikis.md](rehber/isten-cikis.md) |
| Bebeğimiz oldu. Anneye kaç hafta, babaya kaç gün izin var, nüfusa ne zamana kadar bildirilir? | [rehber/dogum.md](rehber/dogum.md) |
| Ev sahibi ne kadar zam yapabilir, depozito ne olur, beni hangi durumda çıkarabilir? | [rehber/kira.md](rehber/kira.md) |

İşten çıkış sayfası, kaçırılınca geri gelmeyen sürelerle (işe iade için 1 ay, İŞKUR için 30 gün, alacaklar için 5 yıl) başlıyor. Her sayfanın sonunda kapsamadığı konuların listesi var.

## Hesap makineleri

Python 3.11 ya da üstü yeterli, başka bağımlılık yok.

```console
$ git clone https://github.com/TahaKocpinar/resmen && cd resmen
$ python -m resmen kidem --giris 04.03.2019 --cikis 13.11.2026 --ucret 52000
Kıdem tazminatı
  Hizmet süresi            7 yıl 8 ay 10 gün
  Fesih tarihindeki tavan  73.729,87 TL
  Hesaba esas ücret        52.000,00 TL
  Brüt                     400.091,32 TL
  Damga vergisi            −3.036,69 TL
  Net                      397.054,63 TL
  * Ücret giydirilmiş brüt ücrettir: düzenli ödenen yol, yemek, ikramiye gibi ödemeler dahil.
  * Kıdem tazminatından gelir vergisi kesilmez, yalnız damga vergisi kesilir.
Dayanak:
  - 1475 sayılı (eski) İş Kanunu, md. 14  https://www.mevzuat.gov.tr/mevzuat?MevzuatNo=1475&MevzuatTur=1&MevzuatTertip=5
  - ÇSGB, Kıdem Tazminatı (01.07.2026 itibarıyla tavan hesabı)  https://www.csgb.gov.tr/Media/5vuhphpb/...
  - TÜRMOB, 1 Temmuz 2026'dan itibaren vergiden istisna kıdem tazminatı tutarı  https://www.turmob.org.tr/...
```

| Komut | Ne hesaplar |
|---|---|
| `kidem --giris --cikis --ucret` | Kıdem tazminatı; tavanı fesih tarihine göre seçer (2021'den bugüne 12 dönem) |
| `ihbar --giris --cikis --ucret` | Bildirim süresi (2/4/6/8 hafta) ve brüt ihbar tazminatı |
| `izin --giris --cikis --kullanilan [--dogum] [--ucret]` | Yıl yıl hak edilen izin, 18 altı / 50 üstü kuralı, kullanılmayan izin ücreti |
| `issizlik --kazanc --gun [--tarih]` | İşsizlik ödeneği: %40, asgari ücretin %80'i tavanı, 180/240/300 gün |
| `kira --bedel --oran [--yil]` | TÜFE 12 aylık ortalamasına göre en yüksek yeni kira |

Bir tarih için kayıtlı tutar yoksa (ör. 2027 asgari ücreti henüz eklenmediyse) hesap makinesi tahmin yürütmez, hata verir.

## Nasıl çalışıyor

Bir pin, bir alıntı ve yerini tarif ediyor:

```toml
# kaynaklar/pinler.toml
[[pin]]
id = "4857-ek2-babalik"
kanun = "4857"
madde = "ek 2"
alinti = "eşinin doğum yapması hâlinde ise on gün ücretli izin verilir."
```

Rehberde cümle `[^4857-ek2-babalik]` ile bitiyor. `python -m resmen dipnot` sayfanın sonundaki kaynak listesini pinlerden yeniden üretiyor; elle yazılmış dipnot yok.

| Komut | Ağ | Ne yapar |
|---|---|---|
| `python -m resmen kontrol` | yok | Her alıntı `kaynaklar/metin/` altındaki madde kopyasında geçiyor mu, her `[^id]` tanımlı mı, dipnotlar güncel mi, tutar dönemleri çakışıyor ya da bitmiş mi. Her push'ta CI'da çalışır. |
| `python -m resmen guncelle [--yaz]` | var | 23 maddeyi ve değişiklik dipnotlarını mevzuat.gov.tr'den, 4 belgeyi ÇSGB ve TÜRMOB'dan yeniden indirir, kopyayla karşılaştırır, değişen maddenin farkını gösterir. Pazartesi sabahları [mevzuat.yml](.github/workflows/mevzuat.yml) çalıştırır ve fark varsa issue açar. |
| `python -m resmen json` | yok | Pinleri, tutarları ve rehberleri tek JSON olarak yazar. |

Eşleşme boşluk ve dipnot işaretlerine (`[24]`) duyarsız, harf ve noktalama duyarlı. Kanun metinlerinin ilgili maddeleri depoda duruyor (kanun metinleri FSEK md. 31 gereği serbest); diğer belgelerden yalnız alıntının çevresi saklanıyor.

Bugün 7 kanundan 23 madde, 4 resmî belge, 53 pin ve 66 alıntı var; 37 test. Canlı kontrolün tamamı 3 dakika kadar sürüyor; çoğu, mevzuat.gov.tr'nin düşürdüğü bağlantıların yeniden denenmesi.

## Ajanlar için

[skills/resmen/SKILL.md](skills/resmen/SKILL.md), Claude Code, Codex ve benzeri araçlara cevabı bu rehberlerden ve hesap makinelerinden vermesini, maddeyi alıntılamasını ve rehberde olmayan konuyu hafızadan doldurmamasını söylüyor. Ajanlar 2026 değişikliklerinden önceki bilgiyle eğitildiği için ikincisi önemli.

## Bilinen sınırlar

- Kapsam şimdilik üç olay ve 4857'ye tabi işçiler. Memurlar, basın ve deniz iş kanunları yok.
- Yargıtay içtihadı yok. Kanuna değil uygulamaya dayanan birkaç cümle "Uygulamada" diye başlıyor ve pinsiz.
- mevzuat.gov.tr bazı kanunları (488 sayılı Damga Vergisi Kanunu gibi) metin olarak vermiyor; binde 7,59 damga oranı bu yüzden TÜRMOB sirkülerine bağlı.
- İhbar tazminatı ve izin ücretinden kesilecek gelir vergisi hesaplanmıyor; kümülatif matraha bağlı.
- Alıntı kontrolü metin eşleşmesi. Bir maddenin anlamı, atıf yaptığı başka bir maddedeki değişiklikle değişirse yakalanmaz.
- Tutarlar elle ekleniyor. Dönem bitince `kontrol` uyarıyor, ama yenisini birinin eklemesi gerekiyor.
- GitHub, 60 gün hareketsiz kalan depolarda zamanlanmış iş akışlarını durduruyor. Fork'ta haftalık kontrol için Actions'ı açman gerekiyor.

## Katkı

Kural tek: resmî metinde birebir karşılığı olmayan hukuki cümle eklenmiyor. Adımlar [CONTRIBUTING.md](CONTRIBUTING.md)'de, beş komut. En çok ihtiyaç duyulan sayfalar: trafik kazası, miras ve veraset, emeklilik, ayıplı mal ve tüketici hakem heyeti.

## English

resmen is a sourced guide to Turkish rules for losing a job, having a child and renting. Every legal sentence carries a footnote that points to a verbatim quote from the official text of the law; `python -m resmen kontrol` checks the quotes against stored copies of the articles on every push, and a weekly workflow re-reads mevzuat.gov.tr and opens an issue with a diff when an article changes. This is the kind of change it exists for: Law 7578 (April 2026) raised post-birth maternity leave from 8 to 16 weeks and paternity leave from 5 to 10 days, so any guide written before that is now wrong. Stdlib-only Python 3.11+ calculators for severance (kıdem), notice pay (ihbar), annual leave, unemployment benefit and rent increases print the articles they rely on. The content is in Turkish because the law is.

## Lisans

MIT. Kanun metinleri kamuya açıktır.
