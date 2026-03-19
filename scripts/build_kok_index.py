import csv
import json
import re
from pathlib import Path
from collections import defaultdict

# --- Konfigürasyon ve Yollar ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data_raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data_processed"
INPUT_CSV = DATA_RAW_DIR / "meal_full.csv"
INPUT_JSON = DATA_PROCESSED_DIR / "ayet_index.json"
OUTPUT_FILE = DATA_PROCESSED_DIR / "kok_index.json"

def clean_turkish_meaning(meaning_str):
    """
    Parantez içindeki Türkçe anlamı veya bağlamı temizler.
    Örn: "(O) Rahman'dır" -> "rahmandır"
    Örn: "hamdolsun" -> "hamdolsun"
    """
    # Baştaki ve sondaki gereksiz noktalama ve boşlukları temizle
    meaning_str = meaning_str.strip()
    # Parantez içi zamirleri/ekleri (O), (Onlar) gibi yapilari kaldirabiliriz ama anlam kaybi olmamasi icin simdilik sadece kucuk harfe cevirip strip yapalim.
    meaning_str = meaning_str.lower()
    return meaning_str

def build_kok_index():
    print("Katman 2: Kök Sözlüğü (kok_index.json) oluşturuluyor...")
    
    if not INPUT_CSV.exists() or not INPUT_JSON.exists():
        raise FileNotFoundError(f"Kritik Hata: Gerekli girdi dosyaları bulunamadı! {INPUT_CSV} veya {INPUT_JSON} eksik.")

    # 1. Önce Katman 1'in çıktısı olan ayet_index'i okuyalım. (Ayet ID'leri haritalamak için)
    with open(INPUT_JSON, "r", encoding="utf-8") as f:
        ayet_index = json.load(f)

    # 2. Asıl Türkçe anlam ve Arapça orjinal kök harflerini almak için yine meal_full.csv'yi okuyacağız.
    # Çünkü ayet_index.json içerisine "sadece saf kök kodunu (örn: smw)" kaydetmiştik. Mimari plan tam da bunu istiyor.
    
    kok_dict = defaultdict(lambda: {
        "arapca": "",
        "turkce": set(),
        "frekans": 0,
        "ayetler": set()
    })
    
    with open(INPUT_CSV, "r", encoding="utf-8-sig") as file:
        reader = csv.reader(file, delimiter=";")
        header = next(reader, None)
        
        row_count = 0
        for row in reader:
            row_count += 1
            if len(row) < 5:
                continue
                
            sure_no = row[0].strip()
            ayet_no = row[2].strip()
            verse_id = f"{sure_no}:{ayet_no}"
            roots_str = row[5].strip() if len(row) > 5 else ""
            
            if not roots_str:
                continue
                
            # Örnek roots_str: "smw (سمو): adıyla | rHm (رحم): Rahman"
            root_entries = roots_str.split('|')
            for entry in root_entries:
                entry = entry.strip()
                if not entry:
                    continue
                
                # Regex ile 3 parçayı alalım: 
                # 1: Kök Kodu (smw)
                # 2: Arapça Orjinal Harfleri (سمو)
                # 3: Türkçe Anlamı (adıyla)
                match = re.match(r'^([A-Za-z$]+)\s*\((.*?)\)\s*:\s*(.*)$', entry)
                if match:
                    root_code = match.group(1).lower().strip()
                    arapca_orj = match.group(2).strip()
                    turkce_anlam = clean_turkish_meaning(match.group(3))
                    
                    # Veritabanına Ekleme
                    kok_dict[root_code]["arapca"] = arapca_orj
                    if turkce_anlam:
                        kok_dict[root_code]["turkce"].add(turkce_anlam)
                    kok_dict[root_code]["frekans"] += 1
                    kok_dict[root_code]["ayetler"].add(verse_id)
                else:
                    pass # Formata uymayan outlier loglanabilir. Ancak Katman 1'de güvenliği sağladık.

    # 3. Hazırlanan Dictionary'yi JSON kurallarına göre serialize edilebilir formata getir (Set -> List)
    final_kok_index = {}
    for root_code, data in kok_dict.items():
        final_kok_index[root_code] = {
            "arapca": data["arapca"],
            "turkce": list(data["turkce"]), # Set'i List'e çeviriyoruz
            "frekans": data["frekans"],
            "ayetler": sorted(list(data["ayetler"]), key=lambda x: (int(x.split(':')[0]), int(x.split(':')[1]))) # Sıralı ID'ler
        }
        
    print(f"Toplam tespit edilen eşsiz (benzersiz) kök sayısı: {len(final_kok_index)}")
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(final_kok_index, f, ensure_ascii=False, indent=2)
        
    print(f"Başarıyla kaydedildi: {OUTPUT_FILE}")

if __name__ == "__main__":
    build_kok_index()
