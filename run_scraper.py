#!/usr/bin/env python3
"""
EKAP İhale Veri Çekme Motoru - Ana Çalıştırma Betiği

Kullanım:
    python run_scraper.py                 # Tüm ihaleleri ve detayları sırasıyla çek
    python run_scraper.py --phase 1       # Sadece liste verilerini çek (Aşama 1)
    python run_scraper.py --phase 2       # Sadece ihale detaylarını çek (Aşama 2)
    python run_scraper.py --status        # Mevcut veritabanı durum raporunu göster
    python run_scraper.py --export-csv    # Verileri CSV dosyalarına dönüştür
"""

import sys
import os

# scraper/ klasörünü import yoluna ekle
SCRAPER_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scraper")
sys.path.insert(0, SCRAPER_DIR)

if __name__ == "__main__":
    if "--export-csv" in sys.argv:
        from export_csv import main as export_main
        export_main()
    else:
        from bulk_fetcher import main as fetcher_main
        fetcher_main()
