namespace EkapBackend.DTOs;

public class TenderAnalysisDto
{
    public int IlgiSkoru { get; set; }          // 0-100 arası uygunluk skoru
    public bool SirketeUygunMu { get; set; }
    public string? LlmOzeti { get; set; }       // 1-3 cümlelik yapay zeka özeti
}
