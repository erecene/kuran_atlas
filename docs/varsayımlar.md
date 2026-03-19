# Varsayımlar ve Kabuller

## Katman 0: Sistem Temeli
- Tüm sistemin proje ana dizini olan `c:\Users\EnginSu\Desktop\kuran_atlas` hedef alınarak inşa edildiği varsayılmıştır.
- Tüm çalışmanın omurgası olan `meal_full.csv` adlı ham verinin, sistem Katman 1'i işlemeye başlamadan önce kullanıcı tarafından `data_raw` klasörünün altına atılacağı varsayılmıştır.
- Python dili ve uygun Python pip ortamının (sürümleriyle birlikte) dış ortamda kullanıcının makinesinde yüklü veya yüklenmeye hazır olduğu kabul edilmiştir. Yeri geldiğinde bu kütüphaneler talep edilecektir.

## Katman 1: Veri İndeksleme
- **CSV Sütun Şeması:** Mevcut örnekte olduğu gibi formatın kesinlikle şu sırada olduğu kabul edilmiştir: `Sure_No` (0), `Sure_Adı` (1), `Ayet_No` (2), `Arapça` (3), `Meal` (4), `Kökler` (5). Sütunların yer değiştirmesi veya silinmesi scripti bozabilir.
- **Kök Formatsızlığı:** Parantez ve Regex haricinde verinin farklı bir dil ile (örn; "smw [سمو]") girilmediği varsayılmıştır. Parantez yapısı korunduğu sürece kod temiz çalışacaktır.
- **Tekil ID Mantığı:** Kur'an'da 6236 ayetten başka bir satır bulunmadığı, `Sure_No:Ayet_No` (örn 2:177) anahtarının her satırda eşsiz bir ID (Primary Key) üreteceği, duplicate olan satırların bilerek veya yanlışlıkla kopyalanmış atıl veriler olduğu (uyarı verilip atlanacağı) kabul edilmiştir.

## Katman 2: Kök Sözlüğü
- **Anlam Sabitliği:** Kök sözlüğündeki (örn. K-T-B) çevirilerin, Kur'an'ın genelindeki kullanımları kapsayacak kadar yeterli olduğu kabul edilmiştir. Çok spesifik metaforik kaymalar sözlüğün değil, ilerideki LLM analizinin (Katman 6) ve kullanıcının görevi kabul edilmiştir.
- **Normalizasyon:** Büyük/küçük harf veya boşluk hatalarının (Gök, gök) aynı anlama geldiği ve normalize edilmesinin anlam kaybı yaratmayacağı varsayılmıştır.

## Katman 3: Kavram Frekans ve Haritalaması
- **Konusal Temsil:** Bir ayetin içinde bir kökün geçmesinin, o ayetin içeriğinin doğrudan o kavramla güçlü şekilde ilgili olduğunu gösterdiği varsayılmıştır.
- **Frekans Düzleştirmesi (Bias Koruması):** İlerideki Network grafiğinde yanıltıcı merkezler (Hub) oluşmasını engellemek için, bir ayette aynı kelimenin 3 defa geçmesi "1 kez beraber görülme" (`Set` mantığı) olarak düzleştirilmiş ve bu durumun veri kaybı değil, istatistiksel sağlık olduğu kabul edilmiştir.

## Katman 4: Ko-okürrans ve İstatistiksel Ağ
- **Bilinçli Tasarım Varsayımı (Projenin Kalbi):** Kur'an'da iki farklı kelimenin (örneğin "Güneş" ve "Ay" veya "Dünya" ve "Ahiret") aynı ayet bağlamında sıkça yan yana gelmesinin rastgele bir dil alışkanlığı değil, ilahi bir semantik/matematiksel tasarım olduğu varsayılmıştır.
- **Uzun Ayet Normalizasyonu:** Bakara 282 gibi çok uzun ayetlerdeki her kelimenin birbiriyle eşit derecede anlamsal bağ kuramayacağı öngörülmüştür. Bu yüzden matematiksel olarak `1 / (Kelime Sayısı - 1)` formulüyle uzun ayetlerin ağırlıkları bilinçli olarak düşürülmüş ve kısa ayetlerin keskinliği daha güvenilir kabul edilmiştir.

## Katman 5: Embedding Üretimi
- **LLM Kavrama Yeteneği:** Embedding modelinin, kelimenin sadece saf Türkçe anlamına bakarak değil, bizlerin yanına eklediği "3 bağlam ayeti (context)" ile o kelimenin derin teolojik anlamını 768 boyutlu bir vektöre (koordinata) doğru bir şekilde çevirebildiği varsayılmıştır.
- **UMAP Normalizasyonu:** 768 boyutlu çok kompleks bir uzayın 3 boyuta (X, Y, Z) sıkıştırılmasının (UMAP) ufak tefek geometrik sapmalara yol açsa da genel topolojiyi (yapıyı) bozmadığı kabul edilmiştir.

## Katman 6: Semantik İlişki Anlamlandırma
- **LLM Doğruluğu:** Gemma-27B modelinin, sadece kelime ve kısa ayet bağlamından yola çıkarak Kur'an içi kavramsal ilişkileri 11 kategoride (Sebep-Sonuç, Zıtlık vb.) %80+ isabetle tasnif edebildiği varsayılmıştır.
- **NPMI Güvenilirliği:** Sadece istatistiksel açıdan güçlü olan (NPMI > 0.25) kelimelerin LLM'e gönderilmesinin, LLM halüsinasyonlarını kökten keseceği kabul edilmiştir.

---

## Katman 8: Semantik Okuyucu Sayfası (Mod 1)
- **Kullanıcı Deneyimi:** 3D görselleştirmenin (Katman 7) karmaşıklık yarattığı, kullanıcıların "Google benzeri" düz metin ve liste hiyerarşisi üzerinden veriyi çok daha rahat analiz ettiği varsayılıp tasarım buna göre şekillendirilmiştir.
- **Significance Skoru Sabitliği:** NPMI x (Frekans/50) şeklindeki logaritmik formülün ilişkinin önem derecesini sıralamak için en adil matematik modeli olduğu kabul edilmiştir.

## Katman 9: Kavramsal Yolculuklar (Mod 2)
- **Dijkstra Transitive Anlam:** Kur'an'da A'dan B'ye, B'den C'ye bir semantik bağ varsa; Dijkstra'nın A'dan C'ye bulduğu en kısa rotanın (A->B->C) tesadüfi değil, Kutsal Kitabın kendi iç felsefi iskeletini yansıttığı varsayılmıştır.
- **Mesafe Maliyeti:** `1.5 - Significance` formülünün kısa yolları bulmak için yeterince hassas bir ağırlık dengelemesi sağladığı kabul edilmiştir.

## Katman 10: Ayet Röntgeni (Mod 3)
- **Lokal İlişki İzolasyonu:** Bütün grafiği bir anda görmek yerine tek bir ayete (Örn: Bakara 255) odaklanıp sadece oradaki kelimelerin evrensel çapraz bağlarına bakmanın, tefsir ve meallerden çok daha yapısal bir okuma sağlayacağı varsayılmıştır.
