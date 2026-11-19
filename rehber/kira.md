# Kiracıyım: zam, depozito, tahliye

Konut ve çatılı işyeri kiraları için (6098 sayılı Türk Borçlar Kanunu).

## Zam

Yeni kira yılındaki artış, bir önceki kira yılının TÜFE on iki aylık ortalama değişimini geçemez [^6098-344-tufe]. Sözleşmede daha yüksek bir oran yazsa da bu sınır uygulanır. Konut kiralarındaki %25 sınırı yalnız Haziran 2022 ile 1 Temmuz 2024 arasında yenilenen dönemler içindi [^6098-g1-yuzde-25] [^6098-g2-yuzde-25]; o tarihten sonra yenilenen dönemlerde sınır yalnız TÜFE ortalaması.

Oranı TÜİK'in aylık TÜFE bülteninden al ("12 aylık ortalamalara göre değişim").

```console
$ python -m resmen kira --bedel 20000 --oran 35
  Yeni kira en fazla              27.000,00 TL
  Artış en fazla                  7.000,00 TL
```

Kira ilişkisi 5 yılı doldurduysa ev sahibi, emsal kiraları da hesaba katan bir belirleme için dava açabilir; o zaman yeni kirayı hâkim belirler [^6098-344-bes-yil].

## Depozito

- En fazla **3 aylık kira** [^6098-342-guvence].
- Para depozito, ev sahibinin onayı olmadan çekilemeyecek bir vadeli hesaba yatırılır [^6098-342-banka].
- Sözleşme bittikten sonra 3 ay içinde ev sahibi bankaya dava ya da takip başlattığını yazılı bildirmezse banka, senin isteğinle parayı sana geri verir [^6098-342-uc-ay].

## Ev sahibi seni ne zaman çıkarabilir

Sözleşme süresinin bitmesi tek başına sebep değil. Sen en az 15 gün önce bildirmezsen sözleşme aynı koşullarla bir yıl uzar ve ev sahibi süre bitti diye sözleşmeyi sona erdiremez [^6098-347-uzama]. On yıllık uzama süresi dolunca ev sahibi, her uzama yılının bitiminden en az 3 ay önce bildirerek sebep göstermeden sözleşmeyi bitirebilir [^6098-347-on-yil].

Bunun dışında başlıca yollar:

| Sebep | Not | Dayanak |
|---|---|---|
| Ev sahibinin, eşinin, çocuklarının, anne-babasının ya da bakmakla yükümlü olduğu kişilerin konut ihtiyacı | Dava ile, süre sonundan itibaren 1 ay içinde | [^6098-350-ihtiyac] |
| Yazılı tahliye taahhüdü verdiysen | Taahhüt tarihinden itibaren 1 ay içinde icra ya da dava | [^6098-352-taahhut] |
| Bir kira yılında kirayı ödemediğin için **iki haklı yazılı ihtar** aldıysan | Kira yılının bitiminden itibaren 1 ay içinde dava | [^6098-352-iki-ihtar] |
| Aynı ilçede oturmaya elverişli kendi evin varsa ve ev sahibi bunu sözleşme sırasında bilmiyorsa | Dava ile | [^6098-352-konut] |

## Anlaşmazlıkta önce arabulucu

Kira ilişkisinden doğan uyuşmazlıklarda dava açmadan önce arabulucuya başvurmak zorunlu [^6325-18B-kira]. İstisna: ilamsız icra yoluyla tahliye takibi.

## Bu sayfada olmayanlar

- İlamsız icra yoluyla tahliye ve kira alacağı takibi (2004 sayılı İcra ve İflas Kanunu).
- Yeni malikin ihtiyacı (TBK 351), aidat ve ortak gider uyuşmazlıkları (634 sayılı Kat Mülkiyeti Kanunu).

## Kaynaklar

