namespace EkapBackend.DTOs;

public class FilterOptionsDto
{
    public List<string> Iller { get; set; } = new();
    public List<string> Turler { get; set; } = new();
    public List<string> Durumlar { get; set; } = new();
}
