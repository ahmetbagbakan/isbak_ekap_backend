#!/usr/bin/env python3
"""
EKAP PostgreSQL -> CSV Dışa Aktarıcı

PostgreSQL veritabanındaki tabloları data/csv/ klasörüne:
1. Türkçe karakterlerin Excel'de bozulmaması için `utf-8-sig` formatında,
2. Satır içi enter/newline karakterlerini temizleyerek,
3. Türkçe Excel ile %100 uyumlu noktalı virgül (;) ayırıcıyla aktarır.
"""

import psycopg2
import csv
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "isbak_ekap_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")

OUTPUT_DIR = os.path.join(BASE_DIR, "data", "csv")

def export_table_to_csv(conn, table_name, output_csv):
    print(f"[{table_name}] tablosu {output_csv} dosyasına aktarılıyor...")
    c = conn.cursor()
    c.execute(f"SELECT * FROM {table_name}")
    
    columns = [description[0] for description in c.description]
    
    count = 0
    with open(output_csv, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f, delimiter=";", quoting=csv.QUOTE_ALL)
        writer.writerow(columns)
        
        while True:
            rows = c.fetchmany(5000)
            if not rows:
                break
                
            cleaned_rows = []
            for row in rows:
                cleaned_row = []
                for val in row:
                    if isinstance(val, str):
                        cleaned_val = val.replace("\r\n", " ").replace("\n", " ").replace("\r", " ").strip()
                        cleaned_row.append(cleaned_val)
                    else:
                        cleaned_row.append(val)
                cleaned_rows.append(cleaned_row)
                
            writer.writerows(cleaned_rows)
            count += len(rows)
            print(f"  {count:,} satır aktarıldı...", end="\r")
            
    print(f"\n[OK] {table_name} -> {output_csv} tamamlandi ({count:,} satir).\n")
    c.close()


def main():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
    except Exception as e:
        print(f"HATA: PostgreSQL veritabanına bağlanılamadı ({e})")
        return

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    tables = [
        ("tenders", "tenders.csv"),
        ("tender_characteristics", "tender_characteristics.csv"),
        ("tender_okas_codes", "tender_okas_codes.csv"),
        ("tender_announcements", "tender_announcements.csv")
    ]
    
    for table_name, csv_filename in tables:
        out_path = os.path.join(OUTPUT_DIR, csv_filename)
        export_table_to_csv(conn, table_name, out_path)
        
    conn.close()
    print("Tüm tablolar PostgreSQL'den data/csv/ klasörüne düzgün CSV formatında aktarıldı!")

if __name__ == "__main__":
    main()
