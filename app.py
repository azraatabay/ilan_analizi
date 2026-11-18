"""
Kariyer Yetkinlik Analiz Sistemi - Streamlit arayüzü

Çalıştırma (proje klasöründe):
    streamlit run app.py

Gerekenler : analiz_sonuclari.csv   (llm_analysis.py üretir)
İsteğe bağlı: yol_haritasi.json     (python yol_haritasi.py üretir)
"""
import html
import json
import os
import re

import streamlit as st

import analiz_ozet as ao

st.set_page_config(page_title="Kariyer Yetkinlik Analiz Sistemi", page_icon="🎓", layout="wide")

YOL_HARITASI = os.path.join(ao.KLASOR, "yol_haritasi.json")
TUM = "Tüm pozisyonlar"

# ====================================================================== stil
CSS = """
<style>
:root{
  --navy:#1F2A44; --navy2:#34436A; --slate:#5B6577; --mist:#F4F5F9; --line:#E6E9F2;
  --peri:#8E9AC7; --lav:#B7A6CF; --rose:#D9A7B8; --sage:#9DBBAA; --sky:#A8C5DD;
}
.stApp{background:var(--mist);}
.block-container{max-width:1180px;padding-top:1.6rem;padding-bottom:3rem;}
footer{visibility:hidden;}
label[data-testid="stWidgetLabel"] p{font-weight:600;color:var(--navy);}
div[data-baseweb="select"] > div{border-radius:12px;border:1px solid var(--line);
  box-shadow:0 2px 10px rgba(31,42,68,.06);background:#fff;}

/* ---------- hero ---------- */
.hero{position:relative;overflow:hidden;border-radius:22px;padding:34px 38px 30px;color:#fff;
  background:linear-gradient(135deg,#1F2A44 0%,#34436A 58%,#4C5C8C 100%);
  box-shadow:0 14px 34px rgba(31,42,68,.22);margin-bottom:22px;}
.hero:before{content:"";position:absolute;right:-70px;top:-90px;width:300px;height:300px;border-radius:50%;
  background:radial-gradient(circle,rgba(183,166,207,.55),rgba(183,166,207,0) 70%);}
.hero:after{content:"";position:absolute;right:140px;bottom:-110px;width:260px;height:260px;border-radius:50%;
  background:radial-gradient(circle,rgba(217,167,184,.40),rgba(217,167,184,0) 70%);}
.hero .accent{position:absolute;left:0;top:0;height:5px;width:100%;
  background:linear-gradient(90deg,var(--rose),var(--lav),var(--sky));}
.hero h1{position:relative;z-index:1;margin:0 0 10px;font-size:34px;line-height:1.15;font-weight:800;
  letter-spacing:-.3px;color:#fff;}
.hero .tag{position:relative;z-index:1;display:inline-block;font-size:13px;font-weight:600;letter-spacing:.4px;
  padding:6px 14px;border-radius:999px;background:rgba(255,255,255,.14);color:#EDE6F7;
  border:1px solid rgba(255,255,255,.22);margin-bottom:14px;}
.hero p{position:relative;z-index:1;margin:0;max-width:760px;font-size:15px;line-height:1.55;color:#CBD3EA;}

/* ---------- bölüm başlığı ---------- */
.sec{display:flex;align-items:baseline;gap:10px;margin:30px 0 14px;color:var(--navy);
  font-size:20px;font-weight:800;}
.sec:before{content:"";width:6px;height:20px;border-radius:4px;align-self:center;
  background:linear-gradient(180deg,var(--peri),var(--rose));}
.sec small{font-size:13px;font-weight:500;color:var(--slate);}

/* ---------- kart tabanı ---------- */
.card{background:#fff;border:1px solid var(--line);border-radius:18px;padding:20px 22px;
  box-shadow:0 4px 18px rgba(31,42,68,.07);transition:transform .22s ease,box-shadow .22s ease;}
.card:hover{transform:translateY(-4px);box-shadow:0 14px 30px rgba(31,42,68,.14);}

/* ---------- KPI ---------- */
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:16px;}
.kpi{position:relative;overflow:hidden;}
.kpi .ic{width:42px;height:42px;border-radius:12px;display:flex;align-items:center;justify-content:center;
  font-size:20px;margin-bottom:12px;}
.kpi .lb{font-size:12px;font-weight:700;letter-spacing:.5px;text-transform:uppercase;color:var(--slate);}
.kpi .vl{font-size:34px;font-weight:800;color:var(--navy);line-height:1.15;margin:4px 0 2px;}
.kpi .sb{font-size:13px;color:var(--slate);}

/* ---------- ilerleme çubukları ---------- */
.card h3{margin:0 0 4px;font-size:17px;color:var(--navy);font-weight:800;}
.card .hint{font-size:12.5px;color:var(--slate);margin-bottom:14px;}
.sk{margin:13px 0;}
.sk .top{display:flex;justify-content:space-between;font-size:14px;color:var(--navy);margin-bottom:6px;}
.sk .top b{font-weight:700;}
.sk .top span{color:var(--slate);font-size:13px;}
.track{height:11px;border-radius:999px;background:#EEF0F7;overflow:hidden;}
.fill{height:100%;border-radius:999px;animation:grow .9s ease-out both;}
.f1{background:linear-gradient(90deg,var(--peri),var(--lav));}
.f2{background:linear-gradient(90deg,var(--sage),var(--sky));}
@keyframes grow{from{width:0}}
.chips{display:flex;flex-wrap:wrap;gap:8px;margin-top:6px;}
.chip{font-size:12.5px;font-weight:600;padding:5px 11px;border-radius:999px;color:var(--navy);max-width:100%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}
.c0{background:#E6E9F7;} .c1{background:#EFE6F6;} .c2{background:#F8E6EC;} .c3{background:#E3F0E9;} .c4{background:#E2EEF7;}

/* ---------- yapay zeka paneli ---------- */
.ai{position:relative;border-radius:20px;padding:0;overflow:hidden;background:#fff;border:1px solid var(--line);
  box-shadow:0 8px 26px rgba(31,42,68,.10);transition:box-shadow .22s ease;}
.ai:hover{box-shadow:0 16px 36px rgba(31,42,68,.16);}
.ai .head{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:16px 24px;
  background:linear-gradient(100deg,#2A3658,#4A5A86 70%,#6C6FA3);color:#fff;}
.ai .head .l{display:flex;align-items:center;gap:12px;font-weight:700;font-size:16px;}
.ai .spark{width:34px;height:34px;border-radius:10px;display:flex;align-items:center;justify-content:center;
  background:rgba(255,255,255,.16);font-size:18px;}
.ai .badge{font-size:12px;font-weight:600;padding:5px 12px;border-radius:999px;
  background:rgba(255,255,255,.16);border:1px solid rgba(255,255,255,.25);color:#EDE6F7;white-space:nowrap;}
.ai .body{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:26px;padding:24px;}
.ai h4{margin:0 0 10px;font-size:15px;color:var(--navy);font-weight:800;}
.ai p{margin:0 0 12px;font-size:14.5px;line-height:1.6;color:#39445C;}
.ai ul{margin:0;padding-left:0;list-style:none;}
.ai li{position:relative;padding:7px 0 7px 26px;font-size:14px;color:#39445C;line-height:1.45;}
.ai li:before{content:"✓";position:absolute;left:0;top:7px;width:18px;height:18px;border-radius:50%;
  background:#E3F0E9;color:#4F7A63;font-size:11px;font-weight:800;text-align:center;line-height:18px;}
.step{display:flex;gap:14px;position:relative;padding-bottom:16px;}
.step:not(:last-child):before{content:"";position:absolute;left:15px;top:32px;bottom:0;width:2px;background:#E1E5F1;}
.step .n{flex:0 0 32px;height:32px;border-radius:50%;background:linear-gradient(135deg,var(--peri),var(--lav));
  color:#fff;font-weight:800;font-size:14px;display:flex;align-items:center;justify-content:center;
  box-shadow:0 3px 8px rgba(142,154,199,.5);}
.step .t{font-size:12px;font-weight:700;color:var(--peri);text-transform:uppercase;letter-spacing:.4px;}
.step .h{font-size:14.5px;font-weight:700;color:var(--navy);margin:1px 0 3px;}
.step .d{font-size:13.5px;color:#4A556D;line-height:1.5;}
.ai .note{padding:0 24px 18px;font-size:12.5px;color:var(--slate);}
.empty{padding:26px;text-align:center;color:var(--slate);font-size:14px;}

/* ---------- ilan kartları ---------- */
.jobs{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:16px;}
.job{display:flex;flex-direction:column;gap:10px;}
.job .top{display:flex;justify-content:space-between;gap:10px;align-items:flex-start;}
.job .pos{font-size:16px;font-weight:800;color:var(--navy);line-height:1.25;}
.job .firm{font-size:13px;color:var(--slate);margin-top:3px;}
.lvl{font-size:11.5px;font-weight:700;padding:4px 10px;border-radius:999px;white-space:nowrap;}
.l-Stajyer{background:#E3F0E9;color:#3F6B54;} .l-Junior{background:#E2EEF7;color:#35607F;}
.l-Mid{background:#EFE6F6;color:#6A4F8A;} .l-Senior{background:#F8E6EC;color:#94485F;}
.l-Belirtilmemiş{background:#EEF0F5;color:#5B6577;}
.meta{display:flex;flex-wrap:wrap;gap:12px;font-size:12.5px;color:var(--slate);}
.job details{margin-top:2px;border-top:1px dashed var(--line);padding-top:8px;}
.job summary{cursor:pointer;font-size:12.5px;font-weight:600;color:var(--peri);}
.job details p{font-size:12.5px;line-height:1.55;color:#4A556D;margin:8px 0 0;}
.foot{margin-top:30px;text-align:center;font-size:12.5px;color:var(--slate);line-height:1.6;}
</style>
"""


