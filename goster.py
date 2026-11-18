
import pandas as pd

yol = "ilan_analizi/ilanlar.csv"
df = pd.read_csv(yol, encoding="utf-8-sig")

for _, r in df.iterrows():
    print("*" * 60)
    #print("Arama:", r["arama"] if pd.notna(r["arama"]) else "Belirtilmedi")
    print("Pozisyon:", r["pozisyon"])
    print("Firma:", r["firma"])
    print("Şehir:", r["sehir"])
    print("Çalışma modeli:", r["calisma_modeli"])
    print("Çalışma tipi:", r["calisma_tipi"])
    print("İlan metni:", r["metin"])

