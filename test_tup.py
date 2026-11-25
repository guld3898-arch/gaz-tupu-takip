"""Özellik 1 - Tüp sorgulama (kabul kriterleri docs/kartlar/01-tup-sorgulama.md içinde)."""
TUP = "TP-OKS50-00095"  # örnek veride MUS-0093 (Vinççi) müşterisinde, 32 gündür


def test_kayitli_tup_karti_doner(client):
    yanit = client.get(f"/api/tup/{TUP}")
    assert yanit.status_code == 200
    kart = yanit.get_json()
    assert kart["Tup_Kodu"] == TUP
    assert kart["Durum"] == "Müşteride"
    assert kart["Musteri_Kodu"] == "MUS-0093"
    assert kart["Musteride_Kalis_Gun"] == 32


def test_kod_kucuk_harf_ve_bosluk_toleransi(client):
    yanit = client.get("/tup", query_string={"kod": "  tp-oks50-00095 "})
    assert yanit.status_code == 302
    assert yanit.headers["Location"].endswith(f"/tup/{TUP}")


def test_gecmis_en_yeni_ustte(client):
    gecmis = client.get(f"/api/tup/{TUP}").get_json()["Gecmis"]
    assert len(gecmis) >= 1
    tarihler = [g["Tarih"] for g in gecmis]
    assert tarihler == sorted(tarihler, reverse=True)
    assert gecmis[0]["Hareket_Tipi"] == "Teslimat"


def test_kayitsiz_kod_404_ve_mesaj(client):
    yanit = client.get("/tup/TP-YOK-99999")
    assert yanit.status_code == 404
    assert "bulunamadı" in yanit.get_data(as_text=True)
    assert client.get("/api/tup/TP-YOK-99999").status_code == 404


def test_detay_sayfasi_bilgileri_gosterir(client):
    html = client.get(f"/tup/{TUP}").get_data(as_text=True)
    assert TUP in html
    assert "Vinççi" in html
    assert "Hareket geçmişi" in html


def test_depodaki_tupte_musteri_ve_kalis_yok(client):
    kod = "TP-OKS5-00001"  # örnek veride Depoda-Dolu
    kart = client.get(f"/api/tup/{kod}").get_json()
    assert kart["Durum"] == "Depoda-Dolu"
    assert kart["Musteri_Kodu"] is None
    assert kart["Musteride_Kalis_Gun"] is None
