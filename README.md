# Kur'an Kavram Atlası 


## Direkt Deneyimlemek için link https://erecene.github.io/kuran_atlas/index.html

### Eğer ne olduğunu merak ediyorsan okumaya devam et!
---

**Kur'an Kavram Atlası**, Kur'an-ı Kerim'deki 1500 benzersiz kelime kökünün birbirleriyle olan anlamsal, kavramsal ve teolojik ilişkilerini yapay zeka ve ağ teorisi (network theory) kullanarak eşleyen, analiz eden ve son kullanıcıya sunan interaktif bir semantik navigasyon aracıdır.

Proje, düz bir kelime aramasının ötesine geçerek; Kur'an kelimelerinin hangi zıtlık, sebep-sonuç, şart-bağımlılık veya ayrılmaz bütünlük ilişkisiyle birbirine bağlandığını Gemma-27B dil modeliyle analiz eder.

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

**Lisans / License:** MIT
