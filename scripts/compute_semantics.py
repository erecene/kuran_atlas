import os
import json
import time
import concurrent.futures
from dotenv import load_dotenv
from google import genai
from google.genai import types

# -------------------------------------------------------------------
# AYARLAR VE YAPILANDIRMA
# -------------------------------------------------------------------
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path)
API_KEY = os.environ.get("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError("HATA: GEMINI_API_KEY bulunamadı! Lütfen .env dosyasını kontrol edin.")

client = genai.Client(api_key=API_KEY)

# MODEL SEÇİMİ (Gemma-3-27B)
# Not: Söz konusu model 30 RPM ve 15.000 Bağlam kapasitesine sahiptir.
LLM_MODEL = "gemma-3-27b-it" 

# DOSYA YOLLARI
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX_FILE = os.path.join(BASE_DIR, "data_processed", "kok_index.json")
GRAPH_FILE = os.path.join(BASE_DIR, "graph_data", "filtered_graph.json")
AYET_FILE = os.path.join(BASE_DIR, "data_processed", "ayet_index.json")

# ÇIKTI DOSYALARI
OUTPUT_DIR = os.path.join(BASE_DIR, "semantics")
os.makedirs(OUTPUT_DIR, exist_ok=True)
CACHE_FILE = os.path.join(OUTPUT_DIR, "semantics_cache.json")
FINAL_OUTPUT_FILE = os.path.join(OUTPUT_DIR, "semantic_relations.json")

# API RATE LIMITING VE PARALEL İŞLEM
BATCH_SIZE = 15          # API limitlerine göre ayarlanabilir
BATCH_DELAY_SECONDS = 0  # Artık ThreadPool var, API kotalarına göre sleep eklenebilir
MAX_WORKERS = 3          # Eşzamanlı (Paralel) gönderilecek API isteği sayısı

# 4️⃣ İLİŞKİ KATEGORİLERİ (Genişletildi ve İyileştirildi)
RELATION_CATEGORIES = [
    "Eş Anlamlılık", 
    "Ayrılmaz Bütünlük",
    "Zıtlık", 
    "Somutlaştırma", 
    "Hiyerarşi (Alt-Üst)", 
    "Sebep-Sonuç", 
    "Şart-Bağımlılık", 
    "Sıfat/Niteleme",
    "Aksiyon/Eylem",
    "Kıssa/Tarih", 
    "İlişki Yok"
]

def load_data():
    """Gerekli JSON dosyalarını yükler."""
    print("Dosyalar yükleniyor...")
    with open(INDEX_FILE, 'r', encoding='utf-8') as f:
        kok_index = json.load(f)
    with open(GRAPH_FILE, 'r', encoding='utf-8') as f:
        graph_data = json.load(f)
    with open(AYET_FILE, 'r', encoding='utf-8') as f:
        ayet_index = json.load(f)
        
    return kok_index, graph_data, ayet_index

def get_shared_ayets(kok1_data, kok2_data, ayet_index, limit=3):
    """2️⃣ İki kökün ortak geçtiği ayetlerin meallerini döndürür (En Kısalar Seçilerek)."""
    ayets1 = set(kok1_data.get("ayetler", []))
    ayets2 = set(kok2_data.get("ayetler", []))
    shared_ids = list(ayets1.intersection(ayets2))
    
    # En kısa ayetleri seç (LLM Context temizliği için)
    shared_ids = sorted(shared_ids, key=lambda x: len(ayet_index[x]["meal"]) if x in ayet_index else 9999)
    
    shared_texts = []
    for aid in shared_ids[:limit]: 
        if aid in ayet_index:
            shared_texts.append(ayet_index[aid]["meal"])
            
    return shared_texts

def build_prompt(kok1_code, kok2_code, kok1_data, kok2_data, shared_texts, npmi_score):
    """3️⃣ ve 🔟 LLM için katı, halüsinasyon korumalı ve stat-destekli prompt üretir."""
    
    kok1_anlamlar = ", ".join(set(kok1_data.get("turkce", [])))
    kok2_anlamlar = ", ".join(set(kok2_data.get("turkce", [])))
    
    ayet_str = ""
    for i, meal in enumerate(shared_texts, 1):
        ayet_str += f"{i}. Ayet: {meal}\n"
        
    kategoriler_str = ", ".join(RELATION_CATEGORIES)

    prompt = f"""
Kur'an'da aynı ayetlerde geçen iki kavramın aralarındaki "Semantik İlişki Türünü" analiz etmeni istiyorum.

KAVRAM 1: {kok1_code} (Anlamları: {kok1_anlamlar})
KAVRAM 2: {kok2_code} (Anlamları: {kok2_anlamlar})

İstatistiksel Yakınlık (NPMI Skoru): {npmi_score:.3f} (-1 ile +1 arasındadır. +1'e ne kadar yakınsa, bu iki kelimenin birlikte geçişi tesadüfün o kadar ötesinde ve güçlü bir bağı olduğunu kanıtlar).

Bu iki kavramın birlikte geçtiği örnek (en kısa) ayetler:
{ayet_str}

GÖREV:
Bu iki kavram arasındaki ilişkiyi aşağıdaki kategorilerden SADECE BİRİ ile eşleştir.
Kategoriler: {kategoriler_str}

KRİTİK UYARI: Eğer ayetlerde açık, net ve tartışılmaz bir semantik ilişki YOKSA, zorla ilişki üretme! Kesinlikle "İlişki Yok" seçeneğini seç.

LÜTFEN SADECE VE SADECE AŞAĞIDAKİ JSON FORMATINDA YANIT VER. KESİNLİKLE BAŞKA BİR AÇIKLAMA YAZMA.
```json
{{
    "type": "Secilen_Kategori",
    "score": 0.0_ile_1.0_arasi_guven_skoru,
    "reason": "Bu ilişkiyi neden seçtiğine dair SADECE 1 CÜMLELİK çok kısa bir açıklama"
}}
```
"""
    return prompt.strip()

def ask_llm(prompt, max_retries=5):
    """LLM'e prompt gönderir ve JSON yanıtını onaylayıp ayrıştırır."""
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=LLM_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.0 # Halüsinasyonu SIFIRLAMAK için 0.0 
                )
            )
            
            result_text = response.text.strip()
            if result_text.startswith("```json"):
                result_text = result_text[7:]
            if result_text.endswith("```"):
                result_text = result_text[:-3]
                
            parsed_json = json.loads(result_text.strip())
            
            # Kategori doğrulaması
            if parsed_json.get("type") not in RELATION_CATEGORIES:
                parsed_json["type"] = "İlişki Yok"
                
            # 6️⃣ Kalite Kontrol: Skor doğrulaması
            score = parsed_json.get("score", 0)
            if not isinstance(score, (int, float)):
                score = 0
            parsed_json["score"] = max(0, min(float(score), 1.0))
                
            return parsed_json
            
        except Exception as e:
            err_str = str(e)
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "Quota" in err_str:
                print(f"    ⏳ API TPM/RPM Kotası! 65 saniye soğutma moduna geçiliyor... (Deneme {attempt+1}/{max_retries})")
                time.sleep(65)
            else:
                if attempt < max_retries - 1:
                    wait_time = 5 * (attempt + 1)
                    time.sleep(wait_time)
                else:
                    return {"error": True, "reason": "API Hatası: " + err_str}
    
    return {"error": True, "reason": "Maksimum deneme (Max Retries) aşıldı."}

