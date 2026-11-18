"""
analiz_sonuclari.csv için yardımcı fonksiyonlar.
app.py (arayüz) ve yol_haritasi.py bunları kullanır.

LLM'in ürettiği metinler birbirinden farklı yazılabildiği için
("react", "React.js", "ReactJS" gibi) burada tek isme indirgenip sayılır.
"""
import os
import re
from collections import Counter

import pandas as pd

KLASOR = os.path.dirname(os.path.abspath(__file__))
CSV_YOLU = os.path.join(KLASOR, "analiz_sonuclari.csv")
YOK = "belirtilmemiş"


def norm(s):
    """Eşleştirme için: küçük harf + i/ı/İ/I hepsi 'i'.
    (Türkçe küçük harf dönüşümü 'CI/CD' ve 'GIT' gibi İngilizce kısaltmaları bozduğu için
    iki tarafı da aynı şekilde sadeleştiriyoruz.)"""
    return str(s).replace("İ", "i").replace("ı", "i").lower()


def yukle(yol=CSV_YOLU):
    df = pd.read_csv(yol, encoding="utf-8-sig")
    for kolon in ["teknik_beceriler", "sosyal_beceriler", "yabanci_dil", "deneyim_yili", "seviye"]:
        df[kolon] = df[kolon].fillna(YOK).astype(str)
    return df


# ---------------------------------------------------------------- teknik beceriler
# anahtar: küçük harfli yazım -> gösterilecek isim (liste olabilir)
TEKNIK_ESLEME = {
    # .NET ailesi
    ".net": ".NET", ".net core": ".NET", ".net framework": ".NET", ".net 8+": ".NET",
    "asp.net": ".NET", "asp.net core": ".NET", "asp.net mvc": ".NET", "asp.net webforms": ".NET",
    "asp.net core web api": ".NET", "c#/.net": [".NET", "C#"], "c# / .net": [".NET", "C#"],
    ".net microservices": [".NET", "Mikroservis"], "c#/.net core": [".NET", "C#"],
    "c#": "C#",
    # diller
    "java": "Java", "python": "Python", "php": "PHP", "c++": "C++", "c": "C",
    "javascript": "JavaScript", "js": "JavaScript", "typescript": "TypeScript",
    "html": "HTML", "html5": "HTML", "xhtml": "HTML", "html/xhtml": "HTML",
    "css": "CSS", "css3": "CSS",
    # frontend / backend
    "react": "React", "react.js": "React", "reactjs": "React", "react native": "React Native",
    "vue": "Vue.js", "vue.js": "Vue.js", "angular": "Angular",
    "node.js": "Node.js", "nodejs": "Node.js", "next.js": "Next.js",
    "spring boot": "Spring", "spring framework": "Spring", "spring": "Spring",
    "laravel": "Laravel", "django": "Django",
    # API / mimari
    "rest api": "REST API", "restful api": "REST API", "rest apis": "REST API", "rest": "REST API",
    "rest servisleri": "REST API", "restful": "REST API", "web api": "REST API",
    "web servisleri": "REST API",
    "microservices": "Mikroservis", "mikroservis": "Mikroservis", "microservis": "Mikroservis",
    "mikroservis mimarisi": "Mikroservis", "mikro servisler": "Mikroservis",
    "mikroservis mimarileri": "Mikroservis",
    "design patterns": "Tasarım kalıpları", "tasarım kalıpları": "Tasarım kalıpları",
    "tasarım desenleri": "Tasarım kalıpları", "tasarım kalıpları (design patterns)": "Tasarım kalıpları",
    "nesne yönelimli programlama": "OOP", "nesneye yönelik programlama": "OOP", "oop": "OOP",
    "nesne tabanlı geliştirme": "OOP", "nesne yönelimli tasarım": "OOP",
    "solid": "SOLID", "solid prensipleri": "SOLID", "clean code": "Clean Code",
    # veritabanı
    "sql": "SQL", "sql/tsql": "SQL", "t-sql": "SQL",
    "ms sql": "MSSQL", "mssql": "MSSQL", "ms sql server": "MSSQL", "microsoft sql server": "MSSQL",
    "sql server": "MSSQL", "sql server veri tabanı yönetim sistemi": "MSSQL",
    "postgresql": "PostgreSQL", "mysql": "MySQL", "mongodb": "MongoDB", "oracle": "Oracle",
    "nosql": "NoSQL", "redis": "Redis",
    "ilişkisel veritabanları": "İlişkisel veritabanı", "relational veritabanları": "İlişkisel veritabanı",
    "ilişkisel veri tabanları": "İlişkisel veritabanı", "veritabanı tasarımı": "İlişkisel veritabanı",
    "veri tabanı tasarımı": "İlişkisel veritabanı",
    "entity framework": "Entity Framework", "entity framework core": "Entity Framework",
    "ef core": "Entity Framework", "ef6": "Entity Framework", "orm (ef core)": "Entity Framework",
    "orm araçları": "Entity Framework",
    # araçlar / bulut
    "git": "Git", "github": "Git", "gitlab": "Git", "svn": "SVN",
    "docker": "Docker", "docker compose": "Docker",
    "kubernetes": "Kubernetes", "k8s": "Kubernetes", "aks": "Kubernetes",
    "ci/cd": "CI/CD", "continuous integration": "CI/CD", "devops": "DevOps",
    "azure": "Azure", "azure cloud": "Azure", "microsoft azure": "Azure",
    "azure devops": "Azure DevOps", "tfs": "Azure DevOps",
    "aws": "AWS", "gcp": "Google Cloud", "google cloud": "Google Cloud",
    "rabbitmq": "RabbitMQ", "kafka": "Kafka", "signalr": "SignalR", "linux": "Linux",
    # yapay zeka
    "llm": "Yapay zeka / LLM", "yapay zeka": "Yapay zeka / LLM", "yapay zekâ": "Yapay zeka / LLM",
    "büyük dil modelleri (llm)": "Yapay zeka / LLM", "claude": "Yapay zeka / LLM",
    "github copilot": "Yapay zeka / LLM", "chatgpt": "Yapay zeka / LLM", "cursor": "Yapay zeka / LLM",
    "yapay zeka destekli araçlar": "Yapay zeka / LLM",
    "yapay zekâ destekli araçlar": "Yapay zeka / LLM",
    "yapay zekâ destekli yazılım geliştirme araçları": "Yapay zeka / LLM",
    "yapay zekâ teknolojileri": "Yapay zeka / LLM",
}

