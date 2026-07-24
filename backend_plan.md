# ISBAK EKAP — Backend Detaylı Mimari ve Geliştirme Planı

## Projenin Amacı ve Sınırları

EKAP'tan Python scraper tarafından otomatik çekilen ihale verilerini,
İSBAK satış ekibine sunmak. Yapay zeka her ihaleye uygunluk skoru verecek,
satış ekibi binlerce ihale arasından sadece İSBAK'a uygun olanları görecek.

**Sorumluluk Sınırları:**
- Sen (Backend): Veriyi veritabanından okuyup, LLM skorunu yazıp, API ile sunan katman.
- Diğer arkadaş (Frontend): React arayüzü — bu plandaki endpoint'leri tüketecek.
- Diğer arkadaş (Yapay Zeka): LLM servisi — backend API'ye skor yazacak.
- Python Scraper: Her sabah 07:00'de otomatik çalışıp veritabanını besliyor. Backend'in bunu bilmesi yeterli, buna dokunmak gerekmez.

---

## Mevcut Durum (Bugün Elimizde Ne Var)

✅ **Hazır:**
- .NET 10 Web API projesi kurulu (`EkapBackend`)
- 4 C# model sınıfı: `Tender`, `TenderCharacteristic`, `TenderOkasCode`, `TenderAnnouncement`
- `EkapDbContext.cs` — ilişkiler ve DbSet'ler tanımlanmış
- `Program.cs` — `AddDbContext` kaydı yapılmış
- PostgreSQL: `isbak_ekap_db` veritabanı var, verilerle dolu
- Python scraper `ON CONFLICT (ikn) DO NOTHING` ile duplicate'siz çalışıyor

