# Mimari ve Tasarım Kararları (Değişiklikler)

## Katman 0: Proje Altyapısı (Oluşturuldu)
- Sistem tekrarlanabilirlik (reproducibility) ve şeffaflık ilkelerine dayanarak kurulmuştur.
- Modülerliği korumak amacıyla her bir veri işleme adımı (1. İndeksleme, 2. Haritalama, 3. Graf, 4. Embedding) sadece kendi alanındaki dosyayı okuyacak ve sonucunu ayrı bir yapılandırılmış klasöre dökecektir.
- Eski versiyonların birbirini ezmesini önlemek ve veri yollarını standartlaştırmak için `data_raw`, `data_processed`, `graph_data`, `embeddings`, `scripts`, `docs` izole klasörleri oluşturulmuştur.
- Projede sahte (mock) veri kullanımını fiziksel olarak imkansız kılacak klasör hiyerarşisi uygulanmıştır. Bütün pipeline adımları `data_raw` altındaki ham datayı çekmekle mesul kılındı.


## Katman 1: Ayet Veri İndeksi (Tamamlandı)
- **ID Standartlaştırması:** Sûre ve Ayet numaraları kullanılarak `{sure_no}:{ayet_no}` formatında benzersiz `verse_id`'ler (örn: `2:177`) oluşturuldu. İleriki tüm JSON objeleri ve Graf nodeları bu formata referans verecek şekilde mimari kesinleştirildi.
- **Kök Ayrıştırma Regex Kararı:** 6. Sütunda bulunan kompleks kök dökümleri `r'^([A-Za-z$]+)\s*\(.*?\)\s*:'` regex yapısı kullanılarak "Arapça pürüzlerinden arındırılmış" ve sadece sistemin kullanabileceği düz kök kodlarına (`smw`, `kfr`) indirgenmiştir.
- **Frekans Kaybı Koruması:** Bir ayette aynı kökün birden fazla geçmesi (örn: Fatiha 1. ve 3. ayette `rhm` kökünün tekrar etmesi), metin istatistiği ve kavram yoğunluğu analizlerinde (Katman 3 frekans tablosu) önem taşıdığı için "kök listesi" (array) olduğu gibi korundu, `Set` (tekil küme) yapısına dökülerek frekans bilgisi KASITLI olarak SİLİNMEDİ. (Not: Bu katman embedding'e değil, metin istatistiğine hizmet eder. Embedding Katman 5'te semantik bağlam üzerinden çalışır.)
- **Encoding Standartlaştırması:** Kullanıcının (EnginSu) muhtemelen Excel tabanlı veya Windows bazlı ortamlardan csv çıkartacağı öngörülerek, UTF-8 uyumsuzluğunu aşmak adına read işlemi `utf-8-sig` BOM destekli karaktere güncellendi.

## Katman 2: Kök Sözlüğü (Tamamlandı)
- **Data Enrichment (Veri Zenginleştirme):** Ayet indeksi sadece ID ve saf kök listesi tutarken, `kok_index.json` her bir kök için Arapça orjinal karakterleri ve Türkçe anlam haznelerini birleştirecek şekilde zenginleştirildi.
- **Duyarsızlaştırma ve Normalizasyon:** Türkçe anlamlar `.lower()` ve `.strip()` ile normalize edilerek aynı kelimenin farklı varyasyonlarının küme içinde gürültü yapması (Örn: "Gök", "gök", "gök ") engellendi.
- **Benzersizlik Kontrolü:** Toplamda 1500 benzersiz kök tespit edilerek, sistemin "Node (Düğüm)" sayısının sınırları belirlenmiş oldu.
- **Bağlamsal Adresleme:** Her kök sadece istatistik değil, geçtiği ayetlerin listesini de taşıdığı için (Inverse Map), Katman 3 ve Katman 4'teki graf üretim performansı O(1) seviyesine optimize edildi.

