namespace EkapBackend.Models;

public class TenderCharacteristic
{
    public int Id { get; set; }                    // otomatik artan anahtar
    public string TenderId { get; set; } = null!;  // hangi ihaleye ait
    public string Ozellik { get; set; } = null!;

    public Tender Tender { get; set; } = null!;
}