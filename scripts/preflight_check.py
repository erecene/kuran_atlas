import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PROCESSED_DIR = PROJECT_ROOT / "data_processed"

print("Katman 4 Ön Kontrol Raporu")
print("=" * 50)

# 1. ayet_index
with open(DATA_PROCESSED_DIR / "ayet_index.json", "r", encoding="utf-8") as f:
    ayet_index = json.load(f)

# 2. kok_ayet_map
with open(DATA_PROCESSED_DIR / "kok_ayet_map.json", "r", encoding="utf-8") as f:
    kok_map = json.load(f)

# Benzersiz kök sayısı
print(f"Benzersiz kök sayısı        : {kok_map['meta']['toplam_benzersiz_kok']}")

# Toplam kök geçişi (ham)
toplam_ham = 0
for v in ayet_index.values():
    toplam_ham += len(v.get("kokler", []))
print(f"Toplam kök geçişi (ham)     : {toplam_ham}")

# Ortalama kök / ayet (benzersiz)
ayet_kok_counts = [len(kokler) for kokler in kok_map["ayet_to_kokler"].values()]
avg = sum(ayet_kok_counts) / len(ayet_kok_counts) if ayet_kok_counts else 0
min_k = min(ayet_kok_counts) if ayet_kok_counts else 0
max_k = max(ayet_kok_counts) if ayet_kok_counts else 0
print(f"Ortalama kök/ayet (benzers.): {avg:.2f}")
print(f"Min kök/ayet                : {min_k}")
print(f"Max kök/ayet                : {max_k}")

# N>20 olan ayetler
uzun = [(v_id, len(k)) for v_id, k in kok_map["ayet_to_kokler"].items() if len(k) > 20]
uzun.sort(key=lambda x: x[1], reverse=True)
print(f"20'den fazla köklü ayet     : {len(uzun)}")
for v_id, cnt in uzun[:5]:
    print(f"  {v_id}: {cnt} kök")

print("=" * 50)
if 8 <= avg <= 12:
    print("✓ Ortalama kök/ayet beklenen aralıkta (8-12). Parse sağlıklı.")
else:
    print(f"⚠ Ortalama kök/ayet ({avg:.2f}) beklenen aralığın dışında. Kontrol gerekebilir.")