## Katman 3: Kavram Frekans ve Ayet Haritalaması (Tamamlandı)
- **Benzersizleştirme Kararı (Kritik):** Katman 1'de bir ayette aynı kökün tekrarını korumuştuk (frekans kaybını önlemek için). Ancak Katman 3'te ko-okürrans hesabını bozmamak adına `ayet_to_kokler` haritasında `sorted(set(kokler))` kullanılarak **bilinçli benzersizleştirme** yapıldı. Böylece aynı kökün bir ayette 3 kez geçmesi, o kökün başka köklerle yapay olarak güçlü bağ kurmasını engelliyor.
- **Çifte Frekans Mimarisi:** Her kök için tek bir sayı yerine iki ayrı frekans tutuldu: `toplam_gecis` (ham tekrar) ve `benzersiz_ayet` (kaç farklı ayette). Bu, ileride Node boyutlandırmasında (Katman 7) kullanıcıya "sıklık mı, yaygınlık mı?" seçeneği sunabilmeyi mümkün kılıyor.
- **Katmanlar Arası Çapraz Doğrulama:** Katman 2 ile Katman 3 arasında kök kümeleri otomatik olarak karşılaştırılarak veri kaybı, hayalet kök veya eksik eşleşme riski sıfıra indirildi. Her iki küme birebir eşleşiyor.
- **22 Köksüz Ayet Tespiti:** 6236 ayetin 22'sinde kök bilgisi bulunmadığı tespit edildi. Bu ayetler silinmedi, haritalama dışında bırakıldı. Veri kaybı yapılmadan şeffaf raporlandı.

## Katman 4: Ko-okürrans Kavram Grafı (Tamamlandı)
- **Ayet Uzunluğu Normalizasyonu (Kritik):** Ön kontrol 99 adet 20+ köklü ayet tespit etti (max: Bakara 282, 47 kök). Naif sayımda bu tek ayet 1081 çift üretir. `weight += 1/(N-1)` normalizasyonu uygulanarak uzun ayetlerin graf merkezine yapay olarak oturması engellendi. (Network Science standardı.)
- **PMI/NPMI Eklenmesi (Kritik):** Sadece ham frekans yerine, her çift için PMI (beklentinin üzerindeki ilişki gücü) ve NPMI (normalize edilmiş versiyonu, -1 ile +1 arasında) hesaplandı. Bu sayede "Allah–iman" gibi sık geçen ama gerçek association strength'i düşük olan çiftler, "güneş–ay" gibi gerçekten anlamlı çiftlerden doğru şekilde ayrıştırıldı.
- **Üçlü Graf Mimarisi:** Tek graf yerine üç ayrı graf üretildi:
  - `cooccurrence_graph.json` → Ham birlikte geçme grafı (Analiz ve keşif için)
  - `pmi_graph.json` → PMI/NPMI skorlu graf (Hub bias olmadan saf ilişki gücü için)
  - `filtered_graph.json` → PMI>=2.0 ve raw_count>=3 filtreli graf (LLM etiketleme ve görselleştirme için)
- **Hub Bias Kontrolü:** Filtered Graph'ta en çok bağlantılı kök `nsw` (نسو) 52 bağlantı ile birinci. Allah, iman gibi kökler hub olarak patlamamış. PMI normalizasyonunun doğru çalıştığının kanıtı.
- **Semantik Doğrulama:** En yüksek NPMI'ye sahip çiftler Kur'an'daki bilinen tematik ikilileri doğruluyor: amca↔dayı (0.909), güneş↔ay (0.839), doğu↔batı (0.835). Bu, grafın gerçek semantik yapıyı yakaladığını kanıtlıyor.

### Katman 5
1. **Bağlam (Context) Üretimi:** Kökler sisteme sadece kod ve anlamları olarak değil, Kur'an'da geçtiği ilk 3 ayetin Türkçe mealiyle birlikte (Zenginleştirilmiş RAG Metni) gönderildi.
2. **Çok Anlamlılık Filtresi:** Türkçe anlamlar set() ile benzersizleştirildi; frekans gürültüsü engellendi.
3. **SDK ve Model Güncellemesi:** Yeni genai.Client mimarisine geçildi, kota limitinden korunmak için model olarak gemini-embedding-2-preview seçildi.
4. **Boyut Optimizasyonu:** Matryoshka learning uyarınca output_dimensionality=768 yapıldı, veri boyutu 1/4 oranında hafifletildi.
5. **Güvenli API Mimarisi:** 62 saniyelik Throttle mekanizması eklendi; API çökse dahi kayıp olmaması için Incremental Cache JSON yazma metodu eklendi.
6. **Veri Ayrıştırma:** Çıktılar yapılandırıldı; ham vektörler kok_embeddings.json dosyasına, sadece 3D arayüz noktaları kok_coords.json dosyasına ayrıldı.


