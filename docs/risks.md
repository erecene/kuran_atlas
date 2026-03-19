# Teknik ve Operasyonel Risk Analizi

## Katman 0: Altyapı Riskleri
- **Veri Kaybı ve Ham Veri Bozulması:** İşlem adımlarında yanlışlıkla `data_raw` altındaki dosyanın üzerine yazılması veri bütünlüğünü tehdit eder.
  - **Alınan Önlem:** Yazılacak olan Python scriptlerinde `data_raw` dosyası her türlü işleme karşı kati suretle "Salt Okunur" (read mode `r`) olarak açılacaktır. Hiçbir dosyaya `w` modu yetkisi `data_raw` içinde verilmeyecektir.
- **Git / Repo Şişmesi Riski:** Üretilecek JSON (graph indexleri) ve Embedding datalarının (n boyutlu diziler) megabaytlarca yeri kaplayıp versiyon kontrol sistemlerinde şişme yaşatması riski mevcuttur.
  - **Alınan Önlem:** Büyük veri yapıları (`graph_data` ve `embeddings` vb.) için ileride ihtiyaç dahilinde bir `.gitignore` dosyası oluşturulması gerekebilir.

## Katman 1: Ayet Veri İndeksi Riskleri
1. **Dengesiz CSV Formatı (Formatting Errors)**
   - **Risk:** Kullanıcının sağladığı `meal_full.csv` dosyasında sütun kaymaları, eksik tırnak işaretleri veya encoding hataları olması parse işlemlerini çökertir.
   - **Alınan Önlem:** Python `csv` modülü `utf-8-sig` encoding ile çalıştırılarak BOM hataları önlendi. Hatalı satırlar es geçilip loglandı. Parantez içindeki kökleri ayıklamak için sadece ingilizce karakterleri seçen `r'^([A-Za-z$]+)\s*\(.*?\)\s*:'` regex kontrolü kuruldu.

## Katman 2: Kök Sözlüğü Riskleri
1. **Arapça ve Türkçe Uyumsuzluğu ve Kirliliği**
   - **Risk:** Aynı kökün farklı ayetlerde farklı harf büyüklüklerinde ("Gök", " gök") yazılması kümelemede enflasyon yaratır.
   - **Alınan Önlem:** Türkçe anlamların tamamı `.lower()` ve `.strip()` ile temizlendi. Ayrıca haritalamada (Katman 3) hiç eşleşmeyen "hayalet kökler" graf sisteminin dışında bırakıldı.

## Katman 3: Haritalama Riskleri
1. **Tekil Ayet İçi Frekans Şişmesi (Hub Bias)**
   - **Risk:** Bir ayet içerisinde aynı kökün defalarca tekrarlaması, graf hesaplamalarında o düğümü suni olarak aşırı popüler gösterebilir.
   - **Alınan Önlem:** `ayet_to_kokler` haritası oluşturulurken, kök listesi `sorted(set())` işleminden geçirildi. Aynı kökün bir ayette 5 kere geçmesi "1 kez geçti" olarak normalize edildi.

## Katman 4: Ko-okürrans ve Graf Riskleri
1. **Uzun Ayetlerin Grafı Zehirlemesi**
   - **Risk:** Bakara 282 gibi çok uzun ayetlerde (47 farklı kök), sıradan bir sayımla tek ayetten 1081 adet sahte bağlantı doğar ve gürültü yaratır.
   - **Alınan Önlem:** `1/(Kelime_Sayısı - 1)` formülüyle ağırlık bölündü. Kısa ayetlerde kelimelerin yan yana gelmesi net bir bağ sayılırken, devasa ayetlerdeki puan etkisi ciddi oranda seyreltildi.
2. **Çok Sık Geçen Kelimelerin (Allah, İman) Anlamı Yok Etmesi (Stop-word Etkisi)**
   - **Risk:** En çok kullanılan köklerin rastgele her kelimeyle graf merkezinde toplanması.
   - **Alınan Önlem:** Matematiksel bir filtre olan **PMI (Pointwise Mutual Information)** istatistiği uygulandı. Yaygın kelimelerin puanı cezalandırılarak düşürüldü; "Güneş-Ay" gibi sadece nadir ve birlikte geçen kelimelerin anlamsal skoru tavan yaptı.


## Katman 5: Embedding Üretimi Riskleri

1. **API Kotası Kaynaklı Kesintiler (429 Rate Limit)**
   - **Risk**: Google'ın ücretsiz paketinde dakikada 100 metin veya günlük 1000 ağ (request) limiti aşılabilir.
   - **Alınan Önlem**: Koda 90 kavramda bir 62 saniyelik agresif uyuma döngüsü (`Throttle`) ve API hata verdiği an fazladan 65 saniyelik kurtarma beklemesi eklendi. Çökme olsa dahi veri bir JSON cache (`embeddings_cache.json`) üzerinde satır satır yedekli tutulmaktadır.

