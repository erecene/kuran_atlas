import json
import math
from pathlib import Path
from collections import defaultdict
from itertools import combinations

# --- Konfigürasyon ve Yollar ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PROCESSED_DIR = PROJECT_ROOT / "data_processed"
GRAPH_DATA_DIR = PROJECT_ROOT / "graph_data"
INPUT_KOK_AYET_MAP = DATA_PROCESSED_DIR / "kok_ayet_map.json"
INPUT_KOK_INDEX = DATA_PROCESSED_DIR / "kok_index.json"

# Çıktı dosyaları: Üç ayrı graf
OUTPUT_RAW_GRAPH = GRAPH_DATA_DIR / "cooccurrence_graph.json"
OUTPUT_PMI_GRAPH = GRAPH_DATA_DIR / "pmi_graph.json"
OUTPUT_FILTERED_GRAPH = GRAPH_DATA_DIR / "filtered_graph.json"

# --- Eşik Değerleri ---
RAW_WEIGHT_THRESHOLD = 3        # Ham ko-okürrans eşiği (plan gereği)
FILTERED_PMI_THRESHOLD = 2.0    # Filtrelenmiş graf için PMI alt sınırı
FILTERED_MIN_COOCCUR = 3        # Filtrelenmiş grafta minimum birlikte geçme sayısı


def compute_pmi(p_xy, p_x, p_y):
    """
    Pointwise Mutual Information (PMI) hesaplar.
    PMI(x,y) = log2( P(x,y) / (P(x) * P(y)) )
    
    Pozitif PMI → beklentinin üzerinde birlikte geçme (gerçek ilişki).
    Sıfır PMI → bağımsız, rastgele birlikte geçme.
    Negatif PMI → beklentinin altında birlikte geçme (birbirini dışlıyor).
    """
    if p_x == 0 or p_y == 0 or p_xy == 0:
        return 0.0
    return math.log2(p_xy / (p_x * p_y))


def compute_npmi(pmi_value, p_xy):
    """
    Normalized Pointwise Mutual Information (NPMI).
    NPMI = PMI / (-log2(P(x,y)))
    
    Değer aralığı [-1, +1]:
      +1 → her zaman birlikte geçiyor
       0 → bağımsız
      -1 → hiç birlikte geçmiyor
    """
    if p_xy <= 0:
        return 0.0
    denominator = -math.log2(p_xy)
    if denominator == 0:
        return 0.0
    return pmi_value / denominator


