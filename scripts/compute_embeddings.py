import json
import os
import time
import random
import numpy as np
from pathlib import Path
from sklearn.preprocessing import normalize
from sklearn.cluster import KMeans

# 8️⃣ Deterministiklik için Sabit Tohum (Seed)
random.seed(42)
np.random.seed(42)

# --- Konfigürasyon ve Yollar ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PROCESSED_DIR = PROJECT_ROOT / "data_processed"
EMBEDDINGS_DIR = PROJECT_ROOT / "embeddings"

INPUT_KOK_INDEX = DATA_PROCESSED_DIR / "kok_index.json"
INPUT_AYET_INDEX = DATA_PROCESSED_DIR / "ayet_index.json"  # Ayet bağlamı için eklendi

# 5️⃣ & 7️⃣ Çıktı Dosyaları (Cache ve 3D ayrı)
CACHE_FILE = EMBEDDINGS_DIR / "embeddings_cache.json"
OUTPUT_EMBEDDINGS = EMBEDDINGS_DIR / "kok_embeddings.json" # Ham 768D vektörler
OUTPUT_COORDS = EMBEDDINGS_DIR / "kok_coords.json"         # HTML grafı için sadece coords

ENV_FILE = PROJECT_ROOT / ".env"

# Embedding modeli
EMBEDDING_MODEL = "gemini-embedding-2-preview"

# 3️⃣ UMAP parametreleri (Küçük veri için optimize)
UMAP_COMPONENTS = 3       # 3 boyutlu uzay
UMAP_N_NEIGHBORS = 35     # Global yapıyı korumak için artırıldı (~ sqrt(1500))
UMAP_MIN_DIST = 0.1       # Kümeleme sıkılığı
UMAP_METRIC = "cosine"    # Semantik benzerlik

# 6️⃣ API Rate Limiting (Kesin Çözüm: 100 İstek/Dakika Limiti Koruyucu)
# Önemli: Google API batch içindeki *her metni* 1 rate isteği sayar.
# Yani limit dakikada 100 metindir.
# Güvende kalmak için tek seferde 90 metin gönderip 60 saniye tam uykuya geçiyoruz.
BATCH_SIZE = 90
BATCH_DELAY_SECONDS = 62 


