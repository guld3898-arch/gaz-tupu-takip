"""Özellik 2 - Geciken iadeler (kabul kriterleri docs/kartlar/02-geciken-iadeler.md içinde)."""
import sqlite3

from ozellik_iade import geciken_iadeler


def _baglan(yol):
    c = sqlite3.connect(yol)
    c.row_factory = sqlite3.Row
    return c


def test_sozlesme_suresi_ve_varsayilan_30_gun_kurali(mini_db):
    sonuc = geciken_iadeler(_baglan(mini_db))
    # T-2 tam 30 gün: sınırda, gecikmiş sayılmaz. Depodaki T-4 listelenmez.
    assert [(s["Tup_Kodu"], s["Fazla_Gun"]) for s in sonuc] == [("T-1", 5), ("T-3", 1)]


def test_musteri_filtresi(mini_db):
    sonuc = geciken_iadeler(_baglan(mini_db), "mus-c")
    assert [s["Tup_Kodu"] for s in sonuc] == ["T-3"]


def test_hic_geciken_yoksa_bos_liste(mini_db):
    assert geciken_iadeler(_baglan(mini_db), "MUS-B") == []


def test_ornek_veride_en_cok_geciken_ustte(client):
    liste = client.get("/api/geciken-iadeler").get_json()
    assert [s["Tup_Kodu"] for s in liste] == ["TP-OKS50-00095", "TP-KRS50-00152"]
    assert liste[0]["Kalis_Gun"] == 32 and liste[0]["Izin_Verilen_Gun"] == 30
    assert liste[0]["Fazla_Gun"] == 2


def test_sayfa_listeyi_ve_tup_baglantisini_gosterir(client):
    html = client.get("/geciken-iadeler").get_data(as_text=True)
    assert "TP-OKS50-00095" in html
    assert "/tup/TP-OKS50-00095" in html
    assert "+2 gün" in html


def test_sayfa_filtreli(client):
    html = client.get("/geciken-iadeler", query_string={"musteri": "MUS-0049"}).get_data(as_text=True)
    assert "TP-KRS50-00152" in html
    assert "TP-OKS50-00095" not in html
