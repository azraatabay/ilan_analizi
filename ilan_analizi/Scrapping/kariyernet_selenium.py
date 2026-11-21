"""
Kariyer.net iş ilanlarını Selenium ile (gerçek bir Chrome tarayıcısıyla) çeker.

kariyernet_veri.py aynı siteyi requests + BeautifulSoup ile çekiyor. Bu betik ikinci yöntemdir:
sayfayı tarayıcıda açar, JavaScript'in yüklenmesini bekler, listeyi kaydırır ve ilan detaylarını
tarayıcıdan okur.

Gerekenler: Google Chrome ve  pip install selenium pandas  (Selenium 4.6+ sürücüyü kendisi indirir)

Çalıştırma (proje ana klasöründen):
    python ilan_analizi/Scrapping/kariyernet_selenium.py --test        # önce 3 ilanla dene
    python ilan_analizi/Scrapping/kariyernet_selenium.py               # tümü
    python ilan_analizi/Scrapping/kariyernet_selenium.py --headless    # pencere açmadan

Çıktı: ilan_analizi/ilanlar_selenium.csv  (hazirla_veri.py bunu otomatik ekler, aynı ilanlar tekrar sayılmaz)
"""
import html
import json
import os
import random
import re
import sys
import time

import pandas as pd
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

SEARCH_URL = "https://www.kariyer.net/is-ilanlari/bilgisayar-muhendisi?pst=313&pkw=bilgisayar%20m%C3%BChendisi"
PAGE_PARAM = "cp"
MAX_PAGES = 3
KART = "div.job-list-card-item"
ACIKLAMA = "div.job-detail-container-description"
# Ana seçici bulunamazsa sırayla denenecek yedekler
ACIKLAMA_ADAYLARI = [ACIKLAMA, "[class*='job-detail-container-description']",
                     "[class*='job-description']", "[class*='description']"]

TEST = "--test" in sys.argv
HEADLESS = "--headless" in sys.argv

KLASOR = os.path.dirname(os.path.abspath(__file__))
OUTPUT = os.path.normpath(os.path.join(KLASOR, "..", "ilanlar_selenium.csv"))

MODEL_KEYWORDS = ["İş Yerinde", "Uzaktan", "Hibrit", "Remote", "Ofiste"]
TYPE_KEYWORDS = ["Tam zamanlı", "Yarı zamanlı", "Stajyer", "Staj", "Part time", "Full time",
                 "Dönemsel", "Freelance", "Sözleşmeli"]


# ---------------------------------------------------------------- saf yardımcılar (tarayıcı gerektirmez)
def gecerli_isim(text):
    """Boş olmayan ve sadece sayıdan oluşmayan bir metin mi?"""
    return bool(text) and not text.strip().replace(".", "").replace(",", "").isdigit()


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


def sehir_bul(cityname, lines):
    if cityname:
        return cityname
    for line in lines:
        if "•" in line:
            return line.split("•")[0].strip()
    return None


def firma_kartta(lines):
    for line in lines[1:4]:
        if gecerli_isim(line) and "•" not in line:
            return line
    return None


def firma_jsonld(parcalar):
    """Sayfadaki JSON-LD (schema.org JobPosting) bloklarından firma adını bulur."""
    for ham in parcalar:
        try:
            data = json.loads(ham or "")
        except (json.JSONDecodeError, TypeError):
            continue
        for item in (data if isinstance(data, list) else [data]):
            if not isinstance(item, dict):
                continue
            org = item.get("hiringOrganization")
            ad = org.get("name") if isinstance(org, dict) else org
            if isinstance(ad, str) and gecerli_isim(ad):
                return ad.strip()
    return None


def kart_bilgisi(url, pozisyon_attr, sehir_attr, lines):
    """Bir ilan kartının görünen satırlarından liste bilgilerini çıkarır."""
    return {
        "url": url,
        "pozisyon": pozisyon_attr or (lines[0] if lines else None),
        "sehir": sehir_bul(sehir_attr, lines),
        "calisma_modeli": model_bul(lines),
        "calisma_tipi": anahtar_bul(lines, TYPE_KEYWORDS),
        "firma_kart": firma_kartta(lines),
    }


# ---------------------------------------------------------------- tarayıcı işleri
def tarayici_ac():
    secenek = Options()
    if HEADLESS:
        secenek.add_argument("--headless=new")
    secenek.add_argument("--window-size=1366,900")
    secenek.add_argument("--lang=tr-TR")
    return webdriver.Chrome(options=secenek)


