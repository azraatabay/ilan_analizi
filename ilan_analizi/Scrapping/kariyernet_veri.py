import json
import time
import pandas as pd
import requests
from bs4 import BeautifulSoup

BASE = "https://www.kariyer.net"
SEARCH_URL = "https://www.kariyer.net/is-ilanlari/bilgisayar-muhendisi?pst=313&pkw=bilgisayar%20m%C3%BChendisi"
PAGE_PARAM = "cp"      # 2. sayfaya geçince URL'ye bakıp doğrulayın
MAX_PAGES = 3          # önce 1 ile test edin, sonra artırın
OUTPUT = "ilanlar.csv"
headers = {"User-Agent": "Mozilla/5.0"}

MODEL_KEYWORDS = ["İş Yerinde", "Uzaktan", "Hibrit", "Remote", "Ofiste"]
TYPE_KEYWORDS = ["Tam zamanlı", "Yarı zamanlı", "Stajyer", "Staj", "Part time", "Full time",
                 "Dönemsel", "Freelance", "Sözleşmeli"]


def gecerli_isim(text):
    """Sayı olmayan, boş olmayan bir metin mi?"""
    return bool(text) and not text.strip().replace(".", "").replace(",", "").isdigit()


def firma_detaydan(detail_soup):
    # 1) JSON-LD (schema.org JobPosting -> hiringOrganization.name)
    for s in detail_soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(s.string or "")
        except (json.JSONDecodeError, TypeError):
            continue
        items = data if isinstance(data, list) else [data]
        for item in items:
            if not isinstance(item, dict):
                continue
            org = item.get("hiringOrganization")
            name = org.get("name") if isinstance(org, dict) else org
            if isinstance(name, str) and gecerli_isim(name):
                return name.strip()
    # 2) Class adında company geçen etiket
    for tag in detail_soup.find_all(class_=lambda c: c and "company" in c.lower()):
        text = tag.get_text(" ", strip=True)
        if gecerli_isim(text) and len(text) < 100:
            return text
    return None


def firma_kartta(card, lines):
    # Başlıktan sonraki, sayı olmayan ilk uygun satır
    for line in lines[1:4]:
        if gecerli_isim(line) and "•" not in line:
            return line
    tag = card.find(class_=lambda c: c and "company" in c.lower())
    if tag and gecerli_isim(tag.get_text(strip=True)):
        return tag.get_text(strip=True)
    return None


def satirlar(card):
    lines = [l.strip() for l in card.get_text("\n").split("\n") if l.strip()]
    return [l for l in lines if l != "Sponsorlu İlan"]


def anahtar_bul(lines, keywords):
    for line in lines:
        for k in keywords:
            if k.lower() in line.lower():
                return k
    return None


def model_bul(lines):
    for line in lines:
        if "•" in line:
            parts = [p.strip() for p in line.split("•")]
            if len(parts) > 1 and parts[1]:
                return parts[1]
    return anahtar_bul(lines, MODEL_KEYWORDS)


def sehir_bul(card, lines):
    city = card.get("cityname")
    if city:
        return city
    for line in lines:
        if "•" in line:
            return line.split("•")[0].strip()
    return None


def ilan_kartlari(url):
    resp = requests.get(url, headers=headers, timeout=15)
    soup = BeautifulSoup(resp.text, "html.parser")
    cards = soup.find_all("div", class_="job-list-card-item")
    if not cards:
        print("DURUM KODU:", resp.status_code)
        print("SAYFA BAŞLIĞI:", soup.title.get_text(strip=True) if soup.title else None)
        print("İLK 300 KARAKTER:", resp.text[:300].replace("\n", " "))
    return cards


sonuclar = []
gorulen = set()

for sayfa in range(1, MAX_PAGES + 1):
    url = SEARCH_URL if sayfa == 1 else f"{SEARCH_URL}&{PAGE_PARAM}={sayfa}"
    job_cards = ilan_kartlari(url)
    print(f"Sayfa {sayfa}: {len(job_cards)} ilan bulundu.\n")
    if not job_cards:
        break

    if sayfa == 1:
        print("İlk kartın öznitelikleri:", job_cards[0].attrs)
        print("İlk kartın metin satırları:", satirlar(job_cards[0]), "\n")

    for card in job_cards:
        link_tag = card.find("a", href=True)
        if not link_tag:
            continue
        href = link_tag["href"]
        detail_url = href if href.startswith("http") else BASE + href
        if detail_url in gorulen:
            continue
        gorulen.add(detail_url)

        lines = satirlar(card)
        position = card.get("positionname") or (lines[0] if lines else None)
        city = sehir_bul(card, lines)
        model = model_bul(lines)
        tip = anahtar_bul(lines, TYPE_KEYWORDS)

        detail_resp = requests.get(detail_url, headers=headers, timeout=15)
        detail_soup = BeautifulSoup(detail_resp.text, "html.parser")
        desc_div = detail_soup.find("div", class_="job-detail-container-description")
        requirements = desc_div.get_text(" ", strip=True) if desc_div else "Bulunamadı"

        # Firma adı: önce detay sayfası, olmazsa kart
        company = firma_detaydan(detail_soup) or firma_kartta(card, lines)

        print(f"Pozisyon: {position}")
        print(f"Firma adı : {company}")
        print(f"Şehir: {city} | Model: {model} | Tip: {tip}")
        print(f"Firmanın beklentileri ve istenen yetkinlikler : {requirements[:300]}...")
        print("-" * 50)

        sonuclar.append({
            "pozisyon": position,
            "firma": company,
            "sehir": city,
            "calisma_modeli": model,
            "calisma_tipi": tip,
            "metin": requirements,
        })

        pd.DataFrame(sonuclar).to_csv(OUTPUT, index=False, encoding="utf-8-sig")
        time.sleep(2)
    time.sleep(3)

print(f"\nBitti. {len(sonuclar)} ilan {OUTPUT} dosyasına kaydedildi.")