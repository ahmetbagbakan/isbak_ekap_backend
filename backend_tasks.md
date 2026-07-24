# ISBAK EKAP — Backend Görev Takip Listesi (Tasks)

Bu doküman, projenin backend tarafındaki tüm görevleri **Ahmet**, **Atalay** ve **Eren** arasındaki sorumluluk dağılımına göre güncellenmiş takip listesidir.

---

## 📌 Durum ve Sorumluluk Özet Tablosu

| Aşama | Başlık | Sorumlu | Durum |
|---|---|---|---|
| **Aşama 1** | Veritabanı & Temel Yapılandırma | **Atalay** | 🟡 Devam Ediyor |
| **Aşama 2** | DTO Katmanı | **Ahmet** | 🟢 Tamamlandı |
| **Aşama 3** | Repository Katmanı | **Eren** | ⚪ Bekliyor |
| **Aşama 4** | Service Katmanı | **Atalay** | ⚪ Bekliyor |
| **Aşama 5** | Controller & Middleware Katmanı | **Atalay & Eren** | ⚪ Bekliyor |
| **Aşama 6** | Swagger & Test Doğrulama | **Ekip (Atalay, Eren, Ahmet)** | ⚪ Bekliyor |

---

## 🎯 AŞAMA 1 — Veritabanı Hazırlığı & Proje Konfigürasyonu (Atalay)

- [x] **1.1 Veritabanı Sütun Ekleme**: `tenders` tablosuna `takip_durumu` TEXT sütunu eklendi (`ALTER TABLE tenders ADD COLUMN IF NOT EXISTS takip_durumu TEXT;`).
- [ ] **1.2 C# Model Sınıfı Güncelleme (Atalay)**: `Models/Tender.cs` içinde `DetayCekildi` alanının temizlenmesi ve `TakipDurumu` alanının kontrolü.
- [ ] **1.3 `EFCore.NamingConventions` Paket Kurulumu (Atalay)**: Terminalden `dotnet add package EFCore.NamingConventions` çalıştırılacak.
- [ ] **1.4 `EkapDbContext.cs` Güncellemesi (Atalay)**: `.UseSnakeCaseNamingConventions()` seçeneği entegre edilecek.
- [ ] **1.5 `Program.cs` Temel Yapılandırması (Atalay)**: DbContext, Swagger ve CORS servis kayıtları tamamlanacak.
- [ ] **1.6 İlk Derleme Doğrulaması (Atalay)**: `dotnet run` çalıştırılıp projenin hatasız kalktığı doğrulanacak.

---

## 📦 AŞAMA 2 — DTO (Data Transfer Object) Katmanı (Ahmet - 🟢 TAMAMLANDI)

- [x] **2.1 `DTOs/TenderListDto.cs` (Ahmet)**: İhale arama ve liste ekranı için özet alanlar (İKN, Adı, İl, Tarih, Tür, Skoru, TakipDurumu).
- [x] **2.2 `DTOs/TenderDetailDto.cs` (Ahmet)**: Tek ihale detayı ekranı için tam veri (İlanlar, OKAS Kodları, Özellikler, TakipDurumu).
- [x] **2.3 `DTOs/TenderAnalysisDto.cs` (Ahmet)**: Yapay zekanın (LLM) skor gönderimi için DTO (`IlgiSkoru`, `SirketeUygunMu`, `LlmOzeti`).
- [x] **2.4 `DTOs/TenderDurumDto.cs` (Ahmet)**: Satış ekibinin etiket güncellemesi için DTO (`TakipDurumu`: "inceleniyor", "alınması öneriliyor", "alınması önerilmiyor").
- [x] **2.5 `DTOs/PagedResultDto.cs` (Ahmet)**: Sayfalamalı veri zarfı (`Veriler`, `ToplamKayit`, `ToplamSayfa`, `MevcutSayfa`).
- [x] **2.6 `DTOs/FilterOptionsDto.cs` (Ahmet)**: Dropdown seçenekleri için DTO (`Iller`, `Turler`, `Durumlar`).

---

## 🗄️ AŞAMA 3 — Repository (Veri Erişimi) Katmanı (Eren)

- [ ] **3.1 `Repositories/TenderFilter.cs` (Eren)**: Filtreleme sorgusu parametre sınıfı (`Il`, `Tur`, `Durum`, `Kelime`, `MinIlgiSkoru`, `TakipDurumu`, `Sayfa` vb.).
- [ ] **3.2 `Repositories/ITenderRepository.cs` (Eren)**: Veri katmanı arayüzünün (interface) yazılması.
- [ ] **3.3 `Repositories/TenderRepository.cs` (Eren)**:
  - [ ] `GetAllAsync(TenderFilter filter)` (Filtreleme + Sayfalama + Sıralama).
  - [ ] `GetByIknAsync(string ikn)` (`.Include()` ile ilişkili tabloları çekme).
  - [ ] `UpdateAnalysisAsync(string ikn, TenderAnalysisDto dto)`.
  - [ ] `UpdateDurumAsync(string ikn, TenderDurumDto dto)`.
  - [ ] Distinct İl, Tür ve Durum çeken metotlar.

---

## ⚙️ AŞAMA 4 — Service (İş Mantığı) Katmanı (Atalay)

- [ ] **4.1 `Services/ITenderService.cs` (Atalay)**: Servis arayüzünün yazılması.
- [ ] **4.2 `Services/TenderService.cs` (Atalay)**:
  - [ ] `GetIhaleListesiAsync()` (Entity ➔ TenderListDto dönüşümü).
  - [ ] `GetIhaleDetayiAsync()` (Entity ➔ TenderDetailDto dönüşümü).
  - [ ] `UpdateIhaleAnaliziAsync()` (LLM skor kaydı).
  - [ ] `UpdateIhaleDurumuAsync()` (Takip etiketi kaydı).
  - [ ] `GetFilterSeçenekleriAsync()` (Dropdown verilerinin hazırlanması).

---

## 🌐 AŞAMA 5 — Controller (API) & Middleware Katmanı (Atalay & Eren)

- [ ] **5.1 `Middleware/ExceptionMiddleware.cs` (Atalay & Eren)**: Beklenmeyen hataları yakalayan global hata yönetimi middleware'i.
- [ ] **5.2 `Controllers/IhaleController.cs` (Atalay & Eren)**:
  - [ ] `GET /api/ihaleler` ➔ Liste & Filtreleme endpoint'i.
  - [ ] `GET /api/ihaleler/{ikn}` ➔ İhale Detay endpoint'i.
  - [ ] `PUT /api/ihaleler/{ikn}/analiz` ➔ Yapay Zeka Skor kayıt endpoint'i.
  - [ ] `PUT /api/ihaleler/{ikn}/durum` ➔ Satış Ekibi Takip Etiketi kayıt endpoint'i.
  - [ ] `GET /api/ihaleler/filtre-secenekleri` ➔ Dropdown verileri endpoint'i.

---

## 🧪 AŞAMA 6 — Doğrulama ve Swagger Testleri (Atalay, Eren & Ahmet)

- [ ] **6.1 Swagger Arayüzü Testi**: `http://localhost:5086/swagger` üzerinden uç noktaların denenmesi.
- [ ] **6.2 Filtreleme Testleri**: İl, Tür, MinSkor ve TakipDurumu filtrelerinin PostgreSQL üzerinde doğru çalıştığının doğrulanması.
- [ ] **6.3 CORS Testi**: React frontend uygulamasının API'ye istek atabildiğinin teyit edilmesi.