⚠️ **Henüz Çalışmayan / Eksik:**
- `appsettings.json` yok → bağlantı kurulamıyor
- Sütun ismi uyumsuzluğu (C# `IdareAdi` ↔ DB `idare_adi`) → EF Core hata verir
- `Tender.cs`'te olmayan `DetayCekildi` sütunu var → EF Core hata verir
- `AddControllers()` ve Swagger yok → hiçbir endpoint çalışmıyor

🆕 **Yeni Eklenecek (Takip / Watchlist Özelliği):**
- `tenders` tablosuna `takip_durumu` TEXT sütunu eklenecek
- Satış ekibi ihaleleri `alınacak` / `alınmayacak` / `inceleniyor` olarak etiketleyebilecek
- "İhalelerin" sekmesi bu alanı filtreler
- Paylaşımlı liste: tüm ekip aynı etiketleri görür (kişisel değil)

---

## Mimari Tasarım (Clean Architecture — 4 Katman)

Atalay'ın planındaki basit controller → doğrudan DB yaklaşımı yerine,
4 katmanlı temiz mimari öneriyorum. Bu sayede:
- Kod okunabilir ve test edilebilir olur
- Her katman tek bir sorumluluğa sahip olur
- İleride değişiklik yapmak kolaylaşır

```
Controllers/      ← HTTP istekleri alır, DTO döndürür (sunum katmanı)
    ↓
Services/         ← İş mantığı buradadır (filtreleme, sayfalama, veri birleştirme)
    ↓
Repositories/     ← Veritabanı erişimi sadece buradadır (EF Core sorguları)
    ↓
Data/ + Models/   ← EF Core DbContext ve entity sınıfları
```

---

## Klasör Yapısı (Hedef)

```
EkapBackend/
│
├── Models/                     ← Entity sınıfları (Atalay'ın yazdığı, düzeltilecek)
│   ├── Tender.cs
│   ├── TenderCharacteristic.cs
│   ├── TenderOkasCode.cs
│   └── TenderAnnouncement.cs
│
├── DTOs/                       ← API'nin dışarıya döndürdüğü veri şekilleri [YENİ]
│   ├── TenderListDto.cs        ← Liste sayfası için özet
│   ├── TenderDetailDto.cs      ← Detay sayfası için tam veri
│   ├── TenderAnalysisDto.cs    ← LLM'in göndereceği skor
│   ├── TenderDurumDto.cs       ← Satış ekibinin atadığı takip durumu [YENİ]
│   └── PagedResultDto.cs       ← Sayfalama zarfı
│
├── Repositories/               ← Veritabanı erişim katmanı [YENİ]
│   ├── ITenderRepository.cs    ← Arayüz (interface)
│   └── TenderRepository.cs     ← EF Core implementasyonu
│
├── Services/                   ← İş mantığı katmanı [YENİ]
│   ├── ITenderService.cs       ← Arayüz
│   └── TenderService.cs        ← Filtreleme, sayfalama, dönüşüm
│
├── Controllers/                ← HTTP endpoint'leri [YENİ]
│   └── IhaleController.cs
│
├── Middleware/                 ← Global hata yönetimi [YENİ]
│   └── ExceptionMiddleware.cs
│
├── Data/
│   └── EkapDbContext.cs        ← Düzeltilecek (NamingConventions)
│
├── Program.cs                  ← Güncellenecek
└── appsettings.json            ← Oluşturulacak (.gitignore'da)
```

---

## AŞAMA 1 — Temel Düzeltmeler ve Veritabanı Bağlantısı

> Bu aşama bitmeden hiçbir şey çalışmaz. Hepsini sırayla yap.

---

### 1.1 — `appsettings.json` Oluştur

Her geliştirici kendi makinesinde bu dosyayı elle oluşturur.
**Bu dosya `.gitignore`'da kalmaya devam eder.**

```json
{
  "Logging": {
    "LogLevel": {
      "Default": "Information",
      "Microsoft.AspNetCore": "Warning"
    }
  },
  "AllowedHosts": "*",
  "ConnectionStrings": {
    "DefaultConnection": "Host=127.0.0.1;Port=5432;Database=isbak_ekap_db;Username=postgres;Password=postgres"
  }
}
```

Atalay'ın bağlantısı (Mac/Postgres.app):
```
Host=localhost;Port=5432;Database=isbak_ekap_db;Username=postgres;Password=postgres
```

---

### 1.2 — `Tender.cs` Düzelt

**Silinecek satır**: `public int? DetayCekildi { get; set; }` — veritabanında bu sütun yok.

**Eklenecek satır** (Watchlist / Takip özelliği için):
```csharp
public string? TakipDurumu { get; set; }  // null | "inceleniyor" | "alınacak" | "alınmayacak"
```

Ayrıca veritabanına bu sütunu eklemek için DBeaver veya psql üzerinden şu SQL çalıştırılır:
```sql
ALTER TABLE tenders ADD COLUMN IF NOT EXISTS takip_durumu TEXT DEFAULT NULL;
```

Bu sütun Python scraper tarafından doldurulmaz, **sadece backend API üzerinden güncellenir.**

**Not**: `IhaleTarihi` ve `CreatedAt`/`UpdatedAt` alanlarının tipleri
string yerine `DateTime?` olmalı ama veritabanında TEXT olarak saklandığından şimdilik `string?` kalabilir.

---

### 1.3 — NamingConventions Paketi Kur

EF Core, C# sınıfındaki `IdareAdi`'yi veritabanında `IdareAdi` olarak arar.
Ama veritabanımızda `idare_adi` var. Bu paketi kurarak otomatik çözüyoruz.

```bash
dotnet add package EFCore.NamingConventions
```

`EkapDbContext.cs`'te `OnConfiguring` veya `Program.cs`'te UseNpgsql'i şöyle güncelle:

```csharp
options.UseNpgsql(connectionString).UseSnakeCaseNamingConventions();
```

Bu tek satır tüm tablo/sütun isimlerini otomatik snake_case'e çevirir.

---

### 1.4 — Migration YAPMA

Tablolar Python scraper tarafından zaten oluşturulmuş ve dolu.
EF Core migration çalıştırmak mevcut tablolara dokunmaz ama ileride karmaşıklık yaratır.
`dotnet run` ile sadece bağlantıyı doğrula yeterli.

---

### 1.5 — `Program.cs` Temel Güncellemesi

```csharp
using Microsoft.EntityFrameworkCore;
using EkapBackend.Data;
using EkapBackend.Repositories;
using EkapBackend.Services;

var builder = WebApplication.CreateBuilder(args);

// Veritabanı
builder.Services.AddDbContext<EkapDbContext>(options =>
    options.UseNpgsql(builder.Configuration.GetConnectionString("DefaultConnection"))
           .UseSnakeCaseNamingConventions());

// Servis katmanı kaydı
builder.Services.AddScoped<ITenderRepository, TenderRepository>();
builder.Services.AddScoped<ITenderService, TenderService>();

// Controller + Swagger
builder.Services.AddControllers();
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

// CORS
builder.Services.AddCors(options =>
{
    options.AddPolicy("FrontendPolicy", policy =>
        policy.WithOrigins("http://localhost:3000", "http://localhost:5173")
              .AllowAnyHeader()
              .AllowAnyMethod());
});

var app = builder.Build();

// Middleware sırası önemli!
app.UseMiddleware<ExceptionMiddleware>(); // Global hata yakalama
app.UseSwagger();
app.UseSwaggerUI();
app.UseCors("FrontendPolicy");
app.UseAuthorization();
app.MapControllers();
app.Run();
```

---

## AŞAMA 2 — DTO Katmanı

DTO (Data Transfer Object): Entity sınıfını doğrudan API'ye döndürmek yerine,
her endpoint için ne döneceğini açıkça tanımlarız. Avantajlar:
- Frontend'e gereksiz/hassas alan gitmez
- Entity değişince API bozulmaz
- Her endpoint kendi ihtiyacına göre şekillendirilir

---

### `DTOs/TenderListDto.cs` — Liste Sayfası İçin

```csharp
namespace EkapBackend.DTOs;

public class TenderListDto
{
    public string Ikn { get; set; } = null!;
    public string? Adi { get; set; }
    public string? IdareAdi { get; set; }
    public string? Il { get; set; }
    public string? IhaleTarihi { get; set; }
    public string? IhaleTuru { get; set; }       // Mal / Hizmet / Yapım / Danışmanlık
    public string? IhaleUsulu { get; set; }
    public string? IhaleDurumu { get; set; }
    public bool EIhale { get; set; }
    public int? DokumanSayisi { get; set; }
    // LLM alanları — analiz yapılmamışsa null gelir
    public int? IlgiSkoru { get; set; }
    public bool? SirketeUygunMu { get; set; }
    public string? LlmOzeti { get; set; }
    // Takip / Watchlist alanı — satış ekibinin koyduğu etiket
    public string? TakipDurumu { get; set; }  // null | "inceleniyor" | "alınacak" | "alınmayacak"
}
```

---

### `DTOs/TenderDetailDto.cs` — Detay Sayfası İçin

```csharp
namespace EkapBackend.DTOs;

public class TenderDetailDto
{
    public string Ikn { get; set; } = null!;
    public string? Adi { get; set; }
    public string? IdareAdi { get; set; }
    public string? Il { get; set; }
    public string? IhaleTarihi { get; set; }
    public string? IhaleTuru { get; set; }
    public string? IhaleUsulu { get; set; }
    public string? IhaleDurumu { get; set; }
    public string? Kapsam { get; set; }
    public bool EIhale { get; set; }
    public bool KismiTeklif { get; set; }
    public string? IhaleYeri { get; set; }
    public string? IsinYeri { get; set; }
    public int? DokumanSayisi { get; set; }
    // LLM alanları
    public int? IlgiSkoru { get; set; }
    public bool? SirketeUygunMu { get; set; }
    public string? LlmOzeti { get; set; }
    public string? AnalizTarihi { get; set; }
    // Takip / Watchlist alanı
    public string? TakipDurumu { get; set; }  // null | "inceleniyor" | "alınacak" | "alınmayacak"
    // İlişkili veriler
    public List<string> Ozellikler { get; set; } = new();          // TenderCharacteristics
    public List<OkasCodeDto> OkasKodlari { get; set; } = new();    // TenderOkasCodes
    public List<AnnouncementDto> Ilanlar { get; set; } = new();    // TenderAnnouncements
}

public class OkasCodeDto
{
    public string? Kod { get; set; }
    public string? Ad { get; set; }
}

public class AnnouncementDto
{
    public string? IlanTipi { get; set; }
    public string? IlanTarihi { get; set; }
    public string? Baslik { get; set; }
    public string? Icerik { get; set; }
}
```

---

### `DTOs/TenderAnalysisDto.cs` — LLM'in Göndereceği Skor

```csharp
namespace EkapBackend.DTOs;

public class TenderAnalysisDto
{
    public int IlgiSkoru { get; set; }          // 0-100 arası
    public bool SirketeUygunMu { get; set; }
    public string? LlmOzeti { get; set; }       // 1-3 cümle özet
}
```

---

### `DTOs/TenderDurumDto.cs` — Satış Ekibinin Takip Etiketi [YENİ]

```csharp
namespace EkapBackend.DTOs;

public class TenderDurumDto
{
    // Geçerli değerler: "inceleniyor", "alınacak", "alınmayacak"
    // null göndermek etiketi kaldırır (sıfırlar)
    public string? TakipDurumu { get; set; }
}
```

---

### `DTOs/PagedResultDto.cs` — Sayfalama Zarfı

```csharp
namespace EkapBackend.DTOs;

public class PagedResultDto<T>
{
    public List<T> Veriler { get; set; } = new();
    public int ToplamKayit { get; set; }
    public int ToplamSayfa { get; set; }
    public int MevcutSayfa { get; set; }
    public int SayfaBoyutu { get; set; }
}
```

---

## AŞAMA 3 — Repository Katmanı

Repository, EF Core sorgularını Services katmanından ayırır.
Bu sayede servis iş mantığını test edebilirsin, veritabanı detaylarını bilmeden.

---

### `Repositories/ITenderRepository.cs`

```csharp
namespace EkapBackend.Repositories;

public interface ITenderRepository
{
    // Sayfalı + filtreli liste
    Task<(List<Tender> Items, int TotalCount)> GetAllAsync(TenderFilter filter);

    // Tek ihale — ilişkilerle birlikte
    Task<Tender?> GetByIknAsync(string ikn);

    // LLM skoru güncelleme
    Task<bool> UpdateAnalysisAsync(string ikn, TenderAnalysisDto dto);

    // Takip durumu güncelleme ("İhalelerin" sekmesi) [YENİ]
    Task<bool> UpdateDurumAsync(string ikn, TenderDurumDto dto);

    // Filtre seçenekleri (frontend dropdown'ları için)
    Task<List<string>> GetDistinctIllerAsync();
    Task<List<string>> GetDistinctTurlerAsync();
    Task<List<string>> GetDistinctDurumlarAsync();
}
```

---

### `Repositories/TenderFilter.cs` — Filtre Parametreleri

```csharp
namespace EkapBackend.Repositories;

public class TenderFilter
{
    public string? Il { get; set; }
    public string? Tur { get; set; }             // ihale_turu
    public string? Durum { get; set; }           // ihale_durumu
    public string? Usul { get; set; }            // ihale_usulu
    public DateTime? BaslangicTarihi { get; set; }
    public DateTime? BitisTarihi { get; set; }
    public string? Kelime { get; set; }          // Başlıkta veya idare adında arama
    public int? MinIlgiSkoru { get; set; }       // Sadece analize girmiş ihaleler
    public bool? SirketeUygunMu { get; set; }    // true = sadece uygun ihaleler
    // Takip / Watchlist filtresi [YENİ]
    public string? TakipDurumu { get; set; }     // "inceleniyor" | "alınacak" | "alınmayacak" | "takip-edilen" (hepsi)
    public string Sirala { get; set; } = "tarih";// "tarih" | "skor"
    public bool SiralaAzalan { get; set; } = true;
    public int Sayfa { get; set; } = 1;
    public int SayfaBoyutu { get; set; } = 20;
}
```

---

### `Repositories/TenderRepository.cs` — EF Core Implementasyonu

```csharp
namespace EkapBackend.Repositories;

public class TenderRepository : ITenderRepository
{
    private readonly EkapDbContext _db;

    public TenderRepository(EkapDbContext db) => _db = db;

    public async Task<(List<Tender> Items, int TotalCount)> GetAllAsync(TenderFilter f)
    {
        var query = _db.Tenders.AsQueryable();

        // Filtreler — null kontrolü ile
        if (!string.IsNullOrEmpty(f.Il))
            query = query.Where(t => t.Il != null && t.Il.ToLower().Contains(f.Il.ToLower()));

        if (!string.IsNullOrEmpty(f.Tur))
            query = query.Where(t => t.IhaleTuru == f.Tur);

        if (!string.IsNullOrEmpty(f.Durum))
            query = query.Where(t => t.IhaleDurumu == f.Durum);

        if (!string.IsNullOrEmpty(f.Usul))
            query = query.Where(t => t.IhaleUsulu == f.Usul);

        if (!string.IsNullOrEmpty(f.Kelime))
            query = query.Where(t =>
                (t.Adi != null && t.Adi.ToLower().Contains(f.Kelime.ToLower())) ||
                (t.IdareAdi != null && t.IdareAdi.ToLower().Contains(f.Kelime.ToLower())));

        if (f.MinIlgiSkoru.HasValue)
            query = query.Where(t => t.IlgiSkoru >= f.MinIlgiSkoru);

        if (f.SirketeUygunMu.HasValue)
            query = query.Where(t => t.SirketeUygunMu == f.SirketeUygunMu);

        // Takip durumu filtresi [YENİ]
        if (!string.IsNullOrEmpty(f.TakipDurumu))
        {
            if (f.TakipDurumu == "takip-edilen")
                // "takip-edilen" = herhangi bir etiket atanmış olanlar
                query = query.Where(t => t.TakipDurumu != null);
            else
                query = query.Where(t => t.TakipDurumu == f.TakipDurumu);
        }

        // Tarih filtreleri (TEXT sütunu olduğundan LIKE ile karşılaştırma)
        // NOT: ihale_tarihi TEXT olarak saklanıyor. İleride DATE tipine geçilince bu düzelir.
        if (f.BaslangicTarihi.HasValue)
            query = query.Where(t => string.Compare(t.IhaleTarihi,
                f.BaslangicTarihi.Value.ToString("yyyy-MM-dd")) >= 0);

        if (f.BitisTarihi.HasValue)
            query = query.Where(t => string.Compare(t.IhaleTarihi,
                f.BitisTarihi.Value.ToString("yyyy-MM-dd")) <= 0);

        // Toplam kayıt sayısı (sayfalama için)
        var totalCount = await query.CountAsync();

        // Sıralama
        query = f.Sirala switch
        {
            "skor" => f.SiralaAzalan
                ? query.OrderByDescending(t => t.IlgiSkoru)
                : query.OrderBy(t => t.IlgiSkoru),
            _ => f.SiralaAzalan
                ? query.OrderByDescending(t => t.IhaleTarihi)
                : query.OrderBy(t => t.IhaleTarihi)
        };

        // Sayfalama
        var items = await query
            .Skip((f.Sayfa - 1) * f.SayfaBoyutu)
            .Take(f.SayfaBoyutu)
            .ToListAsync();

        return (items, totalCount);
    }

    public async Task<Tender?> GetByIknAsync(string ikn)
    {
        return await _db.Tenders
            .Include(t => t.Characteristics)
            .Include(t => t.OkasCodes)
            .Include(t => t.Announcements)
            .FirstOrDefaultAsync(t => t.Ikn == ikn);
    }

    public async Task<bool> UpdateAnalysisAsync(string ikn, TenderAnalysisDto dto)
    {
        var tender = await _db.Tenders.FirstOrDefaultAsync(t => t.Ikn == ikn);
        if (tender == null) return false;

        tender.IlgiSkoru = dto.IlgiSkoru;
        tender.SirketeUygunMu = dto.SirketeUygunMu;
        tender.LlmOzeti = dto.LlmOzeti;
        tender.AnalizTarihi = DateTime.UtcNow.ToString("yyyy-MM-dd HH:mm:ss");

        await _db.SaveChangesAsync();
        return true;
    }

    // Takip durumu güncelleme [YENİ]
    public async Task<bool> UpdateDurumAsync(string ikn, TenderDurumDto dto)
    {
        var tender = await _db.Tenders.FirstOrDefaultAsync(t => t.Ikn == ikn);
        if (tender == null) return false;

        // null göndermek etiketi kaldırır
        tender.TakipDurumu = dto.TakipDurumu;
        await _db.SaveChangesAsync();
        return true;
    }

    public async Task<List<string>> GetDistinctIllerAsync() =>
        await _db.Tenders.Where(t => t.Il != null)
            .Select(t => t.Il!).Distinct().OrderBy(x => x).ToListAsync();

    public async Task<List<string>> GetDistinctTurlerAsync() =>
        await _db.Tenders.Where(t => t.IhaleTuru != null)
            .Select(t => t.IhaleTuru!).Distinct().OrderBy(x => x).ToListAsync();

    public async Task<List<string>> GetDistinctDurumlarAsync() =>
        await _db.Tenders.Where(t => t.IhaleDurumu != null)
            .Select(t => t.IhaleDurumu!).Distinct().OrderBy(x => x).ToListAsync();
}
```

---

## AŞAMA 4 — Service Katmanı

Service, iş mantığını barındırır: filtreleme parametrelerini repository'e iletir,
gelen entity'leri DTO'ya dönüştürür, sayfalama zarfını hazırlar.

---

### `Services/ITenderService.cs`

```csharp
namespace EkapBackend.Services;

public interface ITenderService
{
    Task<PagedResultDto<TenderListDto>> GetIhaleListesiAsync(TenderFilter filter);
    Task<TenderDetailDto?> GetIhaleDetayiAsync(string ikn);
    Task<bool> UpdateIhaleAnaliziAsync(string ikn, TenderAnalysisDto dto);
    Task<FilterOptionsDto> GetFilterSeçenekleriAsync();
}
```

---

### `Services/TenderService.cs`

```csharp
namespace EkapBackend.Services;

public class TenderService : ITenderService
{
    private readonly ITenderRepository _repo;

    public TenderService(ITenderRepository repo) => _repo = repo;

    public async Task<PagedResultDto<TenderListDto>> GetIhaleListesiAsync(TenderFilter filter)
    {
        var (items, totalCount) = await _repo.GetAllAsync(filter);
        var toplamSayfa = (int)Math.Ceiling(totalCount / (double)filter.SayfaBoyutu);

        return new PagedResultDto<TenderListDto>
        {
            Veriler = items.Select(MapToListDto).ToList(),
            ToplamKayit = totalCount,
            ToplamSayfa = toplamSayfa,
            MevcutSayfa = filter.Sayfa,
            SayfaBoyutu = filter.SayfaBoyutu
        };
    }

    public async Task<TenderDetailDto?> GetIhaleDetayiAsync(string ikn)
    {
        var tender = await _repo.GetByIknAsync(ikn);
        return tender == null ? null : MapToDetailDto(tender);
    }

    public async Task<bool> UpdateIhaleAnaliziAsync(string ikn, TenderAnalysisDto dto) =>
        await _repo.UpdateAnalysisAsync(ikn, dto);

    public async Task<FilterOptionsDto> GetFilterSeçenekleriAsync() =>
        new FilterOptionsDto
        {
            Iller = await _repo.GetDistinctIllerAsync(),
            Turler = await _repo.GetDistinctTurlerAsync(),
            Durumlar = await _repo.GetDistinctDurumlarAsync()
        };

    // --- Mapping yardımcıları ---

    private static TenderListDto MapToListDto(Tender t) => new()
    {
        Ikn = t.Ikn,
        Adi = t.Adi,
        IdareAdi = t.IdareAdi,
        Il = t.Il,
        IhaleTarihi = t.IhaleTarihi,
        IhaleTuru = t.IhaleTuru,
        IhaleUsulu = t.IhaleUsulu,
        IhaleDurumu = t.IhaleDurumu,
        EIhale = t.EIhale == 1,
        DokumanSayisi = t.DokumanSayisi,
        IlgiSkoru = t.IlgiSkoru,
        SirketeUygunMu = t.SirketeUygunMu,
        LlmOzeti = t.LlmOzeti
    };

    private static TenderDetailDto MapToDetailDto(Tender t) => new()
    {
        Ikn = t.Ikn,
        Adi = t.Adi,
        IdareAdi = t.IdareAdi,
        Il = t.Il,
        IhaleTarihi = t.IhaleTarihi,
        IhaleTuru = t.IhaleTuru,
        IhaleUsulu = t.IhaleUsulu,
        IhaleDurumu = t.IhaleDurumu,
        Kapsam = t.Kapsam,
        EIhale = t.EIhale == 1,
        KismiTeklif = t.KismiTeklif == 1,
        IhaleYeri = t.IhaleYeri,
        IsinYeri = t.IsinYeri,
        DokumanSayisi = t.DokumanSayisi,
        IlgiSkoru = t.IlgiSkoru,
        SirketeUygunMu = t.SirketeUygunMu,
        LlmOzeti = t.LlmOzeti,
        AnalizTarihi = t.AnalizTarihi,
        Ozellikler = t.Characteristics.Select(c => c.Ozellik).ToList(),
        OkasKodlari = t.OkasCodes.Select(o => new OkasCodeDto { Kod = o.Kod, Ad = o.Ad }).ToList(),
        Ilanlar = t.Announcements.Select(a => new AnnouncementDto
        {
            IlanTipi = a.IlanTipi,
            IlanTarihi = a.IlanTarihi,
            Baslik = a.Baslik,
            Icerik = a.Icerik
        }).ToList()
    };
}
```

---

## AŞAMA 5 — Controller (API Endpoint'leri)

---

### `Controllers/IhaleController.cs`

```csharp
[ApiController]
[Route("api/ihaleler")]
public class IhaleController : ControllerBase
{
    private readonly ITenderService _service;
    public IhaleController(ITenderService service) => _service = service;

    // GET /api/ihaleler
    // GET /api/ihaleler?il=İstanbul&tur=Yapım&minSkor=70&sayfa=1&sayfaBoyutu=20
    [HttpGet]
    public async Task<IActionResult> GetList([FromQuery] TenderFilter filter)
    {
        var result = await _service.GetIhaleListesiAsync(filter);
        return Ok(result);
    }

    // GET /api/ihaleler/2026/50878
    [HttpGet("{*ikn}")]
    public async Task<IActionResult> GetDetail(string ikn)
    {
        var result = await _service.GetIhaleDetayiAsync(ikn);
        if (result == null) return NotFound(new { hata = $"İhale bulunamadı: {ikn}" });
        return Ok(result);
    }

    // PUT /api/ihaleler/2026/50878/analiz
    // LLM servisi bu endpoint'i çağırır
    [HttpPut("{*ikn}/analiz")]
    public async Task<IActionResult> UpdateAnaliz(string ikn, [FromBody] TenderAnalysisDto dto)
    {
        if (dto.IlgiSkoru < 0 || dto.IlgiSkoru > 100)
            return BadRequest(new { hata = "IlgiSkoru 0-100 arasında olmalıdır." });

        var basarili = await _service.UpdateIhaleAnaliziAsync(ikn, dto);
        if (!basarili) return NotFound(new { hata = $"İhale bulunamadı: {ikn}" });

        return Ok(new { mesaj = "Analiz başarıyla kaydedildi." });
    }

    // GET /api/ihaleler/filtre-secenekleri
    // Frontend'in dropdown verilerini buradan çekebilmesi için
    [HttpGet("filtre-secenekleri")]
    public async Task<IActionResult> GetFiltreSecenekleri()
    {
        var result = await _service.GetFilterSeçenekleriAsync();
        return Ok(result);
    }
}
```

---

## AŞAMA 6 — Global Hata Yönetimi (Middleware)

Tüm beklenmeyen hataları yakalayıp düzgün JSON döndürür.
Controller'larda tek tek try/catch yazmak gerekmez.

---

### `Middleware/ExceptionMiddleware.cs`

```csharp
namespace EkapBackend.Middleware;

public class ExceptionMiddleware
{
    private readonly RequestDelegate _next;
    private readonly ILogger<ExceptionMiddleware> _logger;

    public ExceptionMiddleware(RequestDelegate next, ILogger<ExceptionMiddleware> logger)
    {
        _next = next;
        _logger = logger;
    }

    public async Task InvokeAsync(HttpContext context)
    {
        try
        {
            await _next(context);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Beklenmeyen hata: {Message}", ex.Message);
            context.Response.StatusCode = 500;
            context.Response.ContentType = "application/json";
            await context.Response.WriteAsJsonAsync(new
            {
                hata = "Sunucu hatası oluştu.",
                detay = ex.Message  // Production'da bu satırı kaldır
            });
        }
    }
}
```

---

## API Endpoint Özeti

| Method | URL | Açıklama |
|---|---|---|
| `GET` | `/api/ihaleler` | İhaleleri listele (filtreli + sayfalı) |
| `GET` | `/api/ihaleler/{ikn}` | Tek ihale tam detayı |
| `PUT` | `/api/ihaleler/{ikn}/analiz` | LLM uygunluk skoru yaz |
| `PUT` | `/api/ihaleler/{ikn}/durum` | **Satış ekibi takip etiketi yaz** 🆕 |
| `GET` | `/api/ihaleler?takipDurumu=inceleniyor` | **"İhalelerin" sekmesi filtresi** 🆕 |
| `GET` | `/api/ihaleler/filtre-secenekleri` | Frontend dropdown verileri |
| `GET` | `/swagger` | API dokümantasyonu (geliştirme ortamında) |

---

## Filtre Parametreleri Detayı

| Parametre | Tip | Örnek | Açıklama |
|---|---|---|---|
| `il` | string | `?il=İstanbul` | İl filtresi (contains ile arama) |
| `tur` | string | `?tur=Yapım` | İhale türü (Mal/Hizmet/Yapım/Danışmanlık) |
| `durum` | string | `?durum=Yayımlandı` | İhale durumu |
| `usul` | string | `?usul=Açık` | İhale usulü |
| `baslangicTarihi` | date | `?baslangicTarihi=2026-07-01` | Tarih filtresi başlangıç |
| `bitisTarihi` | date | `?bitisTarihi=2026-08-31` | Tarih filtresi bitiş |
| `kelime` | string | `?kelime=yazılım` | Başlık ve idare adında arama |
| `minIlgiSkoru` | int | `?minIlgiSkoru=60` | Minimum LLM uygunluk skoru |
| `sirketeUygunMu` | bool | `?sirketeUygunMu=true` | Sadece uygun ihaleler |
| `takipDurumu` | string | `?takipDurumu=inceleniyor` | `inceleniyor` \| `alınacak` \| `alınmayacak` \| `takip-edilen` 🆕 |
| `sirala` | string | `?sirala=skor` | `tarih` veya `skor` |
| `siralaAzalan` | bool | `?siralaAzalan=false` | Artan/azalan sıralama |
| `sayfa` | int | `?sayfa=2` | Sayfa numarası (başlangıç: 1) |
| `sayfaBoyutu` | int | `?sayfaBoyutu=50` | Sayfa başına kayıt (max: 100) |

---

## LLM Entegrasyonu Nasıl Çalışacak

```
[LLM Servisi]
    → İhaleyi orijinal EKAP'tan veya bizim API'den çeker
    → İhale metni + kurumsal profile göre skor üretir
    → PUT /api/ihaleler/{ikn}/analiz endpoint'ini çağırır
    → Backend IlgiSkoru, SirketeUygunMu, LlmOzeti'yi veritabanına yazar
    → Frontend bir sonraki sorgudan bu alanları dolu görür
```

LLM arkadaşınla netleştirilecek:
1. LLM tüm ihaleleri mi analiz edecek, yoksa satış ekibi seçecek mi?
2. Analiz sıraya girince backend bunu LLM'e mi bildirecek (webhook), yoksa LLM kendi mi çekecek?
3. Analiz bir kez mi yapılacak, yoksa yeni ilan gelince otomatik tetiklenecek mi?

---

## Geliştirme Öncelik Sırası

```
AŞAMA 1 → appsettings.json + DetayCekildi sil + NamingConventions + takip_durumu sütunu SQL ile ekle
AŞAMA 2 → DTOs/ klasörü: TenderListDto, TenderDetailDto, TenderAnalysisDto, TenderDurumDto, PagedResultDto
AŞAMA 3 → Repositories/ + TenderFilter (takipDurumu dahil) + TenderRepository
AŞAMA 4 → Services/ + TenderService
AŞAMA 5 → Controllers/ + IhaleController (6 endpoint) + ExceptionMiddleware
TEST    → Swagger'dan tüm endpoint'leri test et:
          - GET /api/ihaleler (filtreli liste)
          - GET /api/ihaleler/{ikn} (detay)
          - PUT /api/ihaleler/{ikn}/analiz (LLM skoru)
          - PUT /api/ihaleler/{ikn}/durum (takip etiketi)
          - GET /api/ihaleler?takipDurumu=inceleniyor (İhalelerin sekmesi)
          - GET /api/ihaleler/filtre-secenekleri (dropdownlar)
```

---

## Ekiple Netleştirilecek Kararlar

| Konu | Seçenek A | Seçenek B | Öneri |
|---|---|---|---|
| **URL'de ihale anahtarı** | `ikn` (`2026/50878`) | `id` (SHA hash) | **`ikn`** — okunabilir, EKAP ile uyumlu |
| **LLM çağrı yönü** | LLM → Backend API → DB | LLM → DB doğrudan | **Backend API** — denetlenebilir, loglanabilir |
| **Frontend port** | 3000 (Create React App) | 5173 (Vite) | Arkadaşından öğren, CORS'a ekle |
| **Tarih sütun tipi** | TEXT'te kal | Migration ile DATE'e geç | Şimdilik TEXT, çalışınca düzelt |
| **`/analiz` endpoint güvenliği** | Açık bırak | API key ekle | LLM servisi şirket içi ağdaysa açık kalabilir |

---

## Mimari Özeti

```
[Python Scraper] ──her sabah 07:00──▶ [PostgreSQL — isbak_ekap_db]
                                               │
                              (EF Core, sadece okuma)
                                               │
                                    [TenderRepository]
                                               │
                                    [TenderService]
                                               │
                                 [IhaleController (REST API)]
                                               │
              ┌────────────────────────────────┤
              │                                │
     [React Frontend]                  [LLM Servisi]
     (GET /api/ihaleler)          (PUT /api/ihaleler/{ikn}/analiz)
              │
    [İSBAK Satış Ekibi]
```