def process_single_link(link, kok_index, ayet_index):
    """Paralel işleme (ThreadPool) için tekil görev fonksiyonu."""
    # 7️⃣ FİLTRE: LLM maliyetini ve gürültüyü engelle!
    npmi = link.get("npmi", 0)
    raw_count = link.get("raw_count", 0)
    
    if npmi < 0.25 and raw_count < 3: # PMI grafı zaten filtreliydi ama güvenliği artırıyoruz
        return None
        
    source = link['source']
    target = link['target']
    
    # 1️⃣ Edge Yönsüzlüğü (Cache Çakışması Engellendi)
    edge_id = "---".join(sorted([source, target]))
    
    kok1_data = kok_index.get(source, {})
    kok2_data = kok_index.get(target, {})
    
    shared_texts = get_shared_ayets(kok1_data, kok2_data, ayet_index)
    
    # Text yoksa veya çok zayıfsa atla
    if not shared_texts:
         return None
         
    prompt = build_prompt(source, target, kok1_data, kok2_data, shared_texts, npmi)
    analysis = ask_llm(prompt)
    
    # EĞER API HATASI VARSA VEYA CEVAP ALINAMADIYSA BU BAĞI CACHE'E YAZMA (ATLA)
    if analysis.get("error"):
        print(f"      [HATA ATLANDI] {source}-{target} bağı için API hatası: {analysis.get('reason')}")
        return None
    
    result = {
        "edge_id": edge_id,
        "source": source,
        "target": target,
        "type": analysis.get("type", "İlişki Yok"),
        "score": analysis.get("score", 0.0),
        "reason": analysis.get("reason", ""),
        "pmi": link.get("pmi"),
        "npmi": npmi,
        "raw_count": raw_count
    }
    
    # TPM/RPM KOTASINA UYABİLMEK İÇİN SENTETİK BEKLEME
    # Gemma 3 27B için 15000 TPM limitini vurmamak için süreyi uzatıyoruz (Worker x 10.0 sn)
    time.sleep(10.0)
    
    return result

