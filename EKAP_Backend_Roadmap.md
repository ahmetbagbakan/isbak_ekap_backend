# EKAP Backend — Yol Haritası (Roadmap)

Projenin backend (.NET / C#) tarafını baştan sona adım adım gösteren yol haritası.
İşaretleme: [x] tamamlandı, [~] şu an burada, [ ] yapılacak.

---

## AŞAMA 1 — Kurulum ve temel yapı  ✅ (bitti)

- [x] 1.1 .NET SDK ve VS Code (C# Dev Kit eklentisi) kurulu
- [x] 1.2 `dotnet new webapi -n EkapBackend` ile Web API projesi oluşturuldu
- [x] 1.3 PostgreSQL kuruldu (Postgres.app), `ekap` adında boş veritabanı açıldı
- [x] 1.4 NuGet paketleri kuruldu:
        - Npgsql.EntityFrameworkCore.PostgreSQL
        - Microsoft.EntityFrameworkCore.Design

## AŞAMA 2 — Veri modeli (entity + DbContext)  ✅ (bitti)

- [x] 2.1 `Models/` klasörü + 4 entity sınıfı:
        Tender, TenderCharacteristic, TenderOkasCode, TenderAnnouncement
        (LLM alanları Tender içinde: IlgiSkoru, SirketeUygunMu, LlmOzeti, AnalizTarihi)
- [x] 2.2 `Data/EkapDbContext.cs` — DbSet'ler + ToTable + bire-çok ilişkiler

---

## AŞAMA 3 — Veritabanı bağlantısı  ⬅️ ŞU AN BURADAYIM

- [ ] 3.1 `appsettings.json` → ConnectionStrings > EkapDb (Host/Port/Database/Username/Password)
- [ ] 3.2 `Program.cs` → AddDbContext<EkapDbContext>(UseNpgsql(...)) + using satırları
- [ ] 3.3 `dotnet build` → "Build succeeded" ile doğrula

## AŞAMA 4 — Migration (PostgreSQL'de tabloları oluştur)

- [ ] 4.1 (Gerekirse) `dotnet tool install --global dotnet-ef`
- [ ] 4.2 `dotnet ef migrations add InitialCreate` → migration dosyası üretilir
- [ ] 4.3 `dotnet ef database update` → tablolar ekap veritabanında GERÇEKTEN oluşur
- [ ] 4.4 Doğrulama: DBeaver/psql ile ekap içinde 4 tablonun oluştuğunu gör (boş)

## AŞAMA 5 — Veri aktarımı (SQLite → PostgreSQL)

- [ ] 5.1 Karar: iş anahtarı `ikn` mi `id` mi? (duplicate kontrolü için) — Python ekibiyle netleştir
- [ ] 5.2 SQLite (ekap_ihaleler.db) verisini PostgreSQL'e taşı
        (tek seferlik aktarım scripti VEYA ileride import endpoint'i)
- [ ] 5.3 Doğrulama: PostgreSQL'de kayıt sayısı SQLite ile eşleşiyor mu (47.001 tender)

---

## AŞAMA 6 — İlk API endpoint'leri (okuma)

- [ ] 6.1 `Controllers/IhaleController.cs` oluştur
- [ ] 6.2 GET /api/ihaleler → ihaleleri listele (sayfalama ile, hepsini birden döndürme)
- [ ] 6.3 GET /api/ihaleler/{ikn} → tek ihale detayı (characteristics + okas + announcements dahil)
- [ ] 6.4 Swagger'da test et (dotnet run → /swagger)

## AŞAMA 7 — Filtreleme (asıl iş değeri)

- [ ] 7.1 GET /api/ihaleler?il=...&tur=...&durum=...&baslangic=...&bitis=...
        (il, ihale türü, durum, tarih aralığı, anahtar kelime filtreleri)
- [ ] 7.2 Sayfalama + sıralama (tarihe göre vb.)

## AŞAMA 8 — LLM entegrasyon noktası

- [ ] 8.1 PUT /api/ihaleler/{ikn}/analiz → LLM'in IlgiSkoru, SirketeUygunMu, LlmOzeti yazması
- [ ] 8.2 GET /api/ihaleler?minSkor=... → skora göre filtreleme (frontend "uygun ihaleler" listesi)
- [ ] 8.3 Karar: LLM API üzerinden mi yazsın, DB'ye doğrudan mı? (API önerilir)

## AŞAMA 9 — Veri besleme akışı (Python ↔ Backend)

- [ ] 9.1 POST /api/ihaleler/import → Python'un yeni ihaleleri JSON gönderdiği endpoint
- [ ] 9.2 Duplicate kontrolü (ikn üzerinden) — aynı ihale iki kez yazılmasın
- [ ] 9.3 Karar: Python periyodik mi besleyecek, tek seferlik mi?

## AŞAMA 10 — Son rötuşlar

- [ ] 10.1 CORS ayarı (frontend başka porttan çağırabilsin)
- [ ] 10.2 Hata yönetimi (uygun HTTP kodları: 404, 400 vb.)
- [ ] 10.3 (Opsiyonel) N-layer'a geçiş: iş mantığını Services/ katmanına taşı
- [ ] 10.4 (Opsiyonel) Temel testler

---

## Notlar

- Her aşamada: önce ne/neden yapıldığı anlaşılsın, sonra uygulansın. Otomatik geçme yok.
- SQLite verisi kurum verisi — buluta/online araçlara yüklenmez, yerel işlenir.
- C#/.NET yeni öğreniliyor → kavramlar (class, property, EF Core, migration vb.) yeri geldikçe açıklanacak.
- Bu dosyayı ilerledikçe güncelle: tamamlananı [x], bulunduğun yeri [~] yap.

## Ekiple netleşmesi gereken kararlar (özet)

1. İş anahtarı: ikn mi id mi?
2. Python veriyi nasıl besleyecek: dosya mı, import endpoint'i mi?
3. LLM skoru nasıl yazacak: API mi, doğrudan DB mi?
