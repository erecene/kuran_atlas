# Kurulum ve Çalıştırma Rehberi

Kur'an Kavram Atlası, tamamen **istemci tarafında (Frontend)** çalışan, arka plan sunucusuna (Node.js, PHP, Python Flask vb.) veya bir veritabanı kurulumuna ihtiyaç duymayan statik bir uygulamadır.

Veriler devasa yapay zeka betikleriyle önceden işlenip `json` formatına getirildiği için uygulamanın kendisi sadece bir HTML sayfası (`kuran_atlas.html`) ve o okunan klasörlerden ibarettir.

**Ancak güvenlik nedenleriyle (CORS Origin politikası), modern tarayıcılar yerel bilgisayarınızdaki `file://` protokolü üzerinden JSON dosyalarının okunmasına izin vermez.** Bu yüzden projeyi çift tıklayarak *açamazsınız*; çok basit bir yerel sunucu (Localhost) başlatmanız gerekir.

Aşağıdaki adımları izleyerek projeyi 10 saniye içinde çalıştırabilirsiniz:

### Gereksinimler

- Bilgisayarınızda **Python** yüklü olmalıdır. (Python 3.x tavsiye edilir)
  - Yüklü olup olmadığını anlamak için Terminal veya Komut İstemcisi'ne (CMD) `python --version` yazabilirsiniz.
- Modern bir web tarayıcısı (Google Chrome, Safari, Firefox, Edge vb.).

---

### Adım Adım Kurulum

**1. Proje Dosyalarını İndirin**
Eğer projeyi Github'dan indiriyorsanız, yeşil "Code" butonuna basıp "Download ZIP" diyerek indirebilir veya terminalden klonlayabilirsiniz:
```bash
git clone https://github.com/KULLANICI_ADINIZ/kuran_atlas.git
```
Dosyaları masaüstüne veya dilediğiniz bir klasöre çıkarın.

**2. Terminal / Komut Satırını Açın**
Windows'ta arama çubuğuna `cmd` veya `powershell` yazarak, Mac'te ise `Terminal`'i açarak projenin bulunduğu dizine gidin (Klasörün içine girin). 
Örneğin dosyaları masaüstüne Kur'an_atlas adıyla çıkardıysanız:
```bash
cd Desktop/kuran_atlas
```

**3. Yerel Sunucuyu Başlatın**
Proje klasörünün içindeyken aşağıdaki sihirli Python komutunu yazın ve Enter'a basın:
```bash
python -m http.server 8080
```
Eğer Mac/Linux kullanıyorsanız ve python komutu çalışmazsa `python3` olarak deneyin:
```bash
python3 -m http.server 8080
```

Ekrana şöyle bir çıktı gelecektir:
`Serving HTTP on :: port 8080 (http://[::]:8080/) ...`
Bu, bilgisayarınızda geçici ve güvenli bir sunucunun başarıyla açıldığını gösterir.

**4. Atlas'a Giriş Yapın**
Şimdi favori internet tarayıcınızı (Google Chrome, Edge vs.) açın ve adres çubuğuna şunu yazın:

`http://localhost:8080/kuran_atlas.html`

Ve Enter'a basın. Karşınıza **Kur'an Kavram Atlası** çıkacaktır! 🎉

*(Sunucuyu kapatmak isterseniz Terminal ekranındayken `CTRL + C` tuş kombinasyonuna basmanız yeterlidir).*
