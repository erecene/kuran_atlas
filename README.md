# Kur'an Kavram Atlası (Quran Concept Atlas)

🌍 **[Türkçe](#türkçe-açıklama) | [English](#english-description)**

---

## Türkçe Açıklama

**Kur'an Kavram Atlası**, Kur'an-ı Kerim'deki 1500 benzersiz kelime kökünün birbirleriyle olan anlamsal, kavramsal ve teolojik ilişkilerini yapay zeka ve ağ teorisi (network theory) kullanarak eşleyen, analiz eden ve son kullanıcıya sunan interaktif bir semantik navigasyon aracıdır.

Proje, düz bir kelime aramasının ötesine geçerek; Kur'an kelimelerinin hangi zıtlık, sebep-sonuç, şart-bağımlılık veya ayrılmaz bütünlük ilişkisiyle birbirine bağlandığını Google Gemini-27B dil modelinin gücüyle analiz eder.

### Temel Özellikler (Modlar)

1. **Gelişmiş Semantik Okuyucu (Kavram İncele)**
   - İstediğiniz bir kavramın (Örn: `rhm` - rahmet) Kur'an uzayındaki yerini bulun.
   - Bu kavramla anlam bağı en yüksek olan diğer kavramları "AI Mantık Açıklaması" ve "Semantik Uyum Skoru" ile birlikte listeleyin.
   - Ortak geçen örnek ayetler üzerinden sistemin tespitlerini test edin.

2. **Kavramsal Yolculuklar (Dijkstra Arama)**
   - Birbiriyle görünürde bağı olmayan iki kelime arasında (Örn: "Melek" ve "Ateş") Kur'an'ın kendi anlamsal köprülerini kullanarak nasıl gidilebileceğini keşfedin.
   - Sistem arka planda `Dijkstra's Shortest Path` algoritmasını kullanarak kavramlar arası en kısa anlam rotasını dikey bir zaman çizelgesinde (Timeline) render eder.

3. **Ayet Röntgeni (Ayet İncele)**
   - Belirli bir ayeti (Örn: Bakara 255) sisteme girin.
   - Sistem o ayetteki tüm kelime köklerini deşifre etsin ve sadece o kelimelerin kendi aralarındaki makro teolojik bağları (Mikro Semantik Çözümleme) listelesin.

### Veri ve Mimari (10 Katmanlı İşleyiş)
Bu sistem anlık olarak API'ye soru soran bir chatbot değildir. Veriler **10 Katmanlı** kompleks bir veri madenciliği (Big Data) hattı üzerinden önceden işlenmiş, doğrulanmış ve tarayıcıda sıfır gecikmeyle (0ms) çalışacak şekilde istemciye (Frontend) gömülmüştür. 
Daha detaylı bilgi için: `işleyis.md` belgesini okuyabilirsiniz.

### Kurulum ve Çalıştırma
Sistemi bilgisayarınızda kendi başınıza nasıl çok kolay bir şekilde çalıştırabileceğinizi öğrenmek için lütfen [KURULUM.md](KURULUM.md) dosyasına göz atın.

---

## English Description

**Quran Concept Atlas** is an interactive semantic navigation tool that maps, analyzes, and visualizes the semantic, conceptual, and theological relationships between 1500 unique word roots in the Quran using artificial intelligence and network theory.

Moving beyond simple word searches, this project leverages the power of the Google Gemini-27B large language model to analyze whether Quranic words are connected through antonymy, cause-and-effect, conditional dependency, or inseparable unity.

### Key Features (Modes)

1. **Semantic Explorer (Concept View)**
   - Discover the position of any desired concept (e.g., `rhm` - mercy) within the Quranic spatial matrix.
   - List the most strictly correlated concepts alongside an "AI Logic Reason" and "Semantic Correlation Score".
   - Validate the system's findings through verses where the words co-occur.

2. **Conceptual Journeys (Dijkstra Pathfinding)**
   - Explore how to navigate between two seemingly unrelated words (e.g., "Angel" and "Fire") using the Quran's own semantic bridges.
   - The system utilizes `Dijkstra's Shortest Path` algorithm in the background to calculate and render the shortest semantic route between concepts on a vertical Timeline.

3. **Verse Scanner (Verse View)**
   - Focus down onto a specific verse (e.g., 2:255 / Al-Baqarah 255).
   - The engine reverse-engineers all the functional roots within that specific verse and isolates only the macro-theological bonds (Micro Semantic Analysis) occurring uniquely among those specific root words.

### Data & Architecture (10-Layer Pipeline)
This system is not a chatbot that pings an API on the fly. All lexical and semantic data has been pre-processed, mathematically verified, and embedded into the Frontend via a complex **10-Layer** Big Data mining pipeline, ensuring zero-latency (0ms) execution directly in the browser.
For a deeper dive into the architecture, please read the `işleyis.md` document (Available in Turkish).

### Running Locally
To learn how to easily run this system on your own machine, please check the [KURULUM.md](KURULUM.md) file (Available in Turkish).

---

**Lisans / License:** MIT
