"""
Gemini ile "Sektör Ne Bekliyor?" ve "Kariyer Yol Haritası" metinlerini üretir.
Tüm ilanlar için bir tane, ilan sayısı yeterli olan her pozisyon için ayrı bir tane yazar.
Çıktı: yol_haritasi.json  (app.py bunu gösterir)

Çalıştırma:   python yol_haritasi.py
Yarıda kesilirse tekrar çalıştırın, üretilenler atlanır.
"""
import json
import os
import time

from dotenv import load_dotenv
from google import genai
from google.genai import types

import analiz_ozet

load_dotenv(os.path.join(analiz_ozet.KLASOR, ".env"))

MODEL = "gemini-3.5-flash-lite"   # llm_analysis.py'de çalışan modelin aynısını yazın
CIKTI = os.path.join(analiz_ozet.KLASOR, "yol_haritasi.json")
MIN_ILAN = 5                      # bundan az ilanı olan pozisyon için ayrı analiz üretilmez

client = genai.Client(http_options=types.HttpOptions(timeout=90000))

PROMPT = """Aşağıda "{kapsam}" kapsamındaki {n} adet iş ilanının analizinden çıkan sayılar var.
"teknolojiler" ve "sosyal_beceriler" için sayı = o beceriyi isteyen ilan sayısıdır.

{veri}

Bu verilere dayanarak bilgisayar mühendisliği öğrencisi için Türkçe, SADECE şu biçimde bir JSON döndür:
{{
  "sektor_ne_bekliyor": "2-3 cümlelik özet: bu ilanlarda öne çıkan teknolojiler, dil ve deneyim beklentisi",
  "one_cikanlar": ["3 ila 4 kısa madde, her biri en fazla 12 kelime"],
  "yol_haritasi": [
    {{"donem": "1-2. ay", "baslik": "kısa başlık", "aciklama": "1-2 cümle, somut ve uygulanabilir"}}
  ]
}}

Kurallar:
- "yol_haritasi" tam 4 adım içersin (örn. 1-2. ay, 3-4. ay, 5-6. ay, sonrası).
- Sadece verideki sayılara dayan, veride olmayan istatistik uydurma.
- Örneklem büyüklüğünü metinde tekrar etme.
- Sadece geçerli JSON döndür.
"""


def gecerli_mi(d):
    return (
        isinstance(d, dict)
        and isinstance(d.get("sektor_ne_bekliyor"), str)
        and isinstance(d.get("one_cikanlar"), list)
        and isinstance(d.get("yol_haritasi"), list) and len(d["yol_haritasi"]) >= 3
        and all(isinstance(a, dict) and {"donem", "baslik", "aciklama"} <= set(a) for a in d["yol_haritasi"])
    )


def uret(kapsam, n, veri):
    prompt = PROMPT.format(kapsam=kapsam, n=n, veri=json.dumps(veri, ensure_ascii=False, indent=2))
    for deneme in range(4):
        try:
            cevap = client.models.generate_content(
                model=MODEL, contents=prompt,
                config=types.GenerateContentConfig(response_mime_type="application/json", temperature=0.3),
            )
            d = json.loads(cevap.text)
            if not gecerli_mi(d):
                raise ValueError("Cevap beklenen biçimde değil")
            d["ilan_sayisi"] = n
            return d
        except Exception as e:
            bekle = 20 * (deneme + 1)
            print(f"   Hata ({e.__class__.__name__}): {str(e)[:150]} | {bekle} sn bekleniyor...")
            time.sleep(bekle)
    return None


def main():
    df = analiz_ozet.yukle()
    gruplar = [("Tümü", "tüm pozisyonlar", df)]
    for poz, g in df.groupby("pozisyon"):
        if len(g) >= MIN_ILAN:
            gruplar.append((poz, poz, g))
    gruplar[1:] = sorted(gruplar[1:], key=lambda x: -len(x[2]))

    sonuc = {}
    if os.path.exists(CIKTI):
        with open(CIKTI, encoding="utf-8") as f:
            sonuc = json.load(f)

    for anahtar, kapsam, g in gruplar:
        if anahtar in sonuc:
            print(f"{anahtar}: zaten var, atlandı")
            continue
        print(f"{anahtar} ({len(g)} ilan) üretiliyor...")
        d = uret(kapsam, len(g), analiz_ozet.ozet(g, n=12))
        if d is None:
            print("   Üretilemedi, sonra tekrar çalıştırın.")
            continue
        sonuc[anahtar] = d
        with open(CIKTI, "w", encoding="utf-8") as f:
            json.dump(sonuc, f, ensure_ascii=False, indent=2)
    print(f"\nBitti. {len(sonuc)} analiz {CIKTI} dosyasına yazıldı.")


if __name__ == "__main__":
    main()