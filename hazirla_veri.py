import os
import pandas as pd

KLASOR = os.path.dirname(os.path.abspath(__file__))
GIRDI = os.path.join(KLASOR, "ilan_analizi", "ilanlar.csv")
CIKTI = os.path.join(KLASOR, "ilanlar_son.csv")
HARIC_POZISYON = ["Bilgisayar Montaj Elemanı", "Test Mühendisi"]
MIN_METIN_UZUNLUK = 100   # bundan kısa ilan metinleri analiz için yetersiz sayılır


# ---------- 1) Dosyayı oku (virgül ya da noktalı virgül ayracı) ----------
df = None
for sep in [",", ";"]:
    try:
        d = pd.read_csv(GIRDI, sep=sep, encoding="utf-8-sig")
    except (pd.errors.ParserError, UnicodeDecodeError):
        continue
    if "metin" in d.columns:
        df = d
        break
if df is None:
    raise SystemExit("Dosya okunamadı veya 'metin' sütunu yok.")

print("Başlangıç:", len(df), "satır")

# ---------- 2) Sütunları düzenle ----------
# Eski 'kaynak' sütunu veriyi toplayan kişiyi tutuyorsa 'toplayan' olur
if "toplayan" not in df.columns:
    if "kaynak" in df.columns:
        df = df.rename(columns={"kaynak": "toplayan"})
    else:
        df["toplayan"] = "belirtilmemiş"
df["kaynak"] = "Kariyer.net"
df = df.drop(columns=[c for c in ["arama"] if c in df.columns])

# ---------- 3) Metni olmayan / çok kısa ilanları çıkar ----------
onceki = len(df)
df = df[df["metin"].notna() & (df["metin"] != "Bulunamadı")].copy()
df["metin"] = df["metin"].astype(str).apply(lambda t: " ".join(t.split()))
df = df[df["metin"].str.len() >= MIN_METIN_UZUNLUK]
print(f"Metni eksik/kısa olduğu için çıkarılan: {onceki - len(df)}")

# ---------- 4) Tekrarları sil ----------
onceki = len(df)
if "url" in df.columns:
    df = df.drop_duplicates(subset=["url"])
df = df.drop_duplicates(subset=["metin"])
print(f"Tekrar olduğu için çıkarılan: {onceki - len(df)}")

# ---------- 5) İstenmeyen pozisyonları çıkar (büyük/küçük harf farkı önemsiz) ----------
haric_set = {p.strip().lower() for p in HARIC_POZISYON}
haric = df["pozisyon"].astype(str).str.strip().str.lower().isin(haric_set)
print("Çıkarılan pozisyonlar:")
print(df.loc[haric, ["pozisyon", "firma"]].to_string() if haric.any() else "  (yok)")
df = df[~haric].reset_index(drop=True)

# ---------- 6) Kaydet ----------
df.insert(0, "id", range(1, len(df) + 1))
kolonlar = ["id", "kaynak", "pozisyon", "firma", "sehir", "calisma_modeli",
            "calisma_tipi", "metin", "toplayan"]
if "url" in df.columns:
    kolonlar.append("url")     # kaynak göstermek ve kontrol için saklanır
df = df[kolonlar]
df.to_csv(CIKTI, index=False, encoding="utf-8-sig")
print(f"\nKaydedildi: {len(df)} ilan -> {CIKTI}")