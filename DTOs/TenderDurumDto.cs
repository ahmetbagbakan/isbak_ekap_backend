namespace EkapBackend.DTOs;

public class TenderDurumDto
{
    // Geçerli değerler: "inceleniyor", "alınması öneriliyor", "alınması önerilmiyor"
    // null veya boş string göndermek etiketi kaldırır (sıfırlar)
    public string? TakipDurumu { get; set; }
}