CSS = re.sub(r"/\*.*?\*/", "", CSS, flags=re.S)
CSS = "\n".join(l.strip() for l in CSS.splitlines() if l.strip())


def esc(x):
    return html.escape(str(x), quote=True)


def yaz(parcalar):
    """HTML'i tek blok olarak yazar (satır başı boşluk ve boş satır yok: Markdown kod bloğuna çevirmesin)."""
    st.markdown("".join(parcalar), unsafe_allow_html=True)


# ====================================================================== veri
@st.cache_data
def veri_yukle():
    df = ao.yukle()
    df["seviye_tr"] = df["seviye"].map(lambda s: ao.SEVIYE_ADLARI.get(ao.norm(s).strip(), "Belirtilmemiş"))
    return df


def llm_yukle():
    if not os.path.exists(YOL_HARITASI):
        return {}
    with open(YOL_HARITASI, encoding="utf-8") as f:
        return json.load(f)


# ====================================================================== parçalar
def kpi(ikon, renk, etiket, deger, alt):
    return (f'<div class="card kpi"><div class="ic" style="background:{renk}">{ikon}</div>'
            f'<div class="lb">{esc(etiket)}</div><div class="vl">{esc(deger)}</div>'
            f'<div class="sb">{esc(alt)}</div></div>')