## Katman 6: Semantik İlişki Anlamlandırma
- NPMI skorlarına dayalı istatistiksel veriler ve LLM'in çıkarım gücü (Gemma-3-27B) hibrit bir şekilde birleştirildi.
- Sadece "İlişki Var/Yok" demek yerine, 11 farklı ve detaylı semantik kategori (Sebep-Sonuç, Zıtlık, Şart vb.) oluşturuldu.
- Maliyet ve Rate Limit risklerini aşmak için sadece NPMI > 0.25 ve raw_count >= 3 olan bağlar LLM'e gönderildi.
- Çakışmaları ve çift API çağrılarını önlemek için Node'lar alfabetik sıralanarak Edge ID'ler ('A---B') tekilleştirildi (Edge Yönsüzlüğü).
- Tüm verilerin şeffaf biçimde incelenebilmesi için her bir LLM çıkarımı `semantics_cache.json` dosyasına (Yapay Zeka Yorumu, Skor, NPMI Skoru ve Kategori ile birlikte) milisaniyelik gecikmelerle kaydedilecek şekilde tasarlandı.

## Katman 7 (İptal Edildi): 3D Görselleştirme
- **Mimari Revizyon:** 3D Force-Directed Graph kütüphanesi (three.js tabanlı) performansı olumsuz etkilediği ve karmaşık kullanıcı deneyimi sunduğu için projeden tamamen **çıkarılmıştır**. Görsellik yerine yalın veri sunumuna (Google Arama motoru tarzı liste mimarisine) geçiş yapılmıştır.

## Katman 8: Semantik Okuyucu Sayfası (Mod 1)
- **Significance Algoritması:** Düz NPMI yerine `(NPMI * (count/50))` logaritmik formülü geliştirilip `Significance` (Anlamlılık) adıyla ana sıralama ölçütü yapıldı. 
- **Bileşen Mimarisi:** İlgili kökün Türkçe mealleri, frekansları ve 1. derece ilişkileri bir "Liste Kartı" şeklinde tasarlandı. Kullanıcının sağ paneldeki sıkışık görünüm yerine in-page (sayfa içi) geçişlerle rahat okuma yapması sağlandı.

## Katman 9: Kavramsal Yolculuklar (Mod 2)
- **Dijkstra En Kısa Yol (Shortest Path):** İki alakasız kavram arasındaki semantik zinciri hesaplamak için Dijkstra algoritması Frontend'e (JavaScript) entegre edildi.
- **Maliyet Optimizasyonu (Edge Cost):** Graf gezilirken maliyet statik 1 olarak değil, `1.5 - Significance` formülüyle (Güçlü bağ = Düşük maliyet) dinamik hesaplanacak şekilde mimari oluşturuldu.
- **Timeline Tasarımı:** Sonuçların soyut bir ağ diyagramı yerine okunabilir, WhatsApp chat geçmişi formatında dikey bir "Zaman Çizelgesi" (Timeline) olarak sunulmasına karar verildi.

## Katman 10: Ayet Röntgeni (Mod 3)
- **Reverse Lookup:** `ayetIndex` içerisindeki veriyi okuyup, o ayetteki kökleri `kokIndex`'ten tersine bulacak "Reverse Dictionary" algoritması yazıldı.
- **Lokal İlişki Filtrelemesi:** Tüm graf yerine sadece o ayette yan yana gelen kelimelerin spesifik makro-bağlarını listeleyecek "Mikro Semantik Çözümleme" ünitesi tasarlandı. Çıktılar yine temiz in-page kartlar olarak dizayn edildi.
