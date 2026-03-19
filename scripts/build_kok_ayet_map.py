import json
from pathlib import Path
from collections import defaultdict

# --- Konfigürasyon ve Yollar ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PROCESSED_DIR = PROJECT_ROOT / "data_processed"
INPUT_AYET_INDEX = DATA_PROCESSED_DIR / "ayet_index.json"
INPUT_KOK_INDEX = DATA_PROCESSED_DIR / "kok_index.json"
OUTPUT_FILE = DATA_PROCESSED_DIR / "kok_ayet_map.json"


def build_kok_ayet_map():
    """
    Katman 3: Kavram Frekans ve Ayet Haritalaması

    Bu fonksiyon iki yönlü harita üretir:
      1. ayet_to_kokler  → "2:177": ["br", "slw", "amn", "zak"]
      2. kok_to_ayetler  → "amn": ["2:177", "3:110", ...]
      3. kok_frekans     → "amn": {"toplam_gecis": 812, "benzersiz_ayet": 540}

    Girdi: ayet_index.json (Katman 1 çıktısı)
    Doğrulama: kok_index.json (Katman 2 çıktısı) ile çapraz kontrol
    """
    print("Katman 3: Kavram Frekans ve Ayet Haritalaması başlıyor...")

    # --- Girdi Doğrulama ---
    if not INPUT_AYET_INDEX.exists():
        raise FileNotFoundError(
            f"Kritik Hata: '{INPUT_AYET_INDEX}' bulunamadı! Katman 1 çalıştırılmış olmalı."
        )
    if not INPUT_KOK_INDEX.exists():
        raise FileNotFoundError(
            f"Kritik Hata: '{INPUT_KOK_INDEX}' bulunamadı! Katman 2 çalıştırılmış olmalı."
        )

    # --- Katman 1 ve 2 çıktılarını oku ---
    with open(INPUT_AYET_INDEX, "r", encoding="utf-8") as f:
        ayet_index = json.load(f)

    with open(INPUT_KOK_INDEX, "r", encoding="utf-8") as f:
        kok_index = json.load(f)

    # =========================================================================
    # 1. AYET → KÖKLER haritası (ayet_to_kokler)
    #    Her ayetin içinde geçen köklerin BENZERSİZ listesi.
    #    Katman 4'te (Ko-okürrans Grafı) çift üretimi için bu yapı kullanılır.
    #    Benzersizleştirme burada yapılır çünkü aynı kökün aynı ayette
    #    birden fazla geçmesi ko-okürrans hesabını şişirmemelidir.
    # =========================================================================
    ayet_to_kokler = {}
    ayetsiz_kok_sayisi = 0

    for verse_id, verse_data in ayet_index.items():
        raw_kokler = verse_data.get("kokler", [])
        if not raw_kokler:
            ayetsiz_kok_sayisi += 1
            continue

        # Benzersizleştir ve sırala (deterministik çıktı için)
        unique_kokler = sorted(set(raw_kokler))
        ayet_to_kokler[verse_id] = unique_kokler

    # =========================================================================
    # 2. KÖK → AYETLER haritası (kok_to_ayetler)
    #    Her kökün geçtiği ayetlerin sıralı listesi.
    #    Bu, Katman 6'da (LLM) bağlam seçiminde ve Katman 7'de (UI)
    #    ayet panelinde kullanılacak.
    # =========================================================================
    kok_to_ayetler = defaultdict(set)

    for verse_id, kokler in ayet_to_kokler.items():
        for kok in kokler:
            kok_to_ayetler[kok].add(verse_id)

    # Sıralı listeye dönüştür (Set → sorted List)
    kok_to_ayetler_sorted = {}
    for kok, ayetler in kok_to_ayetler.items():
        kok_to_ayetler_sorted[kok] = sorted(
            list(ayetler),
            key=lambda x: (int(x.split(":")[0]), int(x.split(":")[1])),
        )

    # =========================================================================
    # 3. KÖK FREKANS tablosu (kok_frekans)
    #    Her kök için:
    #      - toplam_gecis: Kur'an genelinde bu kökün ham geçiş sayısı
    #                      (aynı ayette 2 kez geçerse 2 sayılır)
    #      - benzersiz_ayet: Bu kökün kaç farklı ayette geçtiği
    #    Bu iki değer Katman 4 ve 7'de node boyutu ve ağırlık
    #    hesaplamasında kullanılacak.
    # =========================================================================
    kok_frekans = {}

    for kok in kok_to_ayetler_sorted:
        # Ham geçiş sayısı: ayet_index üzerinden tüm köklerin düz sayımı
        toplam_gecis = 0
        for verse_id, verse_data in ayet_index.items():
            toplam_gecis += verse_data.get("kokler", []).count(kok)

        benzersiz_ayet = len(kok_to_ayetler_sorted[kok])

        kok_frekans[kok] = {
            "toplam_gecis": toplam_gecis,
            "benzersiz_ayet": benzersiz_ayet,
        }

    # =========================================================================
    # 4. ÇAPRAZ DOĞRULAMA: Katman 2'deki kök listesi ile tutarlılık kontrolü
    # =========================================================================
    katman2_kokler = set(kok_index.keys())
    katman3_kokler = set(kok_to_ayetler_sorted.keys())

    sadece_k2 = katman2_kokler - katman3_kokler
    sadece_k3 = katman3_kokler - katman2_kokler

    if sadece_k2:
        print(f"UYARI: Katman 2'de var ama Katman 3'te yok ({len(sadece_k2)} kök): {list(sadece_k2)[:10]}...")
    if sadece_k3:
        print(f"UYARI: Katman 3'te var ama Katman 2'de yok ({len(sadece_k3)} kök): {list(sadece_k3)[:10]}...")
    if not sadece_k2 and not sadece_k3:
        print("✓ Çapraz Doğrulama BAŞARILI: Katman 2 ve Katman 3 kök kümeleri birebir eşleşiyor.")

    # =========================================================================
    # 5. BİRLEŞİK ÇIKTI: Tek bir JSON dosyasında üç harita
    # =========================================================================
    output_data = {
        "meta": {
            "toplam_ayet": len(ayet_index),
            "haritalanan_ayet": len(ayet_to_kokler),
            "koksuz_ayet": ayetsiz_kok_sayisi,
            "toplam_benzersiz_kok": len(kok_to_ayetler_sorted),
        },
        "ayet_to_kokler": ayet_to_kokler,
        "kok_to_ayetler": kok_to_ayetler_sorted,
        "kok_frekans": kok_frekans,
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    # --- Rapor ---
    print("-" * 50)
    print(f"Toplam ayet sayısı           : {len(ayet_index)}")
    print(f"Kök bilgisi olan ayet sayısı : {len(ayet_to_kokler)}")
    print(f"Kök bilgisi olmayan ayet     : {ayetsiz_kok_sayisi}")
    print(f"Benzersiz kök sayısı         : {len(kok_to_ayetler_sorted)}")
    print(f"Çıktı dosyası                : {OUTPUT_FILE}")
    print("-" * 50)

    # Beklenen kontroller
    if len(ayet_index) != 6236:
        print(f"DİKKAT! Ayet sayısı 6236 olmalıydı, {len(ayet_index)} bulundu.")

    # En çok geçen 10 kökü göster (kalite kontrolü için)
    print("\nEn sık geçen 10 kök (toplam geçiş sayısına göre):")
    sirali = sorted(kok_frekans.items(), key=lambda x: x[1]["toplam_gecis"], reverse=True)
    for i, (kok, freq) in enumerate(sirali[:10], 1):
        kok_bilgi = kok_index.get(kok, {})
        arapca = kok_bilgi.get("arapca", "?")
        turkce = ", ".join(kok_bilgi.get("turkce", [])[:3])
        print(
            f"  {i:2d}. {kok:8s} ({arapca}) → "
            f"toplam: {freq['toplam_gecis']:5d}, "
            f"benzersiz ayet: {freq['benzersiz_ayet']:4d}  "
            f"[{turkce}]"
        )


if __name__ == "__main__":
    build_kok_ayet_map()
