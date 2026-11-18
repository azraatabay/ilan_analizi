import os
import json
import time
import hashlib
import pandas as pd
from dotenv import load_dotenv
from google import genai
from google.genai import types

KLASOR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(KLASOR, ".env"))

GIRDI = os.path.join(KLASOR, "ilanlar_son.csv")
CIKTI = os.path.join(KLASOR, "analiz_sonuclari.csv")
CACHE = os.path.join(KLASOR, "llm_cache.json")
MODEL = "gemini-3.5-flash-lite"
TEST_N = None          # önce 3 ilan; hepsini çalıştırmak için None yapın
BEKLEME = 4         # istekler arası saniye

client = genai.Client(http_options=types.HttpOptions(timeout=60000))

PROMPT = """
Aşağıdaki iş ilanını analiz et ve şu alanları JSON olarak döndür:
pozisyon, firma, seviye, deneyim_yili, teknik_beceriler, yabanci_dil, sosyal_beceriler

Kurallar:
- Metinde bilgi yoksa "belirtilmemiş" yaz, null veya boş bırakma.
- Sadece geçerli JSON döndür.

{{
  "seviye": "intern | junior | mid | senior | belirtilmemiş",
  "teknik_beceriler": ["..."],
  "yabanci_dil": "ör. İngilizce - iyi seviye veya belirtilmemiş",
  "sosyal_beceriler": ["..."],
  "deneyim_yili": "ör. 0-2 veya belirtilmemiş"
}}

İLAN METNİ:
{metin}
"""


def json_ayikla(text):
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`").replace("json", "", 1).strip()
    return json.loads(text)


def analiz_et(metin):
    prompt = PROMPT.format(metin=metin[:6000])
    for deneme in range(3):
        try:
            cevap = client.models.generate_content(
                model=MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0,
                ),
            )
            return json_ayikla(cevap.text)
        except Exception as e:
            bekle = 20 * (deneme + 1)
            print(f"   Hata ({e.__class__.__name__}): {str(e)[:150]} | {bekle} sn bekleniyor...")
            time.sleep(bekle)
    return None


df = pd.read_csv(GIRDI, encoding="utf-8-sig")
df = df[df["metin"].notna() & (df["metin"] != "Bulunamadı")].reset_index(drop=True)
if TEST_N:
    df = df.head(TEST_N)

if os.path.exists(CACHE):
    with open(CACHE, encoding="utf-8") as f:
        cache = json.load(f)
else:
    cache = {}

sonuclar = []
for i, satir in df.iterrows():
    anahtar = hashlib.md5(str(satir["metin"]).encode("utf-8")).hexdigest()
    if anahtar in cache:
        sonuc = cache[anahtar]
        print(f"[{i+1}/{len(df)}] cache'ten alındı")
    else:
        print(f"[{i+1}/{len(df)}] {satir.get('pozisyon')} | {satir.get('firma')}")
        sonuc = analiz_et(str(satir["metin"]))
        if sonuc is None:
            print("   Atlandı.")
            continue
        cache[anahtar] = sonuc
        with open(CACHE, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
        time.sleep(BEKLEME)

    sonuclar.append({
        **satir.to_dict(),
        "seviye": sonuc.get("seviye"),
        "teknik_beceriler": ", ".join(sonuc.get("teknik_beceriler") or []),
        "yabanci_dil": sonuc.get("yabanci_dil"),
        "sosyal_beceriler": ", ".join(sonuc.get("sosyal_beceriler") or []),
        "deneyim_yili": sonuc.get("deneyim_yili"),
    })

pd.DataFrame(sonuclar).to_csv(CIKTI, index=False, encoding="utf-8-sig")
print(f"\nBitti. {len(sonuclar)} ilan {CIKTI} dosyasına kaydedildi.")