# Katkı

Bu depoda tek kural var: **hukuki bir cümle, resmî metinden birebir bir alıntıya bağlı değilse eklenmez.**

## Bir cümle eklemek

1. Kanunu mevzuat.gov.tr'de aç, cümlenin dayandığı ifadeyi olduğu gibi kopyala.
2. `kaynaklar/pinler.toml` dosyasına bir pin ekle:

   ```toml
   [[pin]]
   id = "4857-53-yas"          # kanun-madde-kısa-ad
   kanun = "4857"
   madde = "53"                # "ek 2", "geçici 1", "18/B" ve "dipnotlar" da olur
   alinti = "Ancak onsekiz ve daha küçük yaştaki işçilerle ..."
   ```

   Kanun `kaynaklar/kanunlar.toml`'da yoksa oraya da ekle.
3. Rehberde cümlenin sonuna `[^4857-53-yas]` yaz.
4. Çalıştır:

   ```console
   python -m resmen guncelle --yaz   # yeni maddenin metnini kaynaklar/metin/ altına indirir
   python -m resmen dipnot           # rehberlerin sonundaki kaynak listesini yeniden üretir
   python -m resmen kontrol          # 0 hata olmalı
   python -m unittest
   ```

mevzuat.gov.tr sık sık bağlantı düşürüyor; `guncelle` beş kez dener, yine olmazsa birkaç dakika sonra tekrar çalıştır.

## Tutar eklemek

Asgari ücret, kıdem tavanı gibi dönemle değişen tutarlar `kaynaklar/parametreler.toml`'da durur. Her satırın dönemi ve bir pini olmalı; pin, tutarın yazdığı resmî belgeye (`url`) bağlanır. Dönemler çakışırsa ya da son dönem geçmişte kaldıysa `kontrol` söyler.

## Yazım

Kısa cümle, "sen" diliyle. Önce süreler ve para, sonra ayrıntı. Yargıtay uygulamasına dayanan bir şey yazmak zorundaysan "Uygulamada" diye başla ve kanun hükmüymüş gibi yazma. Kapsam dışında kalanları sayfanın sonundaki listeye ekle.

## Kod

Python 3.11+, yalnız standart kütüphane. Testler `python -m unittest`.
