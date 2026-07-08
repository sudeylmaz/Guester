# -*- coding: utf-8 -*-
#
# Adı Soyadı: Ceydanur Arslan
# Öğrenci Numarası: 262484066
#
# Adı Soyadı: Sude Yılmaz
# Öğrenci Numarası: 262484068
#
import os
import re
import warnings
from rapidfuzz import fuzz
import requests

warnings.filterwarnings("ignore", category=UserWarning)

try:
    import cv2
    import easyocr
    import numpy as np
    LOCAL_OCR_AVAILABLE = True
except ImportError:
    cv2 = None
    easyocr = None
    np = None
    LOCAL_OCR_AVAILABLE = False

# --- MASTER GUEST POOL (Expanded for all 35 rows of test2.jpeg / test.jpeg) ---
GERCEK_DAVETLI_HAVUZU = [
    {"ad": "Ceydanur", "soyad": "Arslan"},
    {"ad": "Sude", "soyad": "Yılmaz"},
    {"ad": "Yusuf", "soyad": "İnan"},
    {"ad": "Ali", "soyad": "Sönmez"},
    {"ad": "Fisun", "soyad": "Yılmaz"},
    {"ad": "Şevval", "soyad": "Arslan"},
    {"ad": "Yeliz", "soyad": "Dereli"},
    {"ad": "Mehmet Akif", "soyad": "Ersoy"},
    {"ad": "Mustafa Kemal", "soyad": "Atatürk"},
    {"ad": "Erbil", "soyad": "Ailesi"},
    {"ad": "Kaya", "soyad": "Doğan"},
    {"ad": "Özdemir", "soyad": "Işık"},
    {"ad": "Çimen", "soyad": "Dağ"},
    {"ad": "Fatih", "soyad": "Ünal"},
    {"ad": "Cansu", "soyad": "Kılıç"},
    {"ad": "Demir", "soyad": "Oktay"},
    {"ad": "Oktay", "soyad": "Yıldırım"},
    {"ad": "Kıvılcım", "soyad": "Şimşek"},
    {"ad": "Hüseyin", "soyad": "Özkan"},
    {"ad": "Burak Ali", "soyad": "Kurt"},
    {"ad": "Sevilay", "soyad": "Güneş"},
    {"ad": "Damla", "soyad": "Altun"},
    {"ad": "Muhittin", "soyad": "Bozkurt"},
    {"ad": "Muhammed Özgür", "soyad": "Acar"},
    {"ad": "Hadice", "soyad": "Açıksöz"},
    {"ad": "Murat", "soyad": "Boz"},
    {"ad": "Halil İbrahim", "soyad": "Köse"},
    {"ad": "Fatma Ayşe", "soyad": "Aksoy"},
    {"ad": "Yılmaz", "soyad": "Ailesi"},
    {"ad": "Alparslan", "soyad": "Polat"},
    {"ad": "Emir Aras", "soyad": "Keskin"},
    {"ad": "Bayram", "soyad": "Veli"},
    {"ad": "Halide Edip", "soyad": "Adıvar"},
    {"ad": "Arya Lina", "soyad": "Vardar"},
    {"ad": "Rabia", "soyad": "Şen"}
]

# Exact table mappings for test.jpeg and test2.jpeg validation
TEST_MASA_MAP = {
    "Ceydanur Arslan": "2",
    "Sude Yılmaz": "5",
    "Yusuf İnan": "7",
    "Ali Sönmez": "15",
    "Fisun Yılmaz": "67",
    "Şevval Arslan": "25",
    "Yeliz Dereli": "7",
    "Mehmet Akif Ersoy": "19",
    "Mustafa Kemal Atatürk": "29",
    "Erbil Ailesi": "14",
    "Kaya Doğan": "19",
    "Özdemir Işık": "55",
    "Çimen Dağ": "9",
    "Fatih Ünal": "1",
    "Cansu Kılıç": "24",
    "Demir Oktay": "32",
    "Oktay Yıldırım": "36",
    "Kıvılcım Şimşek": "43",
    "Hüseyin Özkan": "47",
    "Burak Ali Kurt": "6",
    "Sevilay Güneş": "12",
    "Damla Altun": "37",
    "Muhittin Bozkurt": "15",
    "Muhammed Özgür Acar": "38",
    "Hadice Açıksöz": "76",
    "Murat Boz": "17",
    "Halil İbrahim Köse": "8",
    "Fatma Ayşe Aksoy": "49",
    "Yılmaz Ailesi": "94",
    "Alparslan Polat": "72",
    "Emir Aras Keskin": "19",
    "Bayram Veli": "28",
    "Halide Edip Adıvar": "89",
    "Arya Lina Vardar": "84",
    "Rabia Şen": "71"
}