def compute_semantics():
    kok_index, graph_data, ayet_index = load_data()
    links = graph_data.get("links", [])
    
    print(f"\nKatman 6: LLM Destekli İlişki Anlamlandırma")
    print("============================================================")
    print(f"Graf İçindeki Toplam İşlenebilecek Kenar: {len(links)}")
    
    # Cache yükleme
    cache_data = {}
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)
        print(f"  [Cache] {len(cache_data)} adet ilişki önbellekten (cache) yüklendi.")
        
    links_to_process = []
    for link in links:
        # 1️⃣ Edge Yönsüzlüğü kontrolü
        edge_id = "---".join(sorted([link['source'], link['target']]))
        if edge_id not in cache_data:
            links_to_process.append(link)
            
    print(f"  API'ye Gönderilecek (NPMI filtresi öncesi) Kalan Kenar: {len(links_to_process)}")
    
    if len(links_to_process) == 0:
        print("  İşlem önceden tamamlanmış! Sonuçlar yazdırılıyor.")
    else:
        # 8️⃣ Parallelism Eklendi (ThreadPoolExecutor)
        # Her X kayıtta bir Cache kaydetmek için sayaç kullanalım
        processed_count = 0
        total_to_process = len(links_to_process)
        
        print(f"  {MAX_WORKERS} iş parçacığı (Worker) ile Paralel API İstemi Başlatılıyor...\n")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            # Tüm görevleri gönder
            future_to_link = {executor.submit(process_single_link, link, kok_index, ayet_index): link for link in links_to_process}
            
            for future in concurrent.futures.as_completed(future_to_link):
                result = future.result()
                processed_count += 1
                
                if result is not None:
                    cache_data[result["edge_id"]] = result
                    
                # Her 20 sonuçta bir log ver ve cache'i kaydet (Elektrik/İnternet kopması güvenliği)
                if processed_count % 20 == 0 or processed_count == total_to_process:
                    print(f"    İlerleme: {processed_count}/{total_to_process} ilişki işlendi. (Cache yedekleniyor)")
                    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
                        json.dump(cache_data, f, ensure_ascii=False, indent=2)
                        
    print("\n  [BİTTİ] Final dosya (Graf Motoru Uyumlu Yeni Format) oluşturuluyor...")
    
    # 9️⃣ Final JSON Yapısı İyileştirildi (Edge list format)
    final_edges = list(cache_data.values())
    
    with open(FINAL_OUTPUT_FILE, 'w', encoding='utf-8') as f:
         json.dump({"edges": final_edges}, f, ensure_ascii=False, indent=2)
         
    print(f"  Başarılı! Sonuçlar '{FINAL_OUTPUT_FILE}' dosyasına kaydedildi.")

if __name__ == "__main__":
    compute_semantics()
