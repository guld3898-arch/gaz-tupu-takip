"""Gaz Tüp Takip - depo sorgu paneli (tek klasörlü, düz yapı).

Her özellik `ozellik_*.py` adlı ayrı bir dosyadır; bu dosya onları otomatik bulur.
Yeni özellik = yeni dosya, burayı değiştirmek gerekmez.
"""
import glob
import importlib
import os
import sqlite3
import sys
from datetime import date

from flask import Flask, current_app, g, render_template_string
from jinja2 import DictLoader

KLASOR = os.path.dirname(os.path.abspath(__file__))
if KLASOR not in sys.path:
    sys.path.insert(0, KLASOR)

TEMEL = """<!doctype html>
<html lang="tr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{% block baslik %}Gaz Tüp Takip{% endblock %}</title>
<style>
:root{--fg:#1c2530;--muted:#5b6673;--bg:#f6f7f9;--card:#fff;--line:#dde2e8;--accent:#0b6b5d;--warn:#b42318}
@media (prefers-color-scheme:dark){:root{--fg:#e8ecf1;--muted:#9aa5b1;--bg:#14181d;--card:#1c2229;--line:#2d3640;--accent:#4cc2ae;--warn:#ff8a7a}}
*{box-sizing:border-box}body{margin:0;font:16px/1.5 system-ui,sans-serif;color:var(--fg);background:var(--bg)}
header{display:flex;flex-wrap:wrap;gap:8px 24px;padding:12px 16px;background:var(--card);border-bottom:1px solid var(--line)}
header a{color:var(--fg);text-decoration:none}.marka{font-weight:700;color:var(--accent)}
main{max-width:960px;margin:0 auto;padding:20px 16px 48px}h1{font-size:1.5rem}
.kartlar{list-style:none;padding:0;display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:12px}
.kartlar a{display:block;padding:14px;background:var(--card);border:1px solid var(--line);border-radius:8px;color:var(--fg);text-decoration:none}
.kartlar span{display:block;color:var(--muted);font-size:.9rem}
form.ara{display:flex;gap:8px;flex-wrap:wrap;margin:12px 0 20px}
input[type=text]{flex:1 1 240px;padding:9px 11px;border:1px solid var(--line);border-radius:6px;background:var(--card);color:var(--fg);font:inherit}
button{padding:9px 16px;border:0;border-radius:6px;background:var(--accent);color:#fff;font:inherit;cursor:pointer}
table{width:100%;border-collapse:collapse;background:var(--card);border:1px solid var(--line)}
th,td{text-align:left;padding:8px 10px;border-bottom:1px solid var(--line);font-size:.93rem}th{color:var(--muted)}
.kutu{overflow-x:auto}dl.bilgi{display:grid;grid-template-columns:max-content 1fr;gap:6px 16px;background:var(--card);border:1px solid var(--line);border-radius:8px;padding:14px}
dl.bilgi dt{color:var(--muted)}dl.bilgi dd{margin:0}.hata{color:var(--warn);font-weight:600}.not{color:var(--muted)}.gec{color:var(--warn);font-weight:600}
</style></head><body>
<header><a class="marka" href="/">Gaz Tüp Takip</a>
{% for sira, baslik, adres, aciklama in menu %}<a href="{{ adres }}">{{ baslik }}</a>{% endfor %}</header>
<main>{% block icerik %}{% endblock %}</main></body></html>"""

ANA_SAYFA = """{% extends "base.html" %}{% block icerik %}
<h1>Depo sorgu paneli</h1>
<p>Depo sorumlusunun gün içinde en sık sorduğu sorulara hızlı cevap verir.</p>
{% if menu %}<ul class="kartlar">{% for sira, baslik, adres, aciklama in menu %}
<li><a href="{{ adres }}"><strong>{{ baslik }}</strong><span>{{ aciklama }}</span></a></li>{% endfor %}</ul>
{% else %}<p class="not">Henüz sayfa yok.</p>{% endif %}{% endblock %}"""


def get_db() -> sqlite3.Connection:
    """İstek başına tek, salt okunur bağlantı (demo verisi bozulmaz)."""
    if "db" not in g:
        g.db = sqlite3.connect(f"file:{current_app.config['DB_PATH']}?mode=ro", uri=True)
        g.db.row_factory = sqlite3.Row
    return g.db


def bugun(db) -> date:
    """Ayar.Calisma_Modu 'Simulasyon' ise Ayar.Veri_Tarihi, 'Gercek' ise bilgisayar tarihi."""
    ayar = dict(db.execute("SELECT Anahtar, Deger FROM Ayar WHERE Anahtar IN ('Calisma_Modu','Veri_Tarihi')").fetchall())
    if ayar.get("Calisma_Modu", "Simulasyon") == "Gercek":
        return date.today()
    return date.fromisoformat(ayar["Veri_Tarihi"])


def create_app(db_path=None) -> Flask:
    app = Flask(__name__)
    app.config["DB_PATH"] = str(db_path or os.environ.get("GAZ_DB") or os.path.join(KLASOR, "ornek.db"))
    app.jinja_loader = DictLoader({"base.html": TEMEL, "index.html": ANA_SAYFA})
    app.teardown_appcontext(lambda _h: (lambda c: c.close() if c else None)(g.pop("db", None)))

    menu = []
    for yol in sorted(glob.glob(os.path.join(KLASOR, "ozellik_*.py"))):
        mod = importlib.import_module(os.path.basename(yol)[:-3])
        app.register_blueprint(mod.bp)
        menu.append(mod.MENU)  # (sıra, başlık, adres, açıklama)
    menu.sort()
    app.context_processor(lambda: {"menu": menu})

    @app.route("/")
    def index():
        return render_template_string(ANA_SAYFA)

    @app.route("/saglik")
    def saglik():
        return {"durum": "ok"}

    return app