def load_api_key():
    key = os.environ.get("GEMINI_API_KEY", "")
    if key: return key

    if ENV_FILE.exists():
        with open(ENV_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("GEMINI_API_KEY="):
                    return line.split("=", 1)[1].strip()

    raise ValueError("Kritik Hata: GEMINI_API_KEY bulunamadı!")


def build_embedding_text(kok_code, kok_data, ayet_index):
    """
    1️⃣ & 2️⃣ Semantik Kaliteyi Artıran Metin Üretici
    - Tekrar eden Türkçe anlamlar (set) ile filtrelenir.
    - Sadece kök değil, kökün kullanıldığı 3 ayet meali modele bağlam (context) olarak sunulur.
    """
    arapca = kok_data.get("arapca", "")
    
    # 2️⃣ Çok anlamlılık problemi (yinelenen anlamları filtrele)
    turkce_liste = kok_data.get("turkce", [])
    benzersiz_anlamlar = sorted(list(set(turkce_liste)))
    anlamlar_str = ", ".join(benzersiz_anlamlar)

    # 1️⃣ Ayet Bağlamı Ekleme
    ayetler = kok_data.get("ayetler", [])[:3] # İlk 3 ayeti örnek olarak al
    ayet_texts = []
    
    for aid in ayetler:
        if aid in ayet_index:
            ayet_texts.append(ayet_index[aid]["meal"])
            
    ayet_str = " | ".join(ayet_texts)

    # Modele gönderilecek zengin içerik
    metin = f"Kur'an kavramı: {arapca}\nAnlamları: {anlamlar_str}"
    if ayet_str:
        metin += f"\nKullanıldığı ayetler:\n{ayet_str}"
        
    return metin


def get_embeddings_batch(texts, model_name, client):
    max_retries = 5
    for attempt in range(max_retries):
        try:
            result = client.models.embed_content(
                model=model_name,
                contents=texts,
                config={"task_type": "SEMANTIC_SIMILARITY", "output_dimensionality": 768}
            )
            return [e.values for e in result.embeddings]
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = 65  # Limit dolduğu için sakinleşme beklemesi
                print(f"    (Google API kotası esnedi, {wait_time} saniye güvenlik uykusu...)")
                time.sleep(wait_time)
            else:
                raise RuntimeError(f"API başarısız: {e}")


def compute_embeddings():
    print("Katman 5: Semantik Embedding Uzayı (Zengin Bağlamlı)")
    print("=" * 60)

    # --- 5️⃣ Cache Kontrolü ---
    cached_vectors = {}
    if CACHE_FILE.exists():
        print(f"  [Cache] {CACHE_FILE.name} bulundu, önbellekten okunuyor...")
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            cached_vectors = json.load(f)["vectors"]
            
    # --- Veri Yükleme ---
    with open(INPUT_KOK_INDEX, "r", encoding="utf-8") as f:
        kok_index = json.load(f)
        
    with open(INPUT_AYET_INDEX, "r", encoding="utf-8") as f:
        ayet_index = json.load(f)

    kok_codes = sorted(kok_index.keys())
    
    # API çekilecek olanları belirle
    eksik_kokler = [code for code in kok_codes if code not in cached_vectors]
    
    if eksik_kokler:
        print(f"  API ile çekilecek yeni kök sayısı: {len(eksik_kokler)}")
        api_key = load_api_key()
        from google import genai
        client = genai.Client(api_key=api_key)

        texts_to_embed = []
        for code in eksik_kokler:
            texts_to_embed.append(build_embedding_text(code, kok_index[code], ayet_index))

        # API İstekleri
        total_batches = (len(texts_to_embed) + BATCH_SIZE - 1) // BATCH_SIZE
        for i in range(0, len(texts_to_embed), BATCH_SIZE):
            batch_num = (i // BATCH_SIZE) + 1
            batch_codes = eksik_kokler[i : i + BATCH_SIZE]
            batch_texts = texts_to_embed[i : i + BATCH_SIZE]
            
            print(f"  Batch {batch_num}/{total_batches} ({len(batch_texts)} metin)...", end="", flush=True)

            embeddings = get_embeddings_batch(batch_texts, EMBEDDING_MODEL, client)
            
            for j, code in enumerate(batch_codes):
                cached_vectors[code] = embeddings[j]
                
            print(f" ✓")
            
            # Incremental (Adım Adım) Kayıt: Script çökse bile ilerleme kaybolmaz
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump({"meta": {"model": EMBEDDING_MODEL}, "vectors": cached_vectors}, f)
                
            if i + BATCH_SIZE < len(texts_to_embed):
                time.sleep(BATCH_DELAY_SECONDS)

        print(f"  Tüm kökler işlendi ve cache güncellendi: {CACHE_FILE.name}")
    else:
        print(f"  Tüm kökler cache'den yüklendi ({len(kok_codes)} adet). API çağrısı yapılmadı.")

    # Tüm sıralı embedding'leri array'e al
    all_embeddings = [cached_vectors[code] for code in kok_codes]
    
    # 4️⃣ Cosine Normalizasyon
    print("  Embedding'ler L2 birim vektörüne normalize ediliyor (Cosine stabilizasyonu)...")
    embedding_matrix = np.array(all_embeddings)
    embedding_matrix = normalize(embedding_matrix, norm='l2', axis=1)

    # --- UMAP Boyut İndirgeme ---
    import umap
    print(f"  UMAP ile {UMAP_COMPONENTS}D indirgeme başlatılıyor (n_neighbors={UMAP_N_NEIGHBORS})...")
    reducer = umap.UMAP(
        n_components=UMAP_COMPONENTS,
        n_neighbors=UMAP_N_NEIGHBORS,
        min_dist=UMAP_MIN_DIST,
        metric=UMAP_METRIC,
        random_state=42,
    )
    coords_3d = reducer.fit_transform(embedding_matrix)
    
    # 9️⃣ Görselleştirme Ölçekleme (Scale)
    coords_3d = coords_3d * 10.0

    # 10️⃣ KMeans Küme Kontrolü (Debug)
    kmeans = KMeans(n_clusters=8, random_state=42, n_init="auto")
    labels = list(kmeans.fit_predict(coords_3d))
    print(f"  [Debug] KMeans(n=8) küme dağılımı: {np.bincount(labels)}")

    # --- 7️⃣ Çıktı Dosyalarını Ayırma ---
    # 1. kok_embeddings.json (Analiz katmanları için, sadece ham 768D vektör)
    full_embed_data = {
        "meta": {"model": EMBEDDING_MODEL},
        "vectors": {code: [round(float(x), 6) for x in cached_vectors[code]] for code in kok_codes}
    }
    with open(OUTPUT_EMBEDDINGS, "w", encoding="utf-8") as f:
        json.dump(full_embed_data, f, ensure_ascii=False)

    # 2. kok_coords.json (HTML Graf görselleştirme için, sadece 3D coords ve cluster)
    coord_data = {
        "meta": {
            "umap_n_neighbors": UMAP_N_NEIGHBORS,
            "umap_min_dist": UMAP_MIN_DIST,
            "skaled": True,
            "clusters": 8
        },
        "nodes": {}
    }
    
    for idx, code in enumerate(kok_codes):
        coord_data["nodes"][code] = {
            "coords": [round(float(x), 4) for x in coords_3d[idx]],
            "cluster": int(labels[idx])
        }

    with open(OUTPUT_COORDS, "w", encoding="utf-8") as f:
        json.dump(coord_data, f, ensure_ascii=False)

    print("\n" + "=" * 60)
    print("KATMAN 5 SONUÇ RAPORU")
    print(f"  Benzersiz kök işlendi   : {len(kok_codes)}")
    print(f"  Raw Embeddings (Ağır)   : {OUTPUT_EMBEDDINGS.name}")
    print(f"  3D Coords (Hafif-HTML)  : {OUTPUT_COORDS.name}")
    print("=" * 60)


if __name__ == "__main__":
    compute_embeddings()
