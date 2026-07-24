# EKAP Backend — Yol Haritası (Güncel)

Backend (.NET / C#) tarafının adım adım yol haritası.
İşaretleme: [x] tamamlandı, [~] şu an burada, [ ] yapılacak.

**Önemli karar:** Backend, ekibin ORTAK PostgreSQL veritabanına bağlanıyor
(Host: 192.168.100.42, DB: isbak_ekap_db). Tabloları Python ekibi oluşturdu.
Bu yüzden MIGRATION ÇALIŞTIRILMIYOR — sadece bağlanıp okuma/yazma yapılıyor.
(Erişim için İŞ ağında / VPN'de olmak gerekir.)

---

## AŞAMA 1 — Kurulum ve temel yapı  ✅

- [x] .NET SDK + VS Code (C# Dev Kit)
- [x] `dotnet new webapi -n EkapBackend` — Web API iskeleti
- [x] PostgreSQL (ekip ortak sunucusu, isbak_ekap_db)
- [x] NuGet: Npgsql.EntityFrameworkCore.PostgreSQL + Microsoft.EntityFrameworkCore.Design

## AŞAMA 2 — Veri modeli (entity + DbContext)  ✅

- [x] Models/ → 4 entity: Tender, TenderCharacteristic, TenderOkasCode, TenderAnnouncement
       (Tender içinde LLM alanları: IlgiSkoru, SirketeUygunMu, LlmOzeti, AnalizTarihi)
- [x] Data/EkapDbContext.cs → DbSet'ler + ToTable + bire-çok ilişkiler

## AŞAMA 3 — Veritabanı bağlantısı  ✅

- [x] appsettings.json → ConnectionStrings > DefaultConnection (ortak DB bilgileri)
       (appsettings.json .gitignore'da — şifre repoya gitmiyor)
- [x] Program.cs → AddDbContext<EkapDbContext>(UseNpgsql(...)) + using satırları
- [x] `dotnet build` → başarılı (Build succeeded)

---

## AŞAMA 4 — Modelleri gerçek tabloyla eşleştir + bağlantı testi  ⬅️ ŞU AN BURADAYIM

Migration YOK. Bunun yerine: modellerin gerçek tablolara oturduğunu doğrula.

- [ ] 4.1 Gerçek tablo/sütun isimlerini teyit et
       (Python'cunun SQLite'ındakiyle aynı mı: tenders, tender_characteristics,
        tender_okas_codes, tender_announcements?)
- [ ] 4.2 Basit test controller'ı yaz (örn. GET /api/ihaleler → ilk 10 ihale)
- [ ] 4.3 `dotnet run` → uygulamayı çalıştır
- [ ] 4.4 Tarayıcı/Swagger'da endpoint'i aç → gerçek veri geliyor mu gör
       (Bağlantı + model eşleşmesi burada kanıtlanır)
- [ ] 4.5 Hata çıkarsa: model/sütun isimlerini gerçek tabloya göre düzelt

## AŞAMA 5 — Okuma endpoint'leri (temel API)

- [ ] 5.1 Controllers/IhaleController.cs
- [ ] 5.2 GET /api/ihaleler → sayfalama ile liste (hepsini birden döndürme!)
- [ ] 5.3 GET /api/ihaleler/{ikn} → tek ihale detayı
       (characteristics + okas kodları + ilanlar dahil — Include ile)
- [ ] 5.4 Swagger'da test

## AŞAMA 6 — Filtreleme (asıl iş değeri)

- [ ] 6.1 GET /api/ihaleler?il=...&tur=...&durum=...&baslangic=...&bitis=...
       (il, ihale türü, durum, tarih aralığı, anahtar kelime)
- [ ] 6.2 Sayfalama + sıralama (tarihe göre vb.)

## AŞAMA 7 — LLM entegrasyon noktası

- [ ] 7.1 PUT /api/ihaleler/{ikn}/analiz → LLM'in IlgiSkoru, SirketeUygunMu, LlmOzeti yazması
- [ ] 7.2 GET /api/ihaleler?minSkor=... → skora göre filtrele (frontend "uygun ihaleler")
- [ ] 7.3 Karar: LLM API üzerinden mi yazsın, DB'ye doğrudan mı? (API önerilir)

## AŞAMA 8 — Son rötuşlar

- [ ] 8.1 CORS ayarı (frontend başka porttan çağırabilsin)
- [ ] 8.2 Hata yönetimi (404, 400 gibi uygun HTTP kodları)
- [ ] 8.3 Microsoft.OpenApi paketini güncelle (NU1903 güvenlik uyarısı)
- [ ] 8.4 appsettings.example.json ekle (ekip için şifresiz örnek ayar)
- [ ] 8.5 (Opsiyonel) İş mantığını Services/ katmanına taşı (N-layer)

---

## Teknoloji özeti

- Dil/platform: C# / ASP.NET Core Web API (.NET 10)
- Veritabanı: PostgreSQL (ekip ortak sunucusu, isbak_ekap_db @ 192.168.100.42)
- ORM: Entity Framework Core + Npgsql
- Editör: VS Code
- Repo: github.com/ahmetbagbakan/isbak_ekap_backend (branch: dev)

## Ekiple netleşecek kararlar

1. Gerçek tablo/sütun isimleri SQLite'takiyle birebir aynı mı?
2. İş anahtarı ikn mi id mi? (Python'da ON CONFLICT ikn UNIQUE kullanılmış — muhtemelen ikn)
3. LLM skoru nasıl yazacak: API mi, doğrudan DB mi?
4. appsettings ekip içinde nasıl paylaşılacak? (example dosyası)

## Git alışkanlığı (hatırlatma)

- Anlamlı iş bitince commit, günün sonunda / aşama bitince push.
- Push'tan ÖNCE her zaman: git pull origin dev
- appsettings.json ve .env repoya GİTMEZ (şifre içerir, gitignore'da).
