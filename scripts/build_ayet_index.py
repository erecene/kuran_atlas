import csv
import json
import re
from pathlib import Path

# --- Kofigürasyon ve Yollar ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data_raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data_processed"
INPUT_FILE = DATA_RAW_DIR / "meal_full.csv"
OUTPUT_FILE = DATA_PROCESSED_DIR / "ayet_index.json"

def process_roots(roots_str):
    """
    Ham kök metnini (Örn: "smw (سمو): adıyla | rHm (رحم): Rahman") parse eder, 
    sadece kök kodlarını (smw, rHm) içeren bir liste döner.
    Katman 2'deki detaylı analiz için zemin hazırlar.
    """
    if not roots_str or roots_str.strip() == "":
        return []

    # ' | ' karakterine göre ayır
    root_entries = roots_str.split('|')
    processed_roots = []
    
    for entry in root_entries:
        entry = entry.strip()
        if not entry:
            continue
            
        # Regex ile ilk kelimeyi (kök kodunu) yakala: "smw (سمو): adıyla" -> "smw"
        # İngilizce alfabe ve muhtemel karakterleri yakalar
        match = re.match(r'^([A-Za-z$]+)\s*\(.*?\)\s*:', entry)
        if match:
             # Kökleri küçük harfe çevirelim standartlaşma için
             root_code = match.group(1).lower().strip()
             processed_roots.append(root_code)
        else:
             # Eğer formata uymuyorsa ilk kelimeyi almayı deneyelim
             parts = entry.split(' ')
             if parts:
                 root_code = parts[0].lower().strip()
                 # Parantez veya iki nokta içeriyorsa temizle
                 root_code = re.sub(r'[\(\):]', '', root_code)
                 if root_code:
                     processed_roots.append(root_code)
            
    # Aynı kökü bir ayet içinde birden fazla kullandıysa, bu listede duplicate olabilir. 
    # Benzersizleştirmeyi burada yapabiliriz ya da frekans için tutabiliriz.
    # Mimari plana göre array içinde tutuyoruz, kelimenin frekansını (aynı ayette birden çok geçmesi) kaybetmemek için set()'e çevirmiyoruz.
    return processed_roots

def build_ayet_index():
    print("Katman 1: Ayet Veri İndeksi oluşturuluyor...")
    
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Kritik Hata: Kaynak veri dosyası '{INPUT_FILE}' bulunamadı!")
        
    ayet_index = {}
    total_rows = 0
    successful_rows = 0
    error_rows = 0
    
    # CSV'yi sadece okuma ('r') modunda açılır. Veri bozulma riski önlenir.
    # Windows ortamında BOM'lu utf-8 olabileceği ihtimaline karşı encoding="utf-8-sig" kullanıyoruz.
    with open(INPUT_FILE, "r", encoding="utf-8-sig") as file:
        # Delimiter olarak noktalı virgül (;) kullanıldığını örnek veriden (`Get-Content`) tespit ettik.
        reader = csv.reader(file, delimiter=";")
        
        # İlk satırın başlık olduğunu varsayarak atlıyoruz (sure_no;sure_adi;ayet_no;...)
        header = next(reader, None)
        
        for row in reader:
            total_rows += 1
            
            # Beklenen sütun sayısı kontrolü
            if len(row) < 5:
                print(f"Uyarı: Satır {total_rows} eksik sütun içeriyor, atlanıyor. İçerik: {row}")
                error_rows += 1
                continue
                
            try:
                sure_no = int(row[0].strip())
                sure_adi = row[1].strip()
                ayet_no = int(row[2].strip())
                arapca = row[3].strip()
                meal = row[4].strip()
                
                # Format: "2:177"
                verse_id = f"{sure_no}:{ayet_no}"
                
                # 6. sütun kökler olabilir, yoksa boş array
                roots_str = row[5].strip() if len(row) > 5 else ""
                kokler = process_roots(roots_str)
                
                # Eğer verse_id daha önce eklendiyse bu bir duplicate'tir. 
                if verse_id in ayet_index:
                    print(f"Uyarı: {verse_id} ID'li ayet tekrar ediyor! Önceki data korunuyor.")
                    error_rows += 1
                    continue
                
                ayet_index[verse_id] = {
                    "sure_no": sure_no,
                    "ayet_no": ayet_no,
                    "sure": sure_adi,
                    "arapca": arapca,
                    "meal": meal,
                    "kokler": kokler
                }
                
                successful_rows += 1
            except ValueError as e:
                print(f"Hata: Satır {total_rows} ayrıştırılamadı. Tür dönüşüm hatası: {e}")
                error_rows += 1
                
    # Sonuçların JSON'a yazılması
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(ayet_index, f, ensure_ascii=False, indent=2)
        
    print("-" * 30)
    print(f"İşlem tamamlandı!")
    print(f"Okunan toplam satır: {total_rows}")
    print(f"Başarıyla indekslenen ayet: {successful_rows}")
    print(f"Hatalı/Atlanan satır: {error_rows}")
    print(f"Çıktı dosyası: {OUTPUT_FILE}")
    
    # Doğrulama adımı: Kuran'da 6236 ayet vardır
    if successful_rows != 6236:
        print(f"DİKKAT! Normalde 6236 ayet olması gerekirken {successful_rows} ayet indekslendi. Veri setinizi kontrol ediniz.")

if __name__ == "__main__":
    build_ayet_index()