TEKNIK_ESLEME = {norm(k): v for k, v in TEKNIK_ESLEME.items()}

# Beceri olmayan, çok genel ifadeler
TEKNIK_GENEL = {
    "yazılım geliştirme", "bilgisayar programları ve sistemleri", "veri tabanı", "backend geliştirme",
    "yazılım geliştirme", "web tabanlı uygulama geliştirme", "web tabanlı uygulamalar", YOK,
}


TEKNIK_GENEL = {norm(k) for k in TEKNIK_GENEL}


def _teknik_adlar(hucre):
    """Bir ilanın teknik beceri hücresini normalize edilmiş isimler kümesine çevirir."""
    sonuc = set()
    for parca in str(hucre).split(","):
        orijinal = parca.strip()
        if not orijinal:
            continue
        anahtar = norm(orijinal)
        if anahtar in TEKNIK_GENEL:
            continue
        if anahtar not in TEKNIK_ESLEME:
            parantezsiz = re.sub(r"\s*\(.*?\)", "", anahtar).strip()
            anahtar = parantezsiz if parantezsiz in TEKNIK_ESLEME else anahtar
        karsilik = TEKNIK_ESLEME.get(anahtar, orijinal)
        if isinstance(karsilik, list):
            sonuc.update(karsilik)
        else:
            sonuc.add(karsilik)
    return sonuc


teknik_adlar = _teknik_adlar   # dışarıdan kullanım için açık isim


def teknik_say(df):
    """{beceri: kaç ilanda geçti} (bir ilanda iki kez sayılmaz)."""
    sayac = Counter()
    for hucre in df["teknik_beceriler"]:
        sayac.update(_teknik_adlar(hucre))
    return sayac