def cubuklar(baslik, ipucu, sayac, n_ilan, adet, sinif):
    govde = []
    for i, (ad, say) in enumerate(sayac.most_common(adet)):
        yuzde = 100 * say / n_ilan
        govde.append(
            f'<div class="sk"><div class="top"><b>{esc(ad)}</b><span>%{yuzde:.0f} · {say} ilan</span></div>'
            f'<div class="track"><div class="fill {sinif}" style="width:{yuzde:.1f}%;animation-delay:{i * 70}ms"></div>'
            f'</div></div>')
    if not govde:
        govde = ['<div class="empty">Bu seçimde gösterilecek veri yok.</div>']
    return f'<div class="card"><h3>{esc(baslik)}</h3><div class="hint">{esc(ipucu)}</div>{"".join(govde)}</div>'


def ai_paneli(kayit, notu):
    if not kayit:
        return ('<div class="ai"><div class="head"><div class="l"><div class="spark">✨</div>'
                'Yapay Zeka Analizi</div></div><div class="empty">Yapay zeka analizi henüz üretilmedi.<br>'
                'Terminalde <b>python yol_haritasi.py</b> çalıştırın.</div></div>')
    maddeler = "".join(f"<li>{esc(m)}</li>" for m in kayit["one_cikanlar"])
    adimlar = "".join(
        f'<div class="step"><div class="n">{i}</div><div><div class="t">{esc(a["donem"])}</div>'
        f'<div class="h">{esc(a["baslik"])}</div><div class="d">{esc(a["aciklama"])}</div></div></div>'
        for i, a in enumerate(kayit["yol_haritasi"], 1))
    return (
        '<div class="ai"><div class="head"><div class="l"><div class="spark">✨</div>Yapay Zeka Analizi</div>'
        f'<div class="badge">Gemini · {kayit.get("ilan_sayisi", "?")} ilana dayanır</div></div>'
        '<div class="body"><div><h4>🔎 Sektör Ne Bekliyor?</h4>'
        f'<p>{esc(kayit["sektor_ne_bekliyor"])}</p><ul>{maddeler}</ul></div>'
        f'<div><h4>🗺️ Kariyer Yol Haritası Tavsiyeleri</h4>{adimlar}</div></div>'
        + (f'<div class="note">ℹ️ {esc(notu)}</div>' if notu else "") + '</div>')


