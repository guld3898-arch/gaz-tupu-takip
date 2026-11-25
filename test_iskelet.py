def test_saglik(client):
    yanit = client.get("/saglik")
    assert yanit.status_code == 200
    assert yanit.get_json() == {"durum": "ok"}


def test_ana_sayfa_acilir(client):
    yanit = client.get("/")
    assert yanit.status_code == 200
    assert "Depo sorgu paneli" in yanit.get_data(as_text=True)
