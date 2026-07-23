namespace EkapBackend.DTOs;

public class PagedResultDto<T>
{
    public List<T> Veriler { get; set; } = new();
    public int ToplamKayit { get; set; }
    public int ToplamSayfa { get; set; }
    public int MevcutSayfa { get; set; }
    public int SayfaBoyutu { get; set; }
}