def liste_ilanlari(driver, url):
    """Bir arama sayfasını açar, kartların yüklenmesini bekler, kaydırır ve kart bilgilerini döndürür."""
    driver.get(url)
    try:
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, KART)))
    except TimeoutException:
        print("   Kart bulunamadı. Sayfa başlığı:", driver.title)
        return []

    onceki = -1
    for _ in range(8):  # geç yüklenen kartlar için aşağı kaydır
        sayi = len(driver.find_elements(By.CSS_SELECTOR, KART))
        if sayi == onceki:
            break
        onceki = sayi
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1.5)

    sonuc = []
    for kart in driver.find_elements(By.CSS_SELECTOR, KART):
        try:
            link = kart.find_element(By.CSS_SELECTOR, "a[href]").get_attribute("href")
        except NoSuchElementException:
            continue
        lines = [l.strip() for l in kart.text.split("\n") if l.strip() and l.strip() != "Sponsorlu İlan"]
        sonuc.append(kart_bilgisi(link, kart.get_attribute("positionname"),
                                  kart.get_attribute("cityname"), lines))
    return sonuc


def jsonld_aciklama(parcalar):
    """JSON-LD (schema.org JobPosting) içindeki 'description' alanını düz metne çevirir."""
    for ham in parcalar:
        try:
            data = json.loads(ham or "")
        except (json.JSONDecodeError, TypeError):
            continue
        for item in (data if isinstance(data, list) else [data]):
            if isinstance(item, dict) and isinstance(item.get("description"), str):
                duz = re.sub(r"<[^>]+>", " ", html.unescape(item["description"]))
                duz = " ".join(duz.split())
                if len(duz) >= 100:
                    return duz
    return None


_debug_yazildi = False


def hata_ayiklama_kaydet(driver, neden):
    """İlk başarısız detay sayfasının ekran görüntüsünü ve HTML'ini kaydeder (sorunu görmek için)."""
    global _debug_yazildi
    if _debug_yazildi:
        return
    _debug_yazildi = True
    klasor = os.path.dirname(OUTPUT)
    try:
        with open(os.path.join(klasor, "selenium_debug.html"), "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        driver.save_screenshot(os.path.join(klasor, "selenium_debug.png"))
    except Exception as e:
        print("   Debug dosyası yazılamadı:", e)
    print(f"   ! {neden}")
    print(f"   ! Sayfa başlığı: {driver.title!r} | adres: {driver.current_url}")
    print(f"   ! HTML uzunluğu: {len(driver.page_source)} karakter. selenium_debug.html ve .png kaydedildi.")


def detay_oku(driver, url):
    """İlan detay sayfasından (metin, firma, kaynak) döndürür. kaynak: metnin nereden alındığı."""
    driver.get(url)
    try:
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, ACIKLAMA)))
    except TimeoutException:
        pass  # yedek yöntemler aşağıda denenecek

    ld = [e.get_attribute("innerHTML") for e in
          driver.find_elements(By.CSS_SELECTOR, 'script[type="application/ld+json"]')]
    firma = firma_jsonld(ld)

    metin, kaynak = "", "yok"
    for secici in ACIKLAMA_ADAYLARI:
        bulunan = driver.find_elements(By.CSS_SELECTOR, secici)
        if bulunan:
            aday = " ".join(bulunan[0].text.split())
            if len(aday) >= 100:
                metin, kaynak = aday, f"css {secici}"
                break
    if not metin:
        aday = jsonld_aciklama(ld)
        if aday:
            metin, kaynak = aday, "jsonld"
    if not metin:
        hata_ayiklama_kaydet(driver, "İlan metni bulunamadı")
        metin = "Bulunamadı"
    return metin, firma, kaynak


def kaydet(satirlar):
    pd.DataFrame(satirlar).to_csv(OUTPUT, index=False, encoding="utf-8-sig")


def main():
    driver = tarayici_ac()
    try:
        kartlar, gorulen = [], set()
        for sayfa in range(1, MAX_PAGES + 1):
            url = SEARCH_URL if sayfa == 1 else f"{SEARCH_URL}&{PAGE_PARAM}={sayfa}"
            bulunan = liste_ilanlari(driver, url)
            print(f"Sayfa {sayfa}: {len(bulunan)} ilan bulundu.")
            if not bulunan:
                break
            for k in bulunan:
                if k["url"] not in gorulen:
                    gorulen.add(k["url"])
                    kartlar.append(k)
            if TEST and len(kartlar) >= 3:
                break
            time.sleep(random.uniform(2, 4))

        if TEST:
            kartlar = kartlar[:3]
        print(f"\nToplam {len(kartlar)} ilanın detayı okunacak.\n")

        sonuclar = []
        for i, k in enumerate(kartlar, 1):
            metin, firma_detay, kaynak = detay_oku(driver, k["url"])
            firma = firma_detay or k["firma_kart"]
            print(f"[{i}/{len(kartlar)}] {k['pozisyon']} | {firma} | {len(metin)} karakter | kaynak: {kaynak}")
            sonuclar.append({
                "pozisyon": k["pozisyon"], "firma": firma, "sehir": k["sehir"],
                "calisma_modeli": k["calisma_modeli"], "calisma_tipi": k["calisma_tipi"],
                "metin": metin, "url": k["url"], "toplayan": "selenium",
            })
            kaydet(sonuclar)  # her ilanda kaydet, yarıda kesilirse kaybolmasın
            time.sleep(random.uniform(2, 4))
        print(f"\nBitti. {len(sonuclar)} ilan {OUTPUT} dosyasına kaydedildi.")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