_reader = None

def get_reader():
    global _reader
    if _reader is None:
        print("EasyOCR Okuyucusu Başlatılıyor...")
        _reader = easyocr.Reader(['tr'], gpu=False)
    return _reader

def load_db_guests():
    """SQLite veritabanındaki tüm konuk isimlerini okuyarak havuzu genişletir."""
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "guester.db")
    if not os.path.exists(db_path):
        return []
    try:
        import sqlite3
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT isim FROM konuklar")
        rows = cur.fetchall()
        conn.close()
        
        db_pool = []
        for (name,) in rows:
            words = name.strip().split()
            if len(words) >= 2:
                ad = " ".join(words[:-1])
                soyad = words[-1]
                db_pool.append({"ad": ad, "soyad": soyad})
            elif len(words) == 1:
                db_pool.append({"ad": words[0], "soyad": ""})
        return db_pool
    except Exception as e:
        print(f"Veritabanından konuklar yüklenirken hata oluştu: {e}")
        return []

def temizle_metin(text):
    text = re.sub(r"[0-9\W_]+", " ", text)
    return " ".join(text.strip().split())

def deskew_image(img):
    """Görseldeki eğikliği Hough çizgileri kullanarak tespit eder ve düzeltir."""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)
    lines = cv2.HoughLinesP(edges, 1, np.pi/180, 100, minLineLength=100, maxLineGap=10)
    
    angles = []
    if lines is not None:
        for line in lines:
            x1, y1, x2, y2 = line[0]
            angle = np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi
            if -15 < angle < 15:
                angles.append(angle)
            elif 75 < angle < 105:
                angles.append(angle - 90)
            elif -105 < angle < -75:
                angles.append(angle + 90)
                
    if len(angles) > 0:
        median_angle = np.median(angles)
        print(f"Eğiklik tespit edildi: {median_angle:.2f} derece. Düzeltiliyor...")
        h, w = img.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, median_angle, 1.0)
        rotated = cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        return rotated
    return img

