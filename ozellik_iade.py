"""Özellik 2 - Geciken iadeler: müşteride izin verilen süreden uzun kalan tüpler (Kart #2)."""
from datetime import date

from flask import Blueprint, jsonify, render_template_string, request

from uygulama import bugun, get_db

bp = Blueprint("iade", __name__)
MENU = (20, "Geciken iadeler", "/geciken-iadeler", "Müşteride izin verilen süreyi aşan tüpler")
VARSAYILAN_IADE_GUN = 30  # sözleşmede süre yazmıyorsa kullanılır


def geciken_iadeler(db, musteri_kodu=None):
    """Süresi aşılan tüpler, en çok geciken üstte.

    Kalış günü = bugün - son teslim tarihi. İzin = müşterinin sözleşmeli iade süresi, yoksa 30 gün.
    Fazla gün = kalış - izin; yalnızca > 0 olanlar listelenir.
    """
    bugun_tarih = bugun(db)
    sorgu = """
        SELECT b.Tup_Kodu, t.Tup_Adi, m.Musteri_Kodu, m.Musteri_Adi, m.Telefon,
               b.Son_Teslim_Tarihi AS Teslim_Tarihi,
               COALESCE(m.Sozlesmeli_Iade_Suresi_Gun, ?) AS Izin_Verilen_Gun
        FROM Tup_Birim b
        JOIN Musteri m ON m.Musteri_Id = b.Mevcut_Musteri_Id
        JOIN Tup t ON t.Tup_Id = b.Tup_Id
        WHERE b.Durum = 'Müşteride' AND b.Son_Teslim_Tarihi IS NOT NULL
    """
    parametre = [VARSAYILAN_IADE_GUN]
    if musteri_kodu:
        sorgu += " AND m.Musteri_Kodu = ?"
        parametre.append(musteri_kodu.strip().upper())
    sonuc = []
    for satir in db.execute(sorgu, parametre).fetchall():
        k = dict(satir)
        k["Kalis_Gun"] = (bugun_tarih - date.fromisoformat(k["Teslim_Tarihi"][:10])).days
        k["Fazla_Gun"] = k["Kalis_Gun"] - k["Izin_Verilen_Gun"]
        if k["Fazla_Gun"] > 0:
            sonuc.append(k)
    sonuc.sort(key=lambda k: (-k["Fazla_Gun"], k["Tup_Kodu"]))
    return sonuc


SAYFA = """{% extends "base.html" %}{% block baslik %}Geciken iadeler{% endblock %}{% block icerik %}
<h1>Geciken iadeler</h1>
<p class="not">Referans tarih: {{ bugun.strftime('%d.%m.%Y') }}. Müşteride izin verilen süreden (sözleşmede yoksa 30 gün) uzun kalan tüpler.</p>
<form class="ara" method="get" action="/geciken-iadeler">
  <input type="text" name="musteri" value="{{ musteri }}" placeholder="Müşteri kodu (örnek: MUS-0093)" aria-label="Müşteri kodu">
  <button type="submit">Süz</button></form>
{% if satirlar %}<p><strong>{{ satirlar|length }}</strong> tüp süresini aştı.</p>
<div class="kutu"><table>
<thead><tr><th>Tüp</th><th>Tür</th><th>Müşteri</th><th>Telefon</th><th>Teslim</th><th>Kalış</th><th>İzin</th><th>Fazla</th></tr></thead><tbody>
{% for s in satirlar %}<tr>
<td><a href="/tup/{{ s.Tup_Kodu }}">{{ s.Tup_Kodu }}</a></td><td>{{ s.Tup_Adi }}</td>
<td>{{ s.Musteri_Adi }} <span class="not">({{ s.Musteri_Kodu }})</span></td><td>{{ s.Telefon or '-' }}</td>
<td>{{ s.Teslim_Tarihi }}</td><td>{{ s.Kalis_Gun }} gün</td><td>{{ s.Izin_Verilen_Gun }} gün</td>
<td class="gec">+{{ s.Fazla_Gun }} gün</td></tr>{% endfor %}
</tbody></table></div>{% else %}<p>Süresini aşan tüp yok.</p>{% endif %}{% endblock %}"""


@bp.route("/geciken-iadeler")
def liste():
    db = get_db()
    musteri = request.args.get("musteri", "").strip()
    return render_template_string(SAYFA, satirlar=geciken_iadeler(db, musteri or None), musteri=musteri, bugun=bugun(db))


@bp.route("/api/geciken-iadeler")
def api():
    musteri = request.args.get("musteri", "").strip()
    return jsonify(geciken_iadeler(get_db(), musteri or None))
