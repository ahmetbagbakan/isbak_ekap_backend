namespace EkapBackend.Models;

public class TenderAnnouncement
{
    public string Id { get; set; } = null!;
    public string TenderId { get; set; } = null!;
    public string? IlanTipi { get; set; }
    public string? IlanTarihi { get; set; }
    public string? Baslik { get; set; }
    public string? Icerik { get; set; }
    public string? CreatedAt { get; set; }

    public Tender Tender { get; set; } = null!;
}