<!-- resmen:dipnotlar -->
[^6098-344-tufe]: 6098 sayılı Türk Borçlar Kanunu, md. 344: “Tarafların yenilenen kira dönemlerinde uygulanacak kira bedeline ilişkin anlaşmaları, bir önceki kira yılında tüketici fiyat endeksindeki oniki aylık ortalamalara göre değişim oranını geçmemek koşuluyla geçerlidir.” ([kaynak](https://www.mevzuat.gov.tr/mevzuat?MevzuatNo=6098&MevzuatTur=1&MevzuatTertip=5))
[^6098-g1-yuzde-25]: 6098 sayılı Türk Borçlar Kanunu, geçici md. 1: “Konut kiraları bakımından bu maddenin yürürlüğe girdiği tarih ilâ 1/7/2023 (bu tarih dâhil) tarihleri arasında yenilenen kira dönemlerinde uygulanacak kira bedeline ilişkin anlaşmalar, bir önceki kira yılına ait kira bedelinin yüzde yirmi beşini geçmemek koşuluyla geçerlidir.” ([kaynak](https://www.mevzuat.gov.tr/mevzuat?MevzuatNo=6098&MevzuatTur=1&MevzuatTertip=5))
[^6098-g2-yuzde-25]: 6098 sayılı Türk Borçlar Kanunu, geçici md. 2: “Konut kiraları bakımından 2/7/2023 ilâ 1/7/2024 (bu tarihler dâhil) tarihleri arasında yenilenen kira dönemlerinde uygulanacak kira bedeline ilişkin anlaşmalar, bir önceki kira yılına ait kira bedelinin yüzde yirmi beşini geçmemek koşuluyla geçerlidir.” ([kaynak](https://www.mevzuat.gov.tr/mevzuat?MevzuatNo=6098&MevzuatTur=1&MevzuatTertip=5))
[^6098-344-bes-yil]: 6098 sayılı Türk Borçlar Kanunu, md. 344: “beş yıldan uzun süreli veya beş yıldan sonra yenilenen kira sözleşmelerinde ve bundan sonraki her beş yılın sonunda, yeni kira yılında uygulanacak kira bedeli, hâkim tarafından tüketici fiyat endeksindeki oniki aylık ortalamalara göre değişim oranı, kiralananın durumu ve emsal kira bedelleri göz önünde tutularak hakkaniyete uygun biçimde belirlenir.” ([kaynak](https://www.mevzuat.gov.tr/mevzuat?MevzuatNo=6098&MevzuatTur=1&MevzuatTertip=5))
[^6098-342-guvence]: 6098 sayılı Türk Borçlar Kanunu, md. 342: “Konut ve çatılı işyeri kiralarında sözleşmeyle kiracıya güvence verme borcu getirilmişse, bu güvence üç aylık kira bedelini aşamaz.” ([kaynak](https://www.mevzuat.gov.tr/mevzuat?MevzuatNo=6098&MevzuatTur=1&MevzuatTertip=5))
[^6098-342-banka]: 6098 sayılı Türk Borçlar Kanunu, md. 342: “kiracı, kiraya verenin onayı olmaksızın çekilmemek üzere, parayı vadeli bir tasarruf hesabına yatırır” ([kaynak](https://www.mevzuat.gov.tr/mevzuat?MevzuatNo=6098&MevzuatTur=1&MevzuatTertip=5))
[^6098-342-uc-ay]: 6098 sayılı Türk Borçlar Kanunu, md. 342: “Kiraya veren, kira sözleşmesinin sona ermesini izleyen üç ay içinde kiracıya karşı kira sözleşmesiyle ilgili bir dava açtığını veya icra ya da iflas yoluyla takibe giriştiğini bankaya yazılı olarak bildirmemişse banka, kiracının istemi üzerine güvenceyi geri vermekle yükümlüdür.” ([kaynak](https://www.mevzuat.gov.tr/mevzuat?MevzuatNo=6098&MevzuatTur=1&MevzuatTertip=5))
[^6098-347-uzama]: 6098 sayılı Türk Borçlar Kanunu, md. 347: “kiracı, belirli süreli sözleşmelerin süresinin bitiminden en az onbeş gün önce bildirimde bulunmadıkça, sözleşme aynı koşullarla bir yıl için uzatılmış sayılır. Kiraya veren, sözleşme süresinin bitimine dayanarak sözleşmeyi sona erdiremez.” ([kaynak](https://www.mevzuat.gov.tr/mevzuat?MevzuatNo=6098&MevzuatTur=1&MevzuatTertip=5))
[^6098-347-on-yil]: 6098 sayılı Türk Borçlar Kanunu, md. 347: “on yıllık uzama süresi sonunda kiraya veren, bu süreyi izleyen her uzama yılının bitiminden en az üç ay önce bildirimde bulunmak koşuluyla, herhangi bir sebep göstermeksizin sözleşmeye son verebilir.” ([kaynak](https://www.mevzuat.gov.tr/mevzuat?MevzuatNo=6098&MevzuatTur=1&MevzuatTertip=5))
[^6098-350-ihtiyac]: 6098 sayılı Türk Borçlar Kanunu, md. 350: “Kiralananı kendisi, eşi, altsoyu, üstsoyu veya kanun gereği bakmakla yükümlü olduğu diğer kişiler için konut ya da işyeri gereksinimi sebebiyle kullanma zorunluluğu varsa … belirli süreli sözleşmelerde sürenin sonunda, belirsiz süreli sözleşmelerde kiraya ilişkin genel hükümlere göre fesih dönemine ve fesih bildirimi için öngörülen sürelere uyularak belirlenecek tarihten başlayarak bir ay içinde açacağı dava ile sona erdirebilir.” ([kaynak](https://www.mevzuat.gov.tr/mevzuat?MevzuatNo=6098&MevzuatTur=1&MevzuatTertip=5))
[^6098-352-taahhut]: 6098 sayılı Türk Borçlar Kanunu, md. 352: “kiralananı belli bir tarihte boşaltmayı yazılı olarak üstlendiği hâlde boşaltmamışsa kiraya veren, kira sözleşmesini bu tarihten başlayarak bir ay içinde icraya başvurmak veya dava açmak suretiyle sona erdirebilir.” ([kaynak](https://www.mevzuat.gov.tr/mevzuat?MevzuatNo=6098&MevzuatTur=1&MevzuatTertip=5))
[^6098-352-iki-ihtar]: 6098 sayılı Türk Borçlar Kanunu, md. 352: “kira bedelini ödemediği için kendisine yazılı olarak iki haklı ihtarda bulunulmasına sebep olmuşsa” ([kaynak](https://www.mevzuat.gov.tr/mevzuat?MevzuatNo=6098&MevzuatTur=1&MevzuatTertip=5))
[^6098-352-konut]: 6098 sayılı Türk Borçlar Kanunu, md. 352: “Kiracının veya birlikte yaşadığı eşinin aynı ilçe veya belde belediye sınırları içinde oturmaya elverişli bir konutu bulunması durumunda kiraya veren, kira sözleşmesinin kurulması sırasında bunu bilmiyorsa” ([kaynak](https://www.mevzuat.gov.tr/mevzuat?MevzuatNo=6098&MevzuatTur=1&MevzuatTertip=5))
[^6325-18B-kira]: 6325 sayılı Hukuk Uyuşmazlıklarında Arabuluculuk Kanunu, md. 18/B: “Aşağıdaki uyuşmazlıklarda, dava açılmadan önce arabulucuya başvurulmuş olması dava şartıdır: a) Kiralanan taşınmazların 2004 sayılı Kanuna göre ilamsız icra yoluyla tahliyesine ilişkin hükümler hariç olmak üzere, kira ilişkisinden kaynaklanan uyuşmazlıklar.” ([kaynak](https://www.mevzuat.gov.tr/mevzuat?MevzuatNo=6325&MevzuatTur=1&MevzuatTertip=5))
<!-- /resmen -->