# ---------------------------------------------------------------- sosyal beceriler
SOSYAL_KATEGORILER = {
    "Takım çalışması / iş birliği": ["takım", "ekip çal", "ekip arkadaş", "ekibi", "ekiple", "ekipler", "ekip içi",
                                     "ekip yönet", "iş birliği", "işbirliği", "koordinasyon", "ekip"],
    "İletişim": ["iletişim"],
    "Analitik düşünme": ["analitik", "analiz", "mantıksal"],
    "Problem çözme": ["problem", "sorun", "çözüm"],
    "Öğrenmeye / gelişime açıklık": ["öğren", "gelişim", "geliştirmeye", "yenilik", "yeni teknoloji",
                                     "yeniliklere", "değişime"],
    "Sorumluluk alma": ["sorumluluk", "sorumlu", "sahiplen", "owning"],
    "Sonuç / hedef odaklılık": ["sonuç", "hedef", "performans"],
    "Müşteri odaklılık": ["müşteri"],
    "Araştırmacılık": ["araştır"],
    "Dokümantasyon / raporlama": ["dokümantasyon", "raporlama", "raporlayabilen"],
    "Proje / zaman yönetimi": ["proje yönetimi", "zaman", "iş takibi", "planlama", "disiplin"],
    "Liderlik / mentorluk": ["liderlik", "mentor", "ekip yönet"],
}


def sosyal_kategoriler(hucre):
    metin = norm(hucre)
    if metin.strip() in ("", norm(YOK)):
        return set()
    return {ad for ad, anahtarlar in SOSYAL_KATEGORILER.items() if any(norm(a) in metin for a in anahtarlar)}


def sosyal_say(df):
    sayac = Counter()
    for hucre in df["sosyal_beceriler"]:
        sayac.update(sosyal_kategoriler(hucre))
    return sayac


# ---------------------------------------------------------------- yabancı dil
def dil_listesi(hucre):
    metin = norm(hucre)
    diller = []
    for ad, anahtar in [("İngilizce", "ingilizce"), ("Almanca", "almanca"), ("Fransızca", "fransizca")]:
        if anahtar in metin:
            diller.append(ad)
    return diller


def dil_seviyesi(hucre):
    """İngilizce seviyesini 4 gruptan birine indirger."""
    metin = norm(hucre)
    if "ingilizce" not in metin:
        return None
    if any(a in metin for a in ["ileri", "b2", "advanced"]):
        return "İleri"
    if "orta" in metin:
        return "Orta"
    if "iyi" in metin:
        return "İyi"
    if any(a in metin for a in ["teknik", "literatür", "dokümantasyon"]):
        return "Teknik doküman okuyabilme"
    return "Seviye belirtilmemiş"


def dil_say(df):
    """(dil sayacı, ingilizce seviye sayacı, dil istenmeyen ilan sayısı)"""
    diller, seviyeler, istenmeyen = Counter(), Counter(), 0
    for hucre in df["yabanci_dil"]:
        d = dil_listesi(hucre)
        if not d:
            istenmeyen += 1
            continue
        diller.update(d)
        sev = dil_seviyesi(hucre)
        if sev:
            seviyeler[sev] += 1
    return diller, seviyeler, istenmeyen


# ---------------------------------------------------------------- deneyim / seviye
SEVIYE_ADLARI = {"intern": "Stajyer", "junior": "Junior", "mid": "Mid", "senior": "Senior", YOK: "Belirtilmemiş"}
SEVIYE_SIRASI = ["Stajyer", "Junior", "Mid", "Senior", "Belirtilmemiş"]


def seviye_say(df):
    sayac = Counter(SEVIYE_ADLARI.get(norm(s).strip(), "Belirtilmemiş") for s in df["seviye"])
    return {ad: sayac.get(ad, 0) for ad in SEVIYE_SIRASI}


def min_deneyim(hucre):
    """'2-5 yıl' -> 2, 'en az 5 yıl' -> 5, 'belirtilmemiş' -> None"""
    m = re.search(r"\d+", str(hucre))
    return int(m.group()) if m else None


def medyan_deneyim(df):
    degerler = [d for d in (min_deneyim(h) for h in df["deneyim_yili"]) if d is not None]
    return (float(pd.Series(degerler).median()), len(degerler)) if degerler else (None, 0)


# ---------------------------------------------------------------- özet (yol haritası için)
def ozet(df, n=15):
    """Tüm analizi tek sözlükte toplar."""
    diller, ing_seviye, dil_yok = dil_say(df)
    medyan, medyan_n = medyan_deneyim(df)
    return {
        "ilan_sayisi": len(df),
        "teknolojiler": dict(teknik_say(df).most_common(n)),
        "sosyal_beceriler": dict(sosyal_say(df).most_common(n)),
        "diller": dict(diller),
        "ingilizce_seviye": dict(ing_seviye),
        "dil_istemeyen_ilan": dil_yok,
        "seviye_dagilimi": seviye_say(df),
        "medyan_min_deneyim_yil": medyan,
        "deneyim_belirten_ilan": medyan_n,
    }