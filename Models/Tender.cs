namespace EkapBackend.Models;

public class Tender
{
    public string Id { get; set; } = null!;       // SHA hash (birincil anahtar)
    public string Ikn { get; set; } = null!;       // İhale Kayıt No, örn. 2026/50878
    public string? Adi { get; set; }
    public string? IdareAdi { get; set; }
    public string? Il { get; set; }
    public string? IhaleTarihi { get; set; }
    public string? IhaleTuru { get; set; }         // Mal / Hizmet / Yapım / Danışmanlık
    public string? IhaleUsulu { get; set; }
    public string? IhaleDurumu { get; set; }
    public string? Kapsam { get; set; }
    public int? EIhale { get; set; }
    public int? KismiTeklif { get; set; }
    public string? IhaleYeri { get; set; }
    public string? IsinYeri { get; set; }
    public int? DokumanSayisi { get; set; }
    public int? DetayCekildi { get; set; }
    public string? CreatedAt { get; set; }
    public string? UpdatedAt { get; set; }

    // İlişkiler (bir ihalenin birden çok özelliği/kodu/ilanı olabilir)
    public List<TenderCharacteristic> Characteristics { get; set; } = new();
    public List<TenderOkasCode> OkasCodes { get; set; } = new();
    public List<TenderAnnouncement> Announcements { get; set; } = new();

    // LLM'in dolduracağı alanlar
    public int? IlgiSkoru { get; set; }            // 0-100 uygunluk skoru
    public bool? SirketeUygunMu { get; set; }      // uygun mu bayrağı
    public string? LlmOzeti { get; set; }          // kısa özet
    public string? AnalizTarihi { get; set; }      // LLM ne zaman analiz etti
}