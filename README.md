# Kariyer Yetkinlik Analiz Sistemi

Bilgisayar ve yazılım mühendisliği iş ilanlarını web scraping ile toplayıp, ilan metinlerinden teknik
yetkinlik, yabancı dil ve sosyal beceri beklentilerini büyük dil modeli (Gemini) ile çıkaran ve sonucu
interaktif bir panelde (Streamlit) gösteren proje. Yapay Zekaya Giriş dersi final ödevi olarak hazırlandı.

## Ne yapar?

1. **Veri toplar:** Kariyer.net'ten bilgisayar/yazılım mühendisliği ilanlarını `requests` + BeautifulSoup ile çeker
   (pozisyon, firma, şehir, çalışma modeli, ilan metni). Selenium ile de denendi, aşağıdaki "Yöntem" bölümüne bakın.
2. **Veriyi temizler:** Metni boş veya çok kısa ilanları, tekrar eden ilanları ve konu dışı pozisyonları çıkarır.
3. **LLM ile analiz eder:** Her ilanı Gemini'ye okutup seviye, deneyim yılı, teknik beceriler, yabancı dil ve
   sosyal becerileri JSON olarak çıkarır.
4. **Yol haritası üretir:** Tüm ilanlar ve ilan sayısı yeterli olan her pozisyon için sayılardan "Sektör ne
   bekliyor?" özeti ve kariyer yol haritası yazar.
5. **Gösterir:** Pozisyon seçilebilen, KPI kartları, yüzdeli ilerleme çubukları ve ilan kartları olan bir panel.

## Klasör yapısı

```
├── ilan_analizi/
│   ├── Scrapping/kariyernet_veri.py   # Kariyer.net scraper (requests + BeautifulSoup)
│   ├── Scrapping/kariyernet_selenium.py  # Selenium denemesi (liste okunur, detay sayfasını site engeller)
│   └── ilanlar.csv                    # Ham ilan verisi (requests + BeautifulSoup)
├── hazirla_veri.py                    # Temizleme: ilanlar.csv -> ilanlar_son.csv
├── ilanlar_son.csv                    # Temizlenmiş ilanlar
├── llm_analysis.py                    # Gemini ile ilan analizi -> analiz_sonuclari.csv
├── analiz_sonuclari.csv               # Her ilan için LLM çıktısı
├── analiz_ozet.py                     # Becerileri sayma ve aynı beceriyi tek isimde toplama
├── yol_haritasi.py                    # Gemini ile yol haritası -> yol_haritasi.json
├── yol_haritasi.json                  # Üretilmiş yol haritası metinleri
├── app.py                             # Streamlit paneli
└── .streamlit/config.toml             # Panel teması
```

## Kurulum

Python 3.10 veya üzeri gerekir.

```
python -m venv .venv
.venv\Scripts\activate          # Windows (Mac/Linux: source .venv/bin/activate)
pip install -r requirements.txt
```

Gemini'yi çağıran adımlar (`llm_analysis.py`, `yol_haritasi.py`) için proje klasöründe `.env` dosyası oluşturun:

```
GEMINI_API_KEY=buraya_kendi_anahtariniz
```

Anahtarı https://aistudio.google.com adresinden alabilirsiniz. `.env` dosyası `.gitignore`'dadır, GitHub'a gönderilmez.

## Çalıştırma

Hazır sonuç dosyaları depoda olduğu için paneli doğrudan açabilirsiniz:

```
streamlit run app.py
```

Tüm hattı baştan çalıştırmak için sırayla:

```
python ilan_analizi/Scrapping/kariyernet_veri.py        # 1a) ilan çek: requests + BeautifulSoup (siteye bağlı)
python hazirla_veri.py                              # 2) temizle
# (İsteğe bağlı) Selenium denemesi: python ilan_analizi/Scrapping/kariyernet_selenium.py --test
# Kariyer.net detay sayfalarında bot koruması devreye girdiği için ilan metni bu yolla alınamadı.
python llm_analysis.py                              # 3) LLM analizi (TEST_N = None olmalı)
python yol_haritasi.py                              # 4) yol haritası
streamlit run app.py                                # 5) panel
```

Notlar:
- `llm_analysis.py` içinde `TEST_N = 3` varsa yalnızca ilk 3 ilan analiz edilir, hepsi için `None` yapın.
- `llm_analysis.py` ve `yol_haritasi.py` içindeki `MODEL` satırı Google'ın güncel model adıyla uyumlu olmalıdır.
  Model adları sık değişir, hesabınızdaki adlar `genai.Client().models.list()` ile listelenebilir.
- Aynı ilan tekrar analiz edilmez, sonuçlar `llm_cache.json` içinde saklanır. Kesilen çalıştırma kaldığı yerden devam eder.

## Yöntem

- **Kaynak:** Kariyer.net, "bilgisayar mühendisi" araması. Önce `requests` + BeautifulSoup ile 49 ilan çekildi,
  temizlik sonrası **43 ilan** kaldı.
- **Selenium denemesi:** Aynı arama gerçek bir Chrome tarayıcısıyla (Selenium) da denendi. Arama sonuç sayfası
  okunabildi (ilk sayfada 28 ilan kartı), ancak ilan detay sayfalarında site "Access to this page has been denied"
  (bot koruması) yanıtı verdi, bu yüzden Selenium ile ilan metni alınamadı. Korumayı aşmaya çalışılmadı. Analizde
  kullanılan ilan metinleri `requests` + BeautifulSoup ile toplanan veridir. `hazirla_veri.py`, varsa
  `ilanlar_selenium.csv` dosyasını da ekleyecek şekilde yazılmıştır (tekrarları atar), ancak bu veri sete girmemiştir.
- **Temizlik:** Metni olmayan veya 100 karakterden kısa ilanlar, aynı metne sahip tekrarlar ve "Bilgisayar Montaj
  Elemanı", "Test Mühendisi" pozisyonları çıkarıldı.
- **LLM analizi:** Her ilan için Gemini'den sabit bir JSON şeması istenir (`temperature=0`).
- **Beceri sayımı:** LLM aynı beceriyi farklı yazabildiği için (örn. "GIT", "Git", "GitHub") `analiz_ozet.py`
  eşleme tablosuyla tek isimde toplar. Bir beceri aynı ilanda kaç kez geçerse geçsin bir sayılır.
  Panelde gösterilen yüzde, becerinin geçtiği ilan sayısının seçili ilan sayısına oranıdır.
- **Sosyal beceriler:** Serbest metin olduğu için benzer ifadeler anahtar kelimelerle gruplanır
  ("ekip çalışması", "takım oyuncusu" gibi).

## Sınırlılıklar

- Veri tek kaynaktan ve yalnızca 43 ilandan oluşur. Sonuçlar sektörün tamamını temsil etmez, bir pozisyonda
  ilan sayısı azaldıkça yüzdeler daha az güvenilirdir.
- Beceriler bir dil modeli tarafından çıkarıldığı için hata ve eksik içerebilir. Çıkarımlar ilan metniyle tek tek
  doğrulanmamıştır.
- Yol haritası metinleri de Gemini tarafından üretilmiştir, yalnızca verilen sayılara dayanması istenmiştir ancak
  bir kişi tarafından gözden geçirilmelidir.
- Scraper site yapısına bağlıdır. Kariyer.net sayfa yapısını veya erişim kurallarını değiştirirse çalışmayabilir.

## Hazırlayanlar

Azra ve Ceren, Yapay Zekaya Giriş dersi final projesi.
