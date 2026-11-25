# Gaz Tüp Takip – Depo Sorgu Paneli

## Hangi problemi çözüyor, kimin için?

Endüstriyel gaz (oksijen, argon, azot, karışım, asetilen…) dolumu ve dağıtımı yapan bir firmanın deposunda
binlerce barkodlu tüp dolaşır; tüplerin bir kısmı dolu, bir kısmı boş, önemli bir kısmı da müşterilerdedir.
**Depo sorumlusu** bir tüpün şu an nerede olduğunu, hangi müşteride kaç gündür beklediğini ve süresi
geçen tüplerin hangi müşterilerde kaldığını öğrenmek için bugün tabloları elle tarıyor. Bu proje, o soruları
tek bir kodla / tek bir sayfada cevaplayan küçük bir web panelidir. Veri kaynağı, firmanın SQLite tüp takip
veritabanıdır (Veri dönemi 18.10.2023 – 17.10.2026; müşteri, sipariş ve tüp verileri demodur).

## İş takip panosu

**Pano:** <PANO_BAĞLANTISI_BURAYA>  
Sütunlar: Yapılacak · Devam Ediyor · Tamamlandı. Her kartta açıklama ve kabul kriterleri yazılıdır.

## Projeyi çalıştırma

Gereken: Python 3.10 veya üstü.

```bash
git clone <DEPO_BAĞLANTISI>
cd gaz-tup-takip

python -m venv .venv
# Windows:      .venv\Scripts\activate
# macOS/Linux:  source .venv/bin/activate

pip install -r requirements.txt
python run.py
```

Tarayıcıda **http://127.0.0.1:5000** adresini açın. Uygulama `ornek.db` (1,6 MB örnek veri) ile gelir; kurulum
gerektiren başka bir şey yoktur. Kendi (tam) veritabanınızı kullanmak için:
`GAZ_DB=/yol/gaz_tup_veritabani.db python run.py` (Windows cmd: `set GAZ_DB=C:\yol\gaz_tup_veritabani.db`).

Testler: `python -m pytest`

## İki özelliği nasıl denersiniz?

Veri "simülasyon" modundadır: bugünün tarihi veri setinin son günü, **17.10.2026** kabul edilir.

### Özellik 1 – Tüp sorgulama (kart #1)
1. Ana sayfada **Tüp sorgula**'ya tıklayın (veya `/tup`).
2. Kutuya `TP-OKS50-00095` yazıp **Sorgula**'ya basın.
3. Beklenen: tüp kartı (durum *Müşteride*, müşteri *Vinççi – MUS-0093*, **32 gün**) ve altında en yeni hareket üstte olan geçmiş tablosu.
4. Küçük harf / boşluklu yazım (`tp-oks50-00095 `) aynı sonucu verir. `TP-YOK-99999` yazarsanız "bulunamadı" mesajı çıkar.
5. JSON hali: `/api/tup/TP-OKS50-00095`

### Özellik 2 – Geciken iadeler (kart #2)
1. Ana sayfada **Geciken iadeler**'e tıklayın (veya `/geciken-iadeler`).
2. Beklenen: müşteride izin verilen süreyi (sözleşmede yoksa 30 gün) aşan **2 tüp**; en çok geciken üstte
   (`TP-OKS50-00095` +2 gün, `TP-KRS50-00152` +1 gün).
3. **Müşteri kodu** kutusuna `MUS-0049` yazıp **Süz**'e basın: yalnızca o müşterinin tüpü kalır.
4. Tüp kodu bağlantısına tıklayınca Özellik 1'in tüp kartı açılır. JSON hali: `/api/geciken-iadeler`

## Proje yapısı

```
uygulama.py        Flask uygulaması: veritabanı bağlantısı, ortak sayfa düzeni, özellikleri otomatik bulur
ozellik_tup.py     Özellik 1: tüp sorgulama (SQL + sayfa + API)
ozellik_iade.py    Özellik 2: geciken iadeler (SQL + sayfa + API)
ornek.db           Tam veritabanından üretilmiş küçük örnek veri (1,6 MB)
conftest.py, test_*.py   pytest testleri
run.py             Başlatma dosyası
.github/workflows/ci.yml   GitHub Actions: her push ve pull request'te testler çalışır
```

Yeni özellik eklemek için `ozellik_<ad>.py` dosyası açmak yeterlidir (`bp` ve `MENU` tanımlanır).

## Geliştirme akışı

`main` dalı her zaman çalışır durumdadır. Her pano kartı için `feature/...` dalı açılır, değişiklik pull request
ile `main`'e alınır; CI testleri geçmeden birleştirilmez. Commit ve PR açıklamalarında kart numarası (`#1`) belirtilir.