def build_graph():
    print("Katman 4: Ko-okürrans Kavram Grafı oluşturuluyor...")
    print("  → PMI/NPMI skorlaması aktif")
    print("  → Ayet uzunluğu normalizasyonu aktif")
    print()

    # --- Girdi Doğrulama ---
    if not INPUT_KOK_AYET_MAP.exists():
        raise FileNotFoundError(
            f"Kritik Hata: '{INPUT_KOK_AYET_MAP}' bulunamadı! Katman 3 çalıştırılmış olmalı."
        )
    if not INPUT_KOK_INDEX.exists():
        raise FileNotFoundError(
            f"Kritik Hata: '{INPUT_KOK_INDEX}' bulunamadı! Katman 2 çalıştırılmış olmalı."
        )

    # --- Veri Yükleme ---
    with open(INPUT_KOK_AYET_MAP, "r", encoding="utf-8") as f:
        kok_map = json.load(f)

    with open(INPUT_KOK_INDEX, "r", encoding="utf-8") as f:
        kok_index = json.load(f)

    ayet_to_kokler = kok_map["ayet_to_kokler"]
    kok_to_ayetler = kok_map["kok_to_ayetler"]
    total_ayetler = kok_map["meta"]["haritalanan_ayet"]  # Kök bilgisi olan ayet sayısı (6214)

    print(f"  Haritalanan ayet sayısı: {total_ayetler}")
    print(f"  Benzersiz kök sayısı  : {len(kok_to_ayetler)}")

    # =========================================================================
    # ADIM 1: Ham Ko-okürrans Hesaplama (Ayet Uzunluğu Normalizasyonlu)
    # 
    # Bir ayette N kök varsa, bu ayette N*(N-1)/2 çift oluşur.
    # Naif yöntemle her çift eşit ağırlık (1) alır → uzun ayetler grafı patlatır.
    # 
    # Çözüm (Network Science standardı):
    #   Her çift için ağırlık = 1/(N-1) olur.
    #   Böylece ayet uzunluğundan bağımsız, her köke düşen toplam katkı = 1 olur.
    # =========================================================================
    raw_edges = defaultdict(float)       # (k1, k2) → normalized cooccurrence weight
    raw_edges_count = defaultdict(int)   # (k1, k2) → ham ortak ayet sayısı (filtreleme için)

    print("\n  Ayet çiftleri taranıyor...")
    for verse_id, kokler in ayet_to_kokler.items():
        n = len(kokler)
        if n < 2:
            continue

        # Normalizasyon faktörü: 1/(N-1)
        norm_weight = 1.0 / (n - 1)

        # Tüm benzersiz çiftleri üret (sıralı key ile tutarlılık sağlanır)
        for k1, k2 in combinations(kokler, 2):
            pair = tuple(sorted([k1, k2]))
            raw_edges[pair] += norm_weight
            raw_edges_count[pair] += 1

    total_raw_edges = len(raw_edges)
    print(f"  Toplam ham edge sayısı       : {total_raw_edges}")

    # =========================================================================
    # ADIM 2: PMI ve NPMI Hesaplama
    #
    # P(k)   = o kökü içeren ayet sayısı / toplam ayet
    # P(k1,k2) = her iki kökü birlikte içeren ayet sayısı / toplam ayet
    # PMI(k1,k2) = log2( P(k1,k2) / (P(k1)*P(k2)) )
    # NPMI(k1,k2) = PMI / (-log2(P(k1,k2)))
    # =========================================================================
    print("  PMI/NPMI skorları hesaplanıyor...")

    # Kök olasılıkları: P(k) = kök_benzersiz_ayet / toplam_ayet
    kok_prob = {}
    for kok, ayetler in kok_to_ayetler.items():
        kok_prob[kok] = len(ayetler) / total_ayetler

    pmi_edges = {}
    for pair, count in raw_edges_count.items():
        k1, k2 = pair
        p_x = kok_prob.get(k1, 0)
        p_y = kok_prob.get(k2, 0)
        p_xy = count / total_ayetler

        pmi_val = compute_pmi(p_xy, p_x, p_y)
        npmi_val = compute_npmi(pmi_val, p_xy)

        pmi_edges[pair] = {
            "raw_count": count,
            "normalized_weight": round(raw_edges[pair], 4),
            "pmi": round(pmi_val, 4),
            "npmi": round(npmi_val, 4),
        }

    # =========================================================================
    # ADIM 3: Üç Ayrı Graf Üretimi
    # =========================================================================

    # --- GRAF 1: Raw Co-occurrence Graph ---
    # Tüm edge'ler, raw_count >= RAW_WEIGHT_THRESHOLD filtresiyle
    raw_graph_edges = []
    for pair, scores in pmi_edges.items():
        if scores["raw_count"] >= RAW_WEIGHT_THRESHOLD:
            raw_graph_edges.append({
                "source": pair[0],
                "target": pair[1],
                "weight": scores["normalized_weight"],
                "raw_count": scores["raw_count"],
            })

    # Node listesi (graf içinde en az bir edge'e sahip olan kökler)
    raw_nodes_set = set()
    for e in raw_graph_edges:
        raw_nodes_set.add(e["source"])
        raw_nodes_set.add(e["target"])

    raw_graph_nodes = []
    for kok in sorted(raw_nodes_set):
        info = kok_index.get(kok, {})
        raw_graph_nodes.append({
            "id": kok,
            "arapca": info.get("arapca", ""),
            "turkce": info.get("turkce", [])[:3],
            "frekans": info.get("frekans", 0),
        })

    raw_graph = {
        "meta": {
            "tip": "Raw Co-occurrence Graph",
            "aciklama": "Ham birlikte geçme grafiği (ayet uzunluğu normalizasyonlu, weight>=3 filtrelenmiş)",
            "node_sayisi": len(raw_graph_nodes),
            "edge_sayisi": len(raw_graph_edges),
            "esik": RAW_WEIGHT_THRESHOLD,
        },
        "nodes": raw_graph_nodes,
        "links": raw_graph_edges,
    }

    # --- GRAF 2: PMI Graph ---
    # Tüm edge'ler PMI/NPMI skorlarıyla, raw_count >= 2 (en az 2 ortak ayet)
    pmi_graph_edges = []
    for pair, scores in pmi_edges.items():
        if scores["raw_count"] >= 2:
            pmi_graph_edges.append({
                "source": pair[0],
                "target": pair[1],
                "pmi": scores["pmi"],
                "npmi": scores["npmi"],
                "raw_count": scores["raw_count"],
                "normalized_weight": scores["normalized_weight"],
            })

    pmi_nodes_set = set()
    for e in pmi_graph_edges:
        pmi_nodes_set.add(e["source"])
        pmi_nodes_set.add(e["target"])

    pmi_graph_nodes = []
    for kok in sorted(pmi_nodes_set):
        info = kok_index.get(kok, {})
        pmi_graph_nodes.append({
            "id": kok,
            "arapca": info.get("arapca", ""),
            "turkce": info.get("turkce", [])[:3],
            "frekans": info.get("frekans", 0),
        })

    pmi_graph = {
        "meta": {
            "tip": "PMI Co-occurrence Graph",
            "aciklama": "PMI/NPMI skorlu graf. Hub bias olmadan gerçek association strength ölçer.",
            "node_sayisi": len(pmi_graph_nodes),
            "edge_sayisi": len(pmi_graph_edges),
        },
        "nodes": pmi_graph_nodes,
        "links": pmi_graph_edges,
    }

    # --- GRAF 3: Filtered Semantic Graph ---
    # Sadece güçlü ve anlamlı ilişkiler: PMI >= threshold VE raw_count >= min
    filtered_graph_edges = []
    for pair, scores in pmi_edges.items():
        if (
            scores["pmi"] >= FILTERED_PMI_THRESHOLD
            and scores["raw_count"] >= FILTERED_MIN_COOCCUR
        ):
            filtered_graph_edges.append({
                "source": pair[0],
                "target": pair[1],
                "pmi": scores["pmi"],
                "npmi": scores["npmi"],
                "raw_count": scores["raw_count"],
                "normalized_weight": scores["normalized_weight"],
            })

    filtered_nodes_set = set()
    for e in filtered_graph_edges:
        filtered_nodes_set.add(e["source"])
        filtered_nodes_set.add(e["target"])

    filtered_graph_nodes = []
    for kok in sorted(filtered_nodes_set):
        info = kok_index.get(kok, {})
        filtered_graph_nodes.append({
            "id": kok,
            "arapca": info.get("arapca", ""),
            "turkce": info.get("turkce", [])[:3],
            "frekans": info.get("frekans", 0),
        })

    filtered_graph = {
        "meta": {
            "tip": "Filtered Semantic Graph",
            "aciklama": f"PMI>={FILTERED_PMI_THRESHOLD} ve raw_count>={FILTERED_MIN_COOCCUR} filtreli graf. LLM etiketleme ve görselleştirme için.",
            "node_sayisi": len(filtered_graph_nodes),
            "edge_sayisi": len(filtered_graph_edges),
            "pmi_esik": FILTERED_PMI_THRESHOLD,
            "min_cooccur": FILTERED_MIN_COOCCUR,
        },
        "nodes": filtered_graph_nodes,
        "links": filtered_graph_edges,
    }

    # =========================================================================
    # ADIM 4: Dosyalara Yazma
    # =========================================================================
    with open(OUTPUT_RAW_GRAPH, "w", encoding="utf-8") as f:
        json.dump(raw_graph, f, ensure_ascii=False, indent=2)

    with open(OUTPUT_PMI_GRAPH, "w", encoding="utf-8") as f:
        json.dump(pmi_graph, f, ensure_ascii=False, indent=2)

    with open(OUTPUT_FILTERED_GRAPH, "w", encoding="utf-8") as f:
        json.dump(filtered_graph, f, ensure_ascii=False, indent=2)

    # =========================================================================
    # ADIM 5: Detaylı Rapor
    # =========================================================================
    print("\n" + "=" * 60)
    print("KATMAN 4: Ko-okürrans Grafı — Sonuç Raporu")
    print("=" * 60)

    print(f"\n1️⃣  Raw Co-occurrence Graph")
    print(f"   Node sayısı  : {raw_graph['meta']['node_sayisi']}")
    print(f"   Edge sayısı  : {raw_graph['meta']['edge_sayisi']}")
    print(f"   Dosya        : {OUTPUT_RAW_GRAPH}")

    print(f"\n2️⃣  PMI Graph (Association Strength)")
    print(f"   Node sayısı  : {pmi_graph['meta']['node_sayisi']}")
    print(f"   Edge sayısı  : {pmi_graph['meta']['edge_sayisi']}")
    print(f"   Dosya        : {OUTPUT_PMI_GRAPH}")

    print(f"\n3️⃣  Filtered Semantic Graph (LLM + Viz)")
    print(f"   Node sayısı  : {filtered_graph['meta']['node_sayisi']}")
    print(f"   Edge sayısı  : {filtered_graph['meta']['edge_sayisi']}")
    print(f"   Dosya        : {OUTPUT_FILTERED_GRAPH}")

    # Hub Bias Kontrolü: En çok bağlantısı olan 10 kök
    print(f"\n{'='*60}")
    print("Hub Bias Kontrolü (Filtered Graph — en çok bağlantılı 10 kök):")
    degree_count = defaultdict(int)
    for e in filtered_graph_edges:
        degree_count[e["source"]] += 1
        degree_count[e["target"]] += 1

    top_hubs = sorted(degree_count.items(), key=lambda x: x[1], reverse=True)[:10]
    for kok, deg in top_hubs:
        info = kok_index.get(kok, {})
        arapca = info.get("arapca", "?")
        turkce = ", ".join(info.get("turkce", [])[:2])
        print(f"  {kok:8s} ({arapca}) → {deg:4d} bağlantı  [{turkce}]")

    # En yüksek NPMI'ye sahip 10 çift (en güçlü doğal ilişkiler)
    print(f"\n{'='*60}")
    print("En güçlü 10 kavram çifti (NPMI skoruna göre):")
    top_npmi = sorted(
        [(p, s) for p, s in pmi_edges.items() if s["raw_count"] >= 3],
        key=lambda x: x[1]["npmi"],
        reverse=True,
    )[:10]
    for pair, scores in top_npmi:
        k1_info = kok_index.get(pair[0], {})
        k2_info = kok_index.get(pair[1], {})
        k1_tr = ", ".join(k1_info.get("turkce", [])[:2])
        k2_tr = ", ".join(k2_info.get("turkce", [])[:2])
        print(
            f"  {pair[0]:8s} ↔ {pair[1]:8s}  "
            f"NPMI={scores['npmi']:.3f}  "
            f"PMI={scores['pmi']:.3f}  "
            f"ortak={scores['raw_count']}  "
            f"[{k1_tr}] ↔ [{k2_tr}]"
        )

    print(f"\n{'='*60}")
    print("Katman 4 tamamlandı.")


if __name__ == "__main__":
    build_graph()
