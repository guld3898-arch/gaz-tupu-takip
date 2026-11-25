import sqlite3
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from uygulama import create_app  # noqa: E402

ORNEK_DB = Path(__file__).resolve().parent / "ornek.db"


@pytest.fixture()
def app():
    return create_app(ORNEK_DB)


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def mini_db(tmp_path):
    """Kenar durumları denemek için 3 müşterili küçük veritabanı.

    Referans tarih 2026-10-17:
      MUS-A: sözleşme 10 gün, tüp 15 gündür müşteride  -> 5 gün gecikmiş
      MUS-B: sözleşme yok (varsayılan 30), tüp 30 gündür -> gecikmemiş (sınır)
      MUS-C: sözleşme yok, tüp 31 gündür                 -> 1 gün gecikmiş
    """
    yol = tmp_path / "mini.db"
    c = sqlite3.connect(yol)
    c.executescript(
        """
        CREATE TABLE Ayar(Anahtar TEXT PRIMARY KEY, Deger TEXT, Aciklama TEXT);
        INSERT INTO Ayar VALUES('Calisma_Modu','Simulasyon',''),('Veri_Tarihi','2026-10-17','');
        CREATE TABLE Tup(Tup_Id INTEGER PRIMARY KEY, Tur_Kodu TEXT, Tup_Adi TEXT);
        INSERT INTO Tup VALUES(1,'OKS50','50 Lt Oksijen');
        CREATE TABLE Musteri(Musteri_Id INTEGER PRIMARY KEY, Musteri_Kodu TEXT, Musteri_Adi TEXT,
                             Telefon TEXT, Sozlesmeli_Iade_Suresi_Gun INTEGER);
        INSERT INTO Musteri VALUES(1,'MUS-A','A Ltd','111',10),(2,'MUS-B','B Ltd','222',NULL),(3,'MUS-C','C Ltd','333',NULL);
        CREATE TABLE Tup_Birim(Tup_Birim_Id INTEGER PRIMARY KEY, Tup_Kodu TEXT, Tup_Id INTEGER, Durum TEXT,
                               Mevcut_Musteri_Id INTEGER, Son_Teslim_Tarihi TEXT);
        INSERT INTO Tup_Birim VALUES
          (1,'T-1',1,'Müşteride',1,'2026-10-02'),
          (2,'T-2',1,'Müşteride',2,'2026-09-17'),
          (3,'T-3',1,'Müşteride',3,'2026-09-16'),
          (4,'T-4',1,'Depoda-Dolu',NULL,'2026-01-01');
        """
    )
    c.commit()
    c.close()
    return yol
