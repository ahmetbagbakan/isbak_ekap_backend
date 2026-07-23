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
    public string? TakipDurumu { get; set; }

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
