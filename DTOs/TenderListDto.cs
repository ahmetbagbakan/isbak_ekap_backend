namespace EkapBackend.DTOs;

public class TenderListDto
{
    public string Ikn { get; set; } = null!;
    public string? Adi { get; set; }
    public string? IdareAdi { get; set; }
    public string? Il { get; set; }
    public string? IhaleTarihi { get; set; }
    public string? IhaleTuru { get; set; }         // Mal / Hizmet / Yapım / Danışmanlık
    public string? IhaleUsulu { get; set; }
    public string? IhaleDurumu { get; set; }
    public bool EIhale { get; set; }
    public int? DokumanSayisi { get; set; }

    // LLM alanları — henüz analiz yapılmamışsa null gelir
    public int? IlgiSkoru { get; set; }            // 0-100 arası
    public bool? SirketeUygunMu { get; set; }
    public string? LlmOzeti { get; set; }

    // Takip / Watchlist alanı — satış ekibinin koyduğu etiket
    public string? TakipDurumu { get; set; }       // null | "inceleniyor" | "alınması öneriliyor" | "alınması önerilmiyor"
}