def ilan_karti(satir, tum_sayac):
    etiketler = sorted(ao.teknik_adlar(satir["teknik_beceriler"]), key=lambda t: -tum_sayac.get(t, 0))[:5]
    chip = "".join(f'<span class="chip c{i % 5}">{esc(t)}</span>' for i, t in enumerate(etiketler))
    ozet = " ".join(str(satir["metin"]).split())
    ozet = ozet[:450] + ("…" if len(ozet) > 450 else "")
    sev = satir["seviye_tr"]
    return (
        f'<div class="card job"><div class="top"><div><div class="pos">{esc(satir["pozisyon"])}</div>'
        f'<div class="firm">{esc(satir["firma"])}</div></div><span class="lvl l-{esc(sev)}">{esc(sev)}</span></div>'
        f'<div class="meta"><span>📍 {esc(satir["sehir"])}</span><span>🕒 {esc(satir["calisma_tipi"])}</span>'
        f'<span>🏢 {esc(satir["calisma_modeli"])}</span></div>'
        f'<div class="chips">{chip}</div>'
        f'<details><summary>İlandan özet</summary><p>{esc(ozet)}</p></details></div>')


# ====================================================================== sayfa
yaz([CSS])

if not os.path.exists(ao.CSV_YOLU):
    st.error("analiz_sonuclari.csv bulunamadı. Önce `python llm_analysis.py` çalıştırın.")
    st.stop()

df_tum = veri_yukle()
kaynaklar = ", ".join(sorted(df_tum["kaynak"].dropna().unique()))

# 1) üst kısım
yaz([
    '<div class="hero"><div class="accent"></div>',
    '<h1>Kariyer Yetkinlik Analiz Sistemi</h1>',
    '<div class="tag">✨ Yapay Zeka Destekli Sektör Analitiği</div>',
    f'<p>{len(df_tum)} bilgisayar ve yazılım mühendisliği ilanı {esc(kaynaklar)} üzerinden web scraping ile toplandı. ',
    'Teknik yetkinlikler, yabancı dil ve sosyal beceri beklentileri büyük dil modeli (Gemini) ile ilan metinlerinden ',
    'çıkarıldı ve kariyer yol haritasına dönüştürüldü.</p></div>',
])

# 2) pozisyon seçimi
sayilar = df_tum["pozisyon"].value_counts()
secim = st.selectbox(
    "Pozisyon seçin",
    [TUM] + list(sayilar.index),
    format_func=lambda p: f"{TUM} ({len(df_tum)} ilan)" if p == TUM else f"{p} ({sayilar[p]} ilan)",
)
df = df_tum if secim == TUM else df_tum[df_tum["pozisyon"] == secim]
n = len(df)

