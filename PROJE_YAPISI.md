# Proje İskeleti — isbak_ekap_backend

Bu dosya, projedeki klasör ve dosyaların ne işe yaradığını açıklar.
Repo iki ana bölümden oluşur: **.NET Backend (C#)** ve **Python Scraper**.

---

## Genel yapı

```
isbak_ekap_backend/
│
├── .NET BACKEND (C# / ASP.NET Core Web API)  ← Atalay'ın alanı
│   ├── Models/                  → Veritabanı tablolarını temsil eden C# sınıfları (entity)
│   │   ├── Tender.cs               → Ana ihale + ilişkiler + LLM alanları
│   │   ├── TenderCharacteristic.cs → İhale özellikleri (E-İhale, Yerli İstekli vb.)
│   │   ├── TenderOkasCode.cs       → OKAS ürün/hizmet sınıflandırma kodları
│   │   └── TenderAnnouncement.cs   → İhale ilanları (başlık, içerik)
│   │
│   ├── Data/                    → Veritabanı erişim katmanı
│   │   └── EkapDbContext.cs         → EF Core köprüsü (DbSet'ler + ilişkiler)
│   │
│   ├── Controllers/             → (henüz yok) API endpoint'leri buraya gelecek
│   │
│   ├── Program.cs               → Uygulamanın başlangıç noktası (servis kaydı, DbContext tanıtımı)
│   ├── appsettings.json         → Ayarlar (connection string buraya) [gitignore'da]
│   ├── appsettings.Development.json → Geliştirme ayarları [gitignore'da]
│   ├── EkapBackend.csproj       → Proje dosyası (paketler, .NET sürümü)
│   ├── EkapBackend.sln          → Solution dosyası (projeyi açan üst kapsayıcı)
│   ├── EkapBackend.http         → API'yi test etmek için hazır HTTP istekleri
│   └── Properties/
│       └── launchSettings.json  → Uygulama hangi portta çalışacak vb.
│
├── PYTHON SCRAPER  ← Python ekibinin alanı (veri çekme)
│   ├── scraper/
│   │   ├── bulk_fetcher.py      → Toplu ihale çekme motoru
│   │   ├── ihale_client.py      → EKAP ihale API istemcisi
│   │   ├── ihale_models.py      → İhale veri modelleri (Python tarafı)
│   │   ├── ilan_client.py       → İlan API istemcisi
│   │   └── export_csv.py        → Veriyi CSV'ye aktarma
│   ├── run_scraper.py           → Scraper'ı çalıştıran ana script
│   ├── requirements.txt         → Python paket bağımlılıkları
│   └── .env                     → Veritabanı bağlantı bilgileri (şifre!) [gitignore'da]
│
├── OTOMASYON
│   └── .github/workflows/
│       └── daily_scraper.yml    → GitHub Actions: scraper'ı otomatik çalıştırma
│
├── DOKÜMANTASYON (Atalay'ın notları)
│   ├── EKAP_Backend_Context.md  → Proje bağlam dosyası [gitignore'da]
│   ├── EKAP_Backend_Roadmap.md  → Adım adım yol haritası
│   └── PROJE_YAPISI.md          → Bu dosya
│
└── .gitignore                   → Git'in yok sayacağı dosyalar (bin/, obj/, .env, appsettings vb.)
```

---

## .NET tarafı — katman mantığı

Backend basit bir katmanlı yapıya oturuyor:

**Models/ (Veri modeli)**
Veritabanındaki her tabloyu bir C# sınıfı temsil eder. `Tender` ana tablo; `TenderCharacteristic`, `TenderOkasCode`, `TenderAnnouncement` ona bağlı (bire-çok). Bir ihalenin birden çok özelliği/kodu/ilanı olabildiği için bunlar ayrı tablolarda tutulur.

**Data/ (Veri erişimi)**
`EkapDbContext`, uygulamayla PostgreSQL arasındaki köprü. Hangi tabloların olduğunu (`DbSet`) ve aralarındaki ilişkileri tanımlar. Kodda veriye bu sınıf üzerinden ulaşılır.

**Controllers/ (Sunum — henüz yok)**
API endpoint'leri buraya gelecek. Örn. `GET /api/ihaleler`, `GET /api/ihaleler/{ikn}`. Dış dünya (frontend, LLM) veriye buradan erişir. Controller'lar DbContext'i kullanarak veriyi çeker ve JSON döner.

**Program.cs (Başlangıç)**
Uygulama açılınca çalışan ilk yer. DbContext'i tanıtır (`AddDbContext`), servisleri kaydeder, controller'ları devreye alır.

---

## Veri akışı (büyük resim)

```
[Python Scraper]  →  EKAP API'sinden ihaleleri çeker
       ↓
[PostgreSQL]      →  Veriler veritabanında saklanır (ortak DB: isbak_ekap_db)
       ↓
[.NET Backend]    →  Veriyi API ile sunar (Controllers)
       ↓
[Frontend + LLM]  →  Frontend gösterir, LLM uygunluk skoru üretip geri yazar
```

---

## Önemli notlar

- **appsettings.json ve .env** git tarafından yok sayılır (`.gitignore`). İçlerinde bağlantı/şifre bilgisi var, repoya gönderilmez. Her geliştirici kendi bağlantısını yazar.
- **bin/ ve obj/** derleme çıktılarıdır, repoya konmaz.
- **Controllers/ klasörü** şu an yok; API endpoint'leri yazılmaya başlandığında oluşturulacak.
- **Ortak veritabanı:** Ekip `isbak_ekap_db` adında ortak bir PostgreSQL kullanıyor (.env'de tanımlı). Backend'in buna mı yoksa lokal bir DB'ye mi bağlanacağı ekiple netleştirilmeli.