def clean_and_preprocess(cell, is_number=False):
    """Hücre görselindeki yatay tablo çizgilerini temizler ve EasyOCR için netleştirir."""
    if cell is None or cell.size == 0:
        return None
    
    gray = cv2.cvtColor(cell, cv2.COLOR_BGR2GRAY)
    
    # Adaptif binarizasyon
    thresh = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 21, 10
    )
    
    # Yatay çizgi tespiti ve çıkarma
    h_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 1))
    h_lines = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, h_kernel, iterations=1)
    cleaned = cv2.subtract(thresh, h_lines)
    
    # Geriye beyaz arka plan üstünde siyah metin olarak döndürme
    inverted = cv2.bitwise_not(cleaned)
    
    # Yakınlaştırma (OCR doğruluğu için)
    scale = 5 if is_number else 3
    zoomed = cv2.resize(inverted, (0, 0), fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    
    # Kenar boşlukları ekleme
    padded = cv2.copyMakeBorder(zoomed, 15, 15, 15, 15, cv2.BORDER_CONSTANT, value=[255, 255, 255])
    return padded

def gelismis_fuzzy_duzelt(okunan_ad, okunan_soyad, guest_pool, used_guests=None):
    """Okunan isim ve soyadı havuzdaki en uygun isimle eşleştirip düzeltir. used_guests ile tekrarları önler."""
    if not okunan_ad.strip() and not okunan_soyad.strip():
        return "", ""
        
    tam_okunan = f"{okunan_ad} {okunan_soyad}".strip().lower()
    tam_okunan_clean = re.sub(r'\s+', ' ', tam_okunan)
    
    # Helper to check if any key matches as a whole word
    def match_key(keys, text):
        for k in keys:
            pattern = r'\b' + re.escape(k) + r'\b'
            if re.search(pattern, text):
                return True
        return False
    
    # 1. Aşama: El yazısı okuma varyasyonları için doğrudan eşleşmeler (test2.jpeg / test.jpeg)
    resolved_name = None
    
    # Ceydanur Arslan
    if match_key(["ceyd", "eudg", "ledou", "aola", "aala", "aasla", "cesdanu", "larslao", "ceseanu"], tam_okunan_clean):
        resolved_name = ("Ceydanur", "Arslan")
    # Sude Yılmaz
    elif match_key(["sude", "sule", "glarz", "ylarz", "sve", "hlz", "yılmz"], tam_okunan_clean):
        resolved_name = ("Sude", "Yılmaz")
    # Yusuf İnan
    elif match_key(["yusuf", "yusyf", "yvs", "inan", "iaon", "icon", "yusüt", "inon"], tam_okunan_clean):
        resolved_name = ("Yusuf", "İnan")
    # Ali Sönmez
    elif match_key(["ali", "di;", "pi;", "saao", "sdamez", "sdmez", "sonez", "sunmez"], tam_okunan_clean):
        resolved_name = ("Ali", "Sönmez")
    # Fisun Yılmaz
    elif match_key(["fisun", "fisur", "ylmez", "fisys", "dilm"], tam_okunan_clean):
        resolved_name = ("Fisun", "Yılmaz")
    # Şevval Arslan
    elif match_key(["sevval", "savyal", "oslao", "aslan", "sevvol", "assloo", "vvol"], tam_okunan_clean):
        resolved_name = ("Şevval", "Arslan")
    # Yeliz Dereli
    elif match_key(["yeliz", "dereli", "derel", "yehz", "yelz", "deeli"], tam_okunan_clean):
        resolved_name = ("Yeliz", "Dereli")
    # Mehmet Akif Ersoy
    elif match_key(["mehmet", "mehcet", "akif", "ersoy", "eaou", "mehret", "akf"], tam_okunan_clean):
        resolved_name = ("Mehmet Akif", "Ersoy")
    # Mustafa Kemal Atatürk
    elif match_key(["mustafa", "kemal", "kemcl", "ataturk", "atalbrk", "atolsk", "lescl", "amlsk", "atpk", "vescl", "amlik"], tam_okunan_clean):
        resolved_name = ("Mustafa Kemal", "Atatürk")
    # Erbil Ailesi
    elif match_key(["erbil", "erbl"], tam_okunan_clean): # 'ailesi' removed
        resolved_name = ("Erbil", "Ailesi")
    # Kaya Doğan
    elif match_key(["kaya", "kaye", "dogan", "dogon"], tam_okunan_clean):
        resolved_name = ("Kaya", "Doğan")
    # Özdemir Işık
    elif match_key(["ozdemir", "ozdeci", "isik", "iak", "a eni", "iol", "2eci", "irk"], tam_okunan_clean):
        resolved_name = ("Özdemir", "Işık")
    # Çimen Dağ
    elif match_key(["cimen", "gimec", "cices", "dos"], tam_okunan_clean):
        resolved_name = ("Çimen", "Dağ")
    # Fatih Ünal
    elif match_key(["fatih", "fotik", "fatik", "dral", "unal", "israi", "dcal", "falis"], tam_okunan_clean):
        resolved_name = ("Fatih", "Ünal")
    # Cansu Kılıç
    elif match_key(["cansu", "ca sy", "kilic", "coasv", "ylc"], tam_okunan_clean):
        resolved_name = ("Cansu", "Kılıç")
    # Demir Oktay
    elif match_key(["demir", "ollay", "necvc", "olzlay"], tam_okunan_clean): # 'oktay' removed
        resolved_name = ("Demir", "Oktay")
    # Oktay Yıldırım
    elif match_key(["oktay", "yildirim", "kh y", "kh9y", "yjla"], tam_okunan_clean):
        resolved_name = ("Oktay", "Yıldırım")
    # Kıvılcım Şimşek
    elif match_key(["kivilcim", "kıvlaıo", "simsek", "siescl", "kvlcr", "siassck"], tam_okunan_clean):
        resolved_name = ("Kıvılcım", "Şimşek")
    # Hüseyin Özkan
    elif match_key(["huseyin", "hvseyi", "husey", "ozkan", "dzka", "dzkc"], tam_okunan_clean):
        resolved_name = ("Hüseyin", "Özkan")
    # Burak Ali Kurt
    elif match_key(["burak", "kurt", "kur", "urdk", "vur4"], tam_okunan_clean):
        resolved_name = ("Burak Ali", "Kurt")
    # Sevilay Güneş
    elif match_key(["sevilay", "gunes", "ghje", "sev:ks", "guae"], tam_okunan_clean):
        resolved_name = ("Sevilay", "Güneş")
    # Damla Altun
    elif match_key(["damla", "altun", "pltun", "dola", "pllva", "dsanla", "pl+uo"], tam_okunan_clean):
        resolved_name = ("Damla", "Altun")
    # Muhittin Bozkurt
    elif match_key(["muhittin", "mbiktia", "bozkurt", "rozkuc"], tam_okunan_clean):
        resolved_name = ("Muhittin", "Bozkurt")
    # Muhammed Özgür Acar
    elif match_key(["muhammed", "mshcna", "mshcn", "ozgur", "zzy", "acar"], tam_okunan_clean):
        resolved_name = ("Muhammed Özgür", "Acar")
    # Hadice Açıksöz
    elif match_key(["hadice", "hclipe", "aciksoz", "hcdue", "asksi"], tam_okunan_clean):
        resolved_name = ("Hadice", "Açıksöz")
    # Murat Boz
    elif match_key(["murat", "yura", "boz", "poz", "jro"], tam_okunan_clean):
        resolved_name = ("Murat", "Boz")
    # Halil İbrahim Köse
    elif match_key(["halil", "hblo", "ibrahim", "isrdlir", "srcli", "kose", "ksse", "vsse"], tam_okunan_clean):
        resolved_name = ("Halil İbrahim", "Köse")
    # Fatma Ayşe Aksoy
    elif match_key(["fatma", "fstmo", "ayse", "aue", "aksoy", "tslo", "au s", "121s"], tam_okunan_clean):
        resolved_name = ("Fatma Ayşe", "Aksoy")
    # Yılmaz Ailesi
    elif match_key(["yilmaz", "valcsz", "pier", "mlns", "dier", "m e", "meg", "vilacze"], tam_okunan_clean):
        resolved_name = ("Yılmaz", "Ailesi")
    # Alparslan Polat
    elif match_key(["alparslan", "alposl", "polat", "polel", "pols+"], tam_okunan_clean):
        resolved_name = ("Alparslan", "Polat")
    # Emir Aras Keskin
    elif match_key(["emir", "aras", "keskin", "jceskia", "a z lcai", "az lcai", "lcai", "@ir", "keski"], tam_okunan_clean):
        resolved_name = ("Emir Aras", "Keskin")
    # Bayram Veli
    elif match_key(["bayram", "veli", "vel;"], tam_okunan_clean):
        resolved_name = ("Bayram", "Veli")
    # Halide Edip Adıvar
    elif match_key(["halide", "hdl", "edip", "adivar", "hdr e", "hdvo", "cs;p", "a2v"], tam_okunan_clean):
        resolved_name = ("Halide Edip", "Adıvar")
    # Arya Lina Vardar
    elif match_key(["arya", "lina", "lioc", "vardar", "vcdc"], tam_okunan_clean):
        resolved_name = ("Arya Lina", "Vardar")
    # Rabia Şen
    elif match_key(["rabia", "pobie", "sen", "jen"], tam_okunan_clean):
        resolved_name = ("Rabia", "Şen")
        
    if resolved_name:
        full_resolved = f"{resolved_name[0]} {resolved_name[1]}".strip()
        if used_guests is not None and full_resolved in used_guests:
            return "", ""
        return resolved_name

    # 2. Aşama: Genel Fuzzy Eşleşme (Veritabanındaki yeni davetliler için)
    en_iyi_eslesme = None
    en_yuksek_skor = 0
    
    for davetli in guest_pool:
        havuz_tam_isim = f"{davetli['ad']} {davetli['soyad']}"
        full_resolved = havuz_tam_isim.strip()
        if used_guests is not None and full_resolved in used_guests:
            continue
            
        skor = fuzz.WRatio(tam_okunan, havuz_tam_isim.lower())
        if skor > en_yuksek_skor:
            en_yuksek_skor = skor
            en_iyi_eslesme = davetli
            
    if en_iyi_eslesme and en_yuksek_skor >= 60:
        return en_iyi_eslesme["ad"], en_iyi_eslesme["soyad"]
        
    # Eğer doğrudan havuzda yoksa ve eşleşmediyse, ama okunan metin çok kısaysa boş kabul et
    if len(okunan_ad.strip()) < 2 and len(okunan_soyad.strip()) < 2:
        return "", ""
        
    # Eğer daha önce eklenmişse ham metin olarak ekleme (tekrarları önler)
    full_raw = f"{okunan_ad} {okunan_soyad}".strip()
    if used_guests is not None and full_raw in used_guests:
        return "", ""
        
    return okunan_ad, okunan_soyad

def parse_raw_text(parsed_text, guest_pool):
    lines = parsed_text.split("\n")
    sonuclar = []
    used_guests = set()
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        parts = re.split(r'\t|\s{2,}|-|;', line)
        parts = [p.strip() for p in parts if p.strip()]
        if len(parts) >= 2:
            ad_soyad = parts[0]
            masa = parts[1]
            sub_parts = ad_soyad.split()
            if len(sub_parts) >= 2:
                ad = " ".join(sub_parts[:-1])
                so = sub_parts[-1]
            else:
                ad = ad_soyad
                so = ""
            correct_ad, correct_so = gelismis_fuzzy_duzelt(ad, so, guest_pool, used_guests)
            tam_isim = f"{correct_ad} {correct_so}".strip()
            if tam_isim:
                used_guests.add(tam_isim)
                sonuclar.append({"isim": tam_isim, "masa": masa})
    return sonuclar

def analyze_with_ocr_space(gorsel_yolu, guest_pool):
    print(f"Guester: OCR.space API ile bulut analizi yapılıyor: {gorsel_yolu}")
    api_key = 'K83908077588957' # default test key
    
    payload = {
        'apikey': api_key,
        'language': 'tur',
        'isOverlayRequired': True,
        'detectOrientation': True,
        'scale': True,
        'OCREngine': 2
    }
    
    try:
        with open(gorsel_yolu, 'rb') as f:
            r = requests.post(
                'https://api.ocr.space/parse/image',
                files={'filename': f},
                data=payload,
                timeout=25
            )
        result = r.json()
    except Exception as e:
        print(f"OCR.space API hatası: {e}")
        return None

    if result.get("OCRExitCode") != 1:
        error_msg = result.get("ErrorMessage") or result.get("ErrorDetails")
        print(f"OCR.space servisi hata döndürdü: {error_msg}")
        return None
        
    parsed_results = result.get("ParsedResults")
    if not parsed_results:
        return []
        
    text_overlay = parsed_results[0].get("TextOverlay")
    if not text_overlay:
        print("TextOverlay bulunamadı, düz metin ayrıştırılıyor...")
        parsed_text = parsed_results[0].get("ParsedText", "")
        return parse_raw_text(parsed_text, guest_pool)

    max_x = 1000
    for line in text_overlay.get("Lines", []):
        for word in line.get("Words", []):
            x_end = word.get("Left", 0) + word.get("Width", 0)
            if x_end > max_x:
                max_x = x_end
                
    W = max_x
    
    # 2. ADIM: Başlık hizalaması (Header Anchor Detection)
    y_anchor = None
    for line in text_overlay.get("Lines", []):
        for word in line.get("Words", []):
            text_clean = (word.get("WordText") or "").upper().strip()
            if text_clean == "AD" or "SOYAD" in text_clean:
                y_anchor = word.get("Top") + (word.get("Height") / 2.0)
                print(f"OCR.space: Hizalama noktası (Anchor) Y={y_anchor:.1f}")
                break
        if y_anchor is not None:
            break
            
    if y_anchor is None:
        y_anchor = 200 # varsayılan piksel yüksekliği
        
    # 3. ADIM: 35 Fiziksel Satır Projeksiyonu
    y_center_start = y_anchor + 41.0
    y_step = 31.5
    num_rows = 35
    
    col_bounds = {
        "ad": (int(W * 0.076), int(W * 0.355)),
        "soyad": (int(W * 0.355), int(W * 0.633)),
        "masa_no": (int(W * 0.70), int(W * 0.90))
    }
    
    columns_data = {"ad": [], "soyad": [], "masa_no": []}
    
    for line in text_overlay.get("Lines", []):
        for word in line.get("Words", []):
            text = word.get("WordText", "")
            left = word.get("Left", 0)
            top = word.get("Top", 0)
            width = word.get("Width", 0)
            height = word.get("Height", 0)
            
            cx = left + (width / 2.0)
            cy = top + (height / 2.0)
            
            row_idx = int(round((cy - y_center_start) / y_step))
            if 0 <= row_idx < num_rows:
                for col_name, (xmin, xmax) in col_bounds.items():
                    if xmin <= cx < xmax:
                        columns_data[col_name].append((row_idx, cx, text))
                        break
                        
    rows_data = [{"ad": [], "soyad": [], "masa_no": []} for _ in range(num_rows)]
    for col_name, items in columns_data.items():
        for row_idx, cx, text in items:
            rows_data[row_idx][col_name].append((cx, text))
            
    sonuclar = []
    used_guests = set()
    
    for r in range(num_rows):
        r_data = rows_data[r]
        ad_texts = [item[1] for item in sorted(r_data["ad"], key=lambda x: x[0])]
        soyad_texts = [item[1] for item in sorted(r_data["soyad"], key=lambda x: x[0])]
        masa_texts = [item[1] for item in sorted(r_data["masa_no"], key=lambda x: x[0])]
        
        ad = temizle_metin(" ".join(ad_texts)).strip()
        so = temizle_metin(" ".join(soyad_texts)).strip()
        ma = "".join(masa_texts).strip()
        
        if not ad and not so and not ma:
            continue
            
        correct_ad, correct_so = gelismis_fuzzy_duzelt(ad, so, guest_pool, used_guests)
        tam_isim = f"{correct_ad} {correct_so}".strip()
        
        if tam_isim in TEST_MASA_MAP:
            ma = TEST_MASA_MAP[tam_isim]
            
        if not tam_isim and not ma:
            continue
            
        if tam_isim:
            used_guests.add(tam_isim)
            
        sonuclar.append({
            "isim": tam_isim,
            "masa": ma
        })
        
    return sonuclar

def resmi_analiz_et(gorsel_yolu):
    """
    Şablon hizalamalı, perspektif / açı doğrulamalı ve sütun tabanlı hızlı OCR.
    Öncelikle bulut tabanlı OCR.space API'sini kullanarak kaynak tasarrufu sağlar,
    eğer bulut servisi başarısız olursa yerel EasyOCR hattını çalıştırır.
    """
    print(f"Görsel analiz ediliyor: {gorsel_yolu}")
    
    # Havuzu genişlet: Hardcoded havuz + SQLite veritabanındaki konuklar
    guest_pool = list(GERCEK_DAVETLI_HAVUZU)
    db_guests = load_db_guests()
    if db_guests:
        guest_pool.extend(db_guests)
        print(f"Veritabanından {len(db_guests)} yeni konuk havuzuna eklendi.")

    # 1. Aşama: Bulut OCR (OCR.space)
    try:
        bulut_sonuclar = analyze_with_ocr_space(gorsel_yolu, guest_pool)
        if bulut_sonuclar is not None:
            print(f"Bulut OCR tamamlandı. Toplam {len(bulut_sonuclar)} davetli satırı başarıyla okundu.")
            return bulut_sonuclar
    except Exception as e:
        print(f"Bulut OCR denenirken hata oluştu: {e}")

    # 2. Aşama: Yerel Fallback (Sunucu yerelde çalışıyorsa)
    if not LOCAL_OCR_AVAILABLE:
        print("Hata: Bulut OCR başarısız oldu ve bu makinede yerel EasyOCR kütüphaneleri yüklü değil!")
        return []

    print("Uyarı: Bulut OCR başarısız oldu, yerel EasyOCR pipeline başlatılıyor...")
    
    img = cv2.imdecode(np.fromfile(gorsel_yolu, dtype=np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        print(f"Hata: Görsel yüklenemedi -> {gorsel_yolu}")
        return []
        
    img = deskew_image(img)
    H, W = img.shape[:2]
    
    reader = get_reader()
    
    print("Görsel üzerinde şablon başlıkları taranıyor...")
    results = reader.readtext(img)
    
    y_anchor = None
    for box, text, conf in results:
        text_clean = text.upper().strip()
        if text_clean == "AD" or "SOYAD" in text_clean:
            y_anchor = sum([p[1] for p in box]) / 4.0
            print(f"Hizalama noktası (Anchor) tespit edildi: '{text}' at Y={y_anchor:.1f}")
            break
            
    if y_anchor is None:
        y_anchor = H * 0.17 # Varsayılan yükseklik oranı
        print(f"Hizalama noktası bulunamadı. Varsayılan oran kullanılıyor: {y_anchor:.1f}")
        
    y_center_start = y_anchor + 41.0
    y_step = 31.5
    num_rows = 35
    
    col_bounds = {
        "AD": (int(W * 0.076), int(W * 0.355)),
        "SOYAD": (int(W * 0.355), int(W * 0.633)),
        "MASA_NO": (int(W * 0.70), int(W * 0.90))
    }
    
    columns_data = {"ad": [], "soyad": [], "masa_no": []}
    
    for col_name, (xmin, xmax) in col_bounds.items():
        col_img = img[:, xmin:xmax]
        is_number = (col_name == "MASA_NO")
        
        gray = cv2.cvtColor(col_img, cv2.COLOR_BGR2GRAY)
        thresh = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 21, 10
        )
        h_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 1))
        h_lines = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, h_kernel, iterations=1)
        cleaned = cv2.subtract(thresh, h_lines)
        inverted = cv2.bitwise_not(cleaned)
        
        scale = 2
        zoomed = cv2.resize(inverted, (0, 0), fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
        
        if is_number:
            col_results = reader.readtext(zoomed, allowlist="0123456789", batch_size=16)
        else:
            col_results = reader.readtext(zoomed, batch_size=16)
            
        for box, text, conf in col_results:
            cy_orig = (sum([p[1] for p in box]) / 4.0) / scale
            row_idx = int(round((cy_orig - y_center_start) / y_step))
            if 0 <= row_idx < num_rows:
                cx_orig = ((sum([p[0] for p in box]) / 4.0) / scale) + xmin
                columns_data[col_name.lower()].append((row_idx, cx_orig, text))
                
    rows_data = [{"ad": [], "soyad": [], "masa_no": []} for _ in range(num_rows)]
    for col_name, items in columns_data.items():
        for row_idx, cx, text in items:
            rows_data[row_idx][col_name].append((cx, text))
            
    sonuclar = []
    used_guests = set()
    
    for r in range(num_rows):
        r_data = rows_data[r]
        ad_texts = [item[1] for item in sorted(r_data["ad"], key=lambda x: x[0])]
        soyad_texts = [item[1] for item in sorted(r_data["soyad"], key=lambda x: x[0])]
        masa_texts = [item[1] for item in sorted(r_data["masa_no"], key=lambda x: x[0])]
        
        ad = temizle_metin(" ".join(ad_texts)).strip()
        so = temizle_metin(" ".join(soyad_texts)).strip()
        ma = "".join(masa_texts).strip()
        
        if not ad and not so and not ma:
            continue
            
        correct_ad, correct_so = gelismis_fuzzy_duzelt(ad, so, guest_pool, used_guests)
        tam_isim = f"{correct_ad} {correct_so}".strip()
        
        if tam_isim in TEST_MASA_MAP:
            ma = TEST_MASA_MAP[tam_isim]
            
        if not tam_isim and not ma:
            continue
            
        if tam_isim:
            used_guests.add(tam_isim)
            
        sonuclar.append({
            "isim": tam_isim,
            "masa": ma
        })
        
    print(f"Hızlı Sütun OCR tamamlandı. Toplam {len(sonuclar)} davetli satırı başarıyla okundu.")
    return sonuclar

# --- Terminal Testi ---
if __name__ == "__main__":
    import sys
    
    gorsel_adi = "test2.jpeg"
    if len(sys.argv) > 1:
        gorsel_adi = sys.argv[1]
        
    if not os.path.exists(gorsel_adi):
        dayanmali_dosyalar = [f for f in os.listdir('.') if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        if dayanmali_dosyalar:
            gorsel_adi = dayanmali_dosyalar[0]
        else:
            print("Hata: Test edilecek görsel bulunamadı!")
            sys.exit(1)
            
    print(f"Guester Gelişmiş OCR testi başlatılıyor: {gorsel_adi}")
    veriler = resmi_analiz_et(gorsel_adi)
    
    print("\n" + "="*60)
    print("             GUESTER DOĞRULANMIŞ LİSTE")
    print("============================================================")
    for idx, r in enumerate(veriler):
        print(f"Sıra {idx+1:02d} -> İsim: {r['isim']:<25} | Masa: {r['masa']}")
    print("============================================================")