sayac = ao.teknik_say(df)
diller, ing_seviye, dil_yok = ao.dil_say(df)
medyan, medyan_n = ao.medyan_deneyim(df)
en_cok = sayac.most_common(1)[0][0] if sayac else "-"
tekrar_eden = sum(1 for v in sayac.values() if v >= 2)

# 3) özet kartları
yaz(['<div class="kpis">',
     kpi("📄", "#E6E9F7", "İncelenen toplam ilan", n, f"{len(df_tum)} ilan içinden"),
     kpi("🛠️", "#EFE6F6", "Teknik yetkinlik çeşitliliği", len(sayac),
         f"{tekrar_eden} tanesi birden fazla ilanda · en sık: {en_cok}"),
     kpi("🌍", "#E3F0E9", "Beklenen yabancı dil (% İngilizce)", f"%{round(100 * diller.get('İngilizce', 0) / n)}",
         f"{diller.get('İngilizce', 0)} / {n} ilanda İngilizce isteniyor"),
     kpi("⏳", "#F8E6EC", "İstenen deneyim (medyan)", f"{medyan:g} yıl" if medyan is not None else "-",
         f"{medyan_n} ilanın alt sınırından" if medyan is not None else "Deneyim belirtilmemiş"),
     '</div>'])
if n < 5:
    st.caption("⚠️ Bu pozisyonda ilan sayısı az, yüzdeleri yorumlarken dikkatli olun.")

# 4) teknik yetkinlik çubukları
yaz(['<div class="sec">Teknik yetkinlikler <small>en çok aranan tech stack</small></div>'])
sol, sag = st.columns([3, 2])
with sol:
    adet = st.slider("Gösterilecek beceri sayısı", 5, 20, 10)
    yaz([cubuklar("En çok aranan teknolojiler",
                  "Yüzde = o beceriyi isteyen ilanların seçili ilanlara oranı", sayac, n, adet, "f1")])
with sag:
    st.write("")
    st.write("")
    yaz([cubuklar("Öne çıkan sosyal beceriler", "Benzer ifadeler gruplanarak sayıldı",
                  ao.sosyal_say(df), n, 6, "f2")])
    seviyeler = ao.seviye_say(df)
    chips = "".join(f'<span class="chip c{i}">{esc(ad)} · {say}</span>'
                    for i, (ad, say) in enumerate(seviyeler.items()) if say)
    yaz([f'<div class="card" style="margin-top:16px"><h3>İstenen seviye</h3><div class="chips">{chips}</div></div>'])

# 5) yapay zeka paneli
yaz(['<div class="sec">Yapay zeka analizi <small>Gemini tarafından üretildi</small></div>'])
llm = llm_yukle()
kayit, not_metni = llm.get("Tümü" if secim == TUM else secim), ""
if secim != TUM and not kayit:
    kayit = llm.get("Tümü")
    not_metni = "Bu pozisyonda ilan sayısı az olduğu için tüm ilanlara dayanan genel analiz gösteriliyor."
yaz([ai_paneli(kayit, not_metni)])

# 6) ilan kartları
yaz(['<div class="sec">İncelenen ilanlar <small>çekilen verilerden örnekler</small></div>'])
kac = st.slider("Gösterilecek ilan sayısı", 3, max(n, 4), min(6, n)) if n > 3 else n
tum_sayac = ao.teknik_say(df_tum)
yaz(['<div class="jobs">'] + [ilan_karti(s, tum_sayac) for _, s in df.head(kac).iterrows()] + ['</div>'])

yaz([f'<div class="foot">Veri: {esc(kaynaklar)} · Python (requests, BeautifulSoup) ile toplandı · Gemini ile analiz edildi.<br>'
     f'Sonuçlar {len(df_tum)} ilanlık küçük bir örnekleme dayanır, sektörün tamamına genelleme yapılmamalıdır.</div>'])