2. **Çok Anlamlılığın Cümle Bağlamını Bozması (Polysemy)**
   - **Risk**: Türkçedeki tekrar eden veya farklı kullanımları olan anlamlar (Örn: bilmek/alim vs. işaret) modele tek boyutlu gönderildiğinde anlamsal gürültü yaratabilir.
   - **Alınan Önlem**: Anlamlar `set()` ile kümelenerek sadeleştirildi. Ek olarak saf kelime yerine Kur'an'dan otomatik seçilmiş 3 ayet de bağlam (context window) olarak prompta eklendi.
   
3. **3D Boyut (UMAP) Görsellerinin Çökmesi (Topolojik Veri Kaybı)**
   - **Risk**: 768 boyut yüksek bir veri setidir, bu 3 boyuta (X,Y,Z) sıkıştırıldığında veriler anlamsızca üst üste binebilir veya çok dar bir skalaya hapsolabilir.
   - **Alınan Önlem**: Algoritmik istikrar için L2 Normalizasyon (Cosine distance stabilization) uygulandı. Ayrıca HTML formatında görüntü bozulmasın diye UMAP `coords_3d * 10.0` ile ölçeklendirilip yayvanlaştırıldı. Ek olarak `n_neighbors` değeri kök sayısının ortalama kareköküne (35) çekilerek global yapı korundu.

## Katman 6: LLM Semantik Analiz Riskleri

1. **Google API Rate Limit (30 RPM) ve Günlük Kotalar**
   - **Risk:** Gemma-3-27B modeli için dakikada sadece 30 istek sınırı mevcuttur.
   - **Alınan Önlem:** `ThreadPoolExecutor` ile 3 paralel işçi (worker) ayarlandı. Her işlem sonuna zorunlu `time.sleep(10.0)` eklendi (Dakikada max ~18 istek). İstisnai durumlarda (429 Kotası) 65 saniyelik agresif beklemeler eklendi. Cache sistemi kullanılarak her 20 işlemde bir dosya yedeği (save) alındı.

2. **Context Window Sınırı ve LLM "Ortada Kaybolma" (Lost in Middle) Sorunu**
   - **Risk:** İki kelimenin ortak geçtiği tüm ayetlerin (Örn: 50 ayet) LLM'e tek seferde verilmesi, modelin bağlamı kaybetmesine veya "Invalid Argument" hatasına (15.000 Token dolumu) sebep olabilir.
   - **Alınan Önlem:** Ayetler uzunluğuna göre küçükten büyüğe sıralandı ve sadece **en kısa 3 ayet** prompt içine dâhil edilerek LLM'in tamamen odaklanması sağlandı.

3. **JSON Mode Desteklenmemesi**
   - **Risk:** Gemma-3-27B modelinin `application/json` yanıt tipini doğrudan desteklememesi sonucu parse (ayrıştırma) işlemlerinin çökmesi.
59.    - **Alınan Önlem:** API config ayarlarından JSON Mode çıkarıldı. Prompt, tamamen metinsel çıktı verecek şekilde katılaştırıldı ve prompt içine örnek JSON formatı eklendi. Dönen metin, Python içinde regex ve string temizleme (`startswith("\`\`\`json")`) işlemlerinden geçirilerek koda gömüldü.

---

## Katman 8: Semantik Okuyucu Sayfası (Mod 1)
- **Mobil Uyumsuzluk Riski:** Geniş ekranlar için tasarlanan liste kartlarının telefonlarda taşması ihtimali `max-width` CSS kısıtlamalarıyla çözülmüştür.
- **Veri Yükleme (Fetch) Engeli:** Tarayıcıların güvenlik politikaları (CORS) gereği `file://` protokolünden JSON okutmamaları nedeniyle sistem kitlenebilir. Bu nedenle `http.server` üzerinden localhost başlatılması bir ön gereksinim olarak `KURULUM.md` dosyasına yazılmıştır.

## Katman 9: Kavramsal Yolculuklar (Mod 2)
- **Sonsuz Döngü ve Limit Patlaması Riski:** Dijkstra algoritmasının çok alakasız iki kelime (Örn: "Karınca" ve "Uzay") arasında rota bulmaya çalışırken tüm tarayıcıyı dondurması riski mevcuttur.
- **Alınan Önlem:** Algoritmaya maksimum derinlik sınırı (`maxDepthLimit = 5`) eklenerek, 5 adımdan uzun bağlantılar kestirilip atılmış ve uyarı mekanizması konulmuştur. Böylece tarayıcı çökmesi (Crash) engellenmiştir.

## Katman 10: Ayet Röntgeni (Mod 3)
- **Boş Sonuç Riski:** Seçilen ayette (Örn: kısa bir ayet) yeterli kök olmaması veya olan köklerin Kur'an genelinde güçlü bir makro-bağa sahip olmaması arayüzde kırık veya boş görünüm yaratabilir.
- **Alınan Önlem:** Dinamik if/else bloklarıyla "Bu ayette yapısal ikili bağ tespit edilemedi" şeklinde zarif null-state mesajları arayüze eklenmiştir.
