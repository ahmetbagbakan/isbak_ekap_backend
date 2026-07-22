namespace EkapBackend.Models;

public class TenderOkasCode
{
    public int Id { get; set; }
    public string TenderId { get; set; } = null!;
    public string? Kod { get; set; }
    public string? Ad { get; set; }

    public Tender Tender { get; set; } = null!;
    
}