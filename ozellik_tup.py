"""Özellik 1 - Tüp sorgulama: tüp koduyla kart ve hareket geçmişi (Kart #1)."""
from datetime import date

from flask import Blueprint, jsonify, redirect, render_template_string, request

from uygulama import bugun, get_db

bp = Blueprint("tup", __name__)
MENU = (10, "Tüp sorgula", "/tup", "Tüp koduyla durum, müşteri ve hareket geçmişi")
GECMIS_LIMIT = 50


def kodu_duzenle(kod):
    """Barkod okuyucu boşluk/küçük harf getirebilir: ' tp-oks50-00095 ' -> 'TP-OKS50-00095'."""
    return (kod or "").strip().upper()


def tup_getir(db, kod):
    """Tüp kartı + hareket geçmişi; kod kayıtlı değilse None."""
    kod = kodu_duzenle(kod)
    if not kod:
        return None
    satir = db.execute(
        """
        SELECT b.Tup_Birim_Id, b.Tup_Kodu, b.Seri_No, t.Tur_Kodu, t.Tup_Adi, t.Gaz_Turu,
               b.Durum, b.Mulkiyet, b.Uretim_Yili, b.Muayene_Sonraki_Tarihi,
               b.Son_Dolum_Tarihi, b.Son_Teslim_Tarihi, b.Toplam_Teslimat_Sayisi,
               m.Musteri_Kodu, m.Musteri_Adi
        FROM Tup_Birim b
        JOIN Tup t ON t.Tup_Id = b.Tup_Id
        LEFT JOIN Musteri m ON m.Musteri_Id = b.Mevcut_Musteri_Id
        WHERE b.Tup_Kodu = ?
        """,
        (kod,),
    ).fetchone()
    if satir is None:
        return None
    kart = dict(satir)
    birim_id = kart.pop("Tup_Birim_Id")
    kart["Musteride_Kalis_Gun"] = None
    if kart["Durum"] == "Müşteride" and kart["Son_Teslim_Tarihi"]:
        kart["Musteride_Kalis_Gun"] = (bugun(db) - date.fromisoformat(kart["Son_Teslim_Tarihi"][:10])).days
    gecmis = db.execute(
        """
        SELECT h.Tarih, h.Hareket_Tipi, m.Musteri_Kodu, m.Musteri_Adi,
               s.Siparis_Kodu, a.Arac_Kodu, h.Musteride_Kalis_Gun
        FROM Tup_Hareket h
        LEFT JOIN Musteri m ON m.Musteri_Id = h.Musteri_Id
        LEFT JOIN Siparis s ON s.Siparis_Id = h.Siparis_Id
        LEFT JOIN Arac a ON a.Arac_Id = h.Arac_Id
        WHERE h.Tup_Birim_Id = ?
        ORDER BY h.Tarih DESC, h.Hareket_Id DESC
        LIMIT ?
        """,
        (birim_id, GECMIS_LIMIT),
    ).fetchall()
    kart["Gecmis"] = [dict(g) for g in gecmis]
    return kart


SORGU = """{% extends "base.html" %}{% block baslik %}Tüp sorgula{% endblock %}{% block icerik %}
<h1>Tüp sorgula</h1>
<p class="not">Barkodu okutun veya tüp kodunu yazın (örnek: TP-OKS50-00095).</p>
<form class="ara" action="/tup" method="get">
  <input type="text" name="kod" placeholder="TP-OKS50-00095" autofocus autocomplete="off" aria-label="Tüp kodu">
  <button type="submit">Sorgula</button></form>
{% if hata %}<p class="hata">{{ hata }}</p>{% endif %}{% endblock %}"""

DETAY = """{% extends "base.html" %}{% block baslik %}{{ t.Tup_Kodu }}{% endblock %}{% block icerik %}
<h1>{{ t.Tup_Kodu }}</h1>
<form class="ara" action="/tup" method="get">
  <input type="text" name="kod" placeholder="Başka tüp kodu" autocomplete="off" aria-label="Tüp kodu">
  <button type="submit">Sorgula</button></form>
<dl class="bilgi">
  <dt>Tür</dt><dd>{{ t.Tup_Adi }} ({{ t.Tur_Kodu }})</dd>
  <dt>Durum</dt><dd><strong>{{ t.Durum }}</strong></dd>
  {% if t.Musteri_Adi %}
  <dt>Müşteri</dt><dd>{{ t.Musteri_Adi }} ({{ t.Musteri_Kodu }})</dd>
  <dt>Müşteride kalış</dt><dd>{{ t.Musteride_Kalis_Gun }} gün (teslim: {{ t.Son_Teslim_Tarihi }})</dd>
  {% endif %}
  <dt>Mülkiyet</dt><dd>{{ t.Mulkiyet }}</dd>
  <dt>Son dolum</dt><dd>{{ t.Son_Dolum_Tarihi or '-' }}</dd>
  <dt>Sonraki muayene</dt><dd>{{ t.Muayene_Sonraki_Tarihi or '-' }}</dd>
  <dt>Toplam teslimat</dt><dd>{{ t.Toplam_Teslimat_Sayisi }}</dd>
</dl>
<h2>Hareket geçmişi <small class="not">(en yeni üstte, en çok {{ t.Gecmis|length }} kayıt)</small></h2>
{% if t.Gecmis %}<div class="kutu"><table>
<thead><tr><th>Tarih</th><th>Hareket</th><th>Müşteri</th><th>Sipariş</th><th>Araç</th></tr></thead><tbody>
{% for g in t.Gecmis %}<tr><td>{{ g.Tarih }}</td><td>{{ g.Hareket_Tipi }}</td><td>{{ g.Musteri_Adi or '-' }}</td><td>{{ g.Siparis_Kodu or '-' }}</td><td>{{ g.Arac_Kodu or '-' }}</td></tr>{% endfor %}
</tbody></table></div>{% else %}<p class="not">Bu tüp için kayıtlı hareket yok.</p>{% endif %}{% endblock %}"""


@bp.route("/tup")
def sorgu():
    kod = request.args.get("kod", "")
    if kod.strip():
        return redirect(f"/tup/{kodu_duzenle(kod)}")
    return render_template_string(SORGU)


@bp.route("/tup/<kod>")
def detay(kod):
    kart = tup_getir(get_db(), kod)
    if kart is None:
        return render_template_string(SORGU, hata=f"'{kodu_duzenle(kod)}' kodlu tüp bulunamadı."), 404
    return render_template_string(DETAY, t=kart)


@bp.route("/api/tup/<kod>")
def api(kod):
    kart = tup_getir(get_db(), kod)
    if kart is None:
        return jsonify(hata="Tüp bulunamadı", kod=kodu_duzenle(kod)), 404
    return jsonify(kart)
