#!/usr/bin/env python3
"""
EKAP Toplu İhale Çekme Betiği (Bulk Fetcher)

Tüm ihaleleri doğrudan PostgreSQL veritabanına iki aşamada çeker:
  Aşama 1 — Liste verisi: Tarih aralıklarıyla sayfalayarak tüm ihalelerin
             temel bilgilerini (tenders tablosu) doldurur.
  Aşama 2 — Detay verisi: Detayı henüz çekilmemiş ihalelerin özellik,
             OKAS ve ilan bilgilerini doldurur.

Kullanım:
    python run_scraper.py                        # Her iki aşamayı çalıştır
    python run_scraper.py --phase 1              # Sadece liste çek
    python run_scraper.py --phase 2              # Sadece detayları çek
    python run_scraper.py --status               # İlerleme raporunu göster
    python run_scraper.py --wipe                 # DB'yi sıfırlayıp baştan başla
"""

import asyncio
import psycopg2
import sys
import os
import argparse
import time
import logging
from datetime import datetime, timedelta

from dotenv import load_dotenv

# .env dosyasından bağlantı şifrelerini yükle
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))

# Scraper istemcisini import et
from ihale_client import EKAPClient

# PostgreSQL Bağlantı Ayarları (.env, Ortam Değişkenleri veya CLI)
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "isbak_ekap_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")

LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bulk_fetcher.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger("bulk_fetcher")


# ---------------------------------------------------------------------------
# Veritabanı Katmanı (PostgreSQL)
# ---------------------------------------------------------------------------

def get_db_connection(host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD):
    """PostgreSQL sunucusuna bağlanır, gerekirse DB'yi otomatik oluşturur."""
    hosts_to_try = [host]
    if host in ("localhost", "127.0.0.1"):
        hosts_to_try = ["127.0.0.1", "localhost"]

    last_error = None
    for attempt in range(5):
        for h in hosts_to_try:
            try:
                return psycopg2.connect(
                    host=h,
                    port=port,
                    dbname=dbname,
                    user=user,
                    password=password,
                    connect_timeout=5
                )
            except psycopg2.OperationalError as e:
                last_error = e
                if f'database "{dbname}" does not exist' in str(e) or 'veri tabanı yok' in str(e):
                    log.info(f"'{dbname}' veritabanı bulunamadı, oluşturuluyor...")
                    sys_conn = psycopg2.connect(
                        host=h,
                        port=port,
                        dbname="postgres",
                        user=user,
                        password=password,
                        connect_timeout=5
                    )
                    sys_conn.autocommit = True
                    cur = sys_conn.cursor()
                    cur.execute(f'CREATE DATABASE "{dbname}"')
                    cur.close()
                    sys_conn.close()
                    log.info(f"✅ '{dbname}' veritabanı oluşturuldu.")

                    return psycopg2.connect(
                        host=h,
                        port=port,
                        dbname=dbname,
                        user=user,
                        password=password,
                        connect_timeout=5
                    )
        time.sleep(1)
    
    log.error(f"PostgreSQL bağlantı hatası: {last_error}")
    raise last_error


def init_db(conn, wipe: bool = False):
    """Tabloları ve indeksleri oluşturur. wipe=True ise tabloları önce sıfırlar."""
    c = conn.cursor()

    if wipe:
        log.warning("⚠️ Veritabanı tabloları sıfırlanıyor (WIPE)...")
        for table in ["tender_announcements", "tender_okas_codes",
                       "tender_characteristics", "tenders"]:
            c.execute(f"DROP TABLE IF EXISTS {table} CASCADE;")
        conn.commit()

    # 1. Tenders Tablosu
    c.execute("""
        CREATE TABLE IF NOT EXISTS tenders (
            id            TEXT PRIMARY KEY,
            ikn           TEXT UNIQUE NOT NULL,
            adi           TEXT,
            idare_adi     TEXT,
            il            TEXT,
            ihale_tarihi  TEXT,
            ihale_turu    TEXT,
            ihale_usulu   TEXT,
            ihale_durumu  TEXT,
            kapsam        TEXT,
            e_ihale       INTEGER DEFAULT 0,
            kismi_teklif  INTEGER DEFAULT 0,
            ihale_yeri    TEXT,
            isin_yeri     TEXT,
            dokuman_sayisi INTEGER DEFAULT 0,
            created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # 2. Tender Characteristics Tablosu
    c.execute("""
        CREATE TABLE IF NOT EXISTS tender_characteristics (
            id         SERIAL PRIMARY KEY,
            tender_id  TEXT NOT NULL REFERENCES tenders(id) ON DELETE CASCADE,
            ozellik    TEXT NOT NULL
        );
    """)

    # 3. Tender OKAS Codes Tablosu
    c.execute("""
        CREATE TABLE IF NOT EXISTS tender_okas_codes (
            id         SERIAL PRIMARY KEY,
            tender_id  TEXT NOT NULL REFERENCES tenders(id) ON DELETE CASCADE,
            kod        TEXT,
            ad         TEXT
        );
    """)

    # 4. Tender Announcements Tablosu
    c.execute("""
        CREATE TABLE IF NOT EXISTS tender_announcements (
            id          TEXT PRIMARY KEY,
            tender_id   TEXT NOT NULL REFERENCES tenders(id) ON DELETE CASCADE,
            ilan_tipi   TEXT,
            ilan_tarihi TEXT,
            baslik      TEXT,
            icerik      TEXT,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Performans İndeksleri
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_tenders_tarih ON tenders(ihale_tarihi);",
        "CREATE INDEX IF NOT EXISTS idx_tenders_il ON tenders(il);",
        "CREATE INDEX IF NOT EXISTS idx_tenders_durum ON tenders(ihale_durumu);",
        "CREATE INDEX IF NOT EXISTS idx_tenders_turu ON tenders(ihale_turu);",
        "CREATE INDEX IF NOT EXISTS idx_chars_tender_id ON tender_characteristics(tender_id);",
        "CREATE INDEX IF NOT EXISTS idx_okas_tender_id ON tender_okas_codes(tender_id);",
        "CREATE INDEX IF NOT EXISTS idx_ann_tender_id ON tender_announcements(tender_id);",
    ]
    for idx_sql in indexes:
        c.execute(idx_sql)

    conn.commit()
    c.close()


def save_tender_from_raw(conn, raw: dict):
    """Ham API yanıtından tek bir ihaleyi PostgreSQL'e kaydeder."""
    c = conn.cursor()

    c.execute("""
        INSERT INTO tenders
            (id, ikn, adi, idare_adi, il, ihale_tarihi, ihale_turu,
             ihale_usulu, ihale_durumu, e_ihale, dokuman_sayisi)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (id) DO NOTHING
    """, (
        raw.get("id"),
        raw.get("ikn"),
        raw.get("ihaleAdi"),
        raw.get("idareAdi"),
        raw.get("ihaleIlAdi"),
        raw.get("ihaleTarihSaat"),
        raw.get("ihaleTipAciklama"),
        raw.get("ihaleUsulAciklama"),
        raw.get("ihaleDurumAciklama"),
        1 if raw.get("ihaleTip") == "E" else 0,
        raw.get("dokumanSayisi", 0),
    ))
    c.close()


def save_tender_details(conn, tender_id: str, details: dict):
    """Detay verisini PostgreSQL üzerindeki ihale kaydına ekler."""
    c = conn.cursor()
    basic = details.get("basic_info", {})

    c.execute("""
        UPDATE tenders SET
            kapsam       = %s,
            e_ihale      = %s,
            kismi_teklif = %s,
            ihale_yeri   = %s,
            isin_yeri    = %s,
            updated_at   = CURRENT_TIMESTAMP
        WHERE id = %s
    """, (
        basic.get("scope_description"),
        1 if basic.get("is_electronic") else 0,
        1 if basic.get("is_partial") else 0,
        basic.get("venue"),
        basic.get("location"),
        tender_id,
    ))

    # Özellik etiketleri
    c.execute("DELETE FROM tender_characteristics WHERE tender_id = %s", (tender_id,))
    for ozellik in details.get("characteristics", []):
        c.execute(
            "INSERT INTO tender_characteristics (tender_id, ozellik) VALUES (%s, %s)",
            (tender_id, ozellik)
        )

    # OKAS kodları
    c.execute("DELETE FROM tender_okas_codes WHERE tender_id = %s", (tender_id,))
    for okas in details.get("okas_codes", []):
        c.execute(
            "INSERT INTO tender_okas_codes (tender_id, kod, ad) VALUES (%s, %s, %s)",
            (tender_id, okas.get("code"), okas.get("name"))
        )

    # İlanlar
    announcements = details.get("announcements_summary", {}).get("announcements", [])
    for ann in announcements:
        ann_id = ann.get("id")
        if not ann_id:
            continue
        c.execute("""
            INSERT INTO tender_announcements
                (id, tender_id, ilan_tipi, ilan_tarihi, baslik, icerik)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                ilan_tipi = EXCLUDED.ilan_tipi,
                ilan_tarihi = EXCLUDED.ilan_tarihi,
                baslik = EXCLUDED.baslik,
                icerik = EXCLUDED.icerik
        """, (
            ann_id,
            tender_id,
            ann.get("type", {}).get("description"),
            ann.get("date"),
            ann.get("title"),
            ann.get("markdown_content"),
        ))
    c.close()


async def search_tenders_fast(client: EKAPClient, **kwargs) -> dict:
    """EKAPClient.search_tenders metodunu çağırır ve öğeleri döner."""
    start_date = kwargs.get("date_start")
    end_date = kwargs.get("date_end")
    page = kwargs.get("page", 1)
    page_size = kwargs.get("page_size", 100)
    skip = (page - 1) * page_size

    res = await client.search_tenders(
        tender_date_start=start_date,
        tender_date_end=end_date,
        limit=page_size,
        skip=skip
    )

    tenders = res.get("tenders", [])
    total_count = res.get("total_count", 0)

    raw_items = []
    for t in tenders:
        t_type = t.get("type")
        t_status = t.get("status")
        type_desc = t_type.get("description") if isinstance(t_type, dict) else t_type
        type_code = t_type.get("code") if isinstance(t_type, dict) else ""
        status_desc = t_status.get("description") if isinstance(t_status, dict) else t_status

        raw_items.append({
            "id": t.get("id"),
            "ikn": t.get("ikn"),
            "ihaleAdi": t.get("name"),
            "idareAdi": t.get("authority"),
            "ihaleIlAdi": t.get("province"),
            "ihaleTarihSaat": t.get("tender_datetime"),
            "ihaleTipAciklama": type_desc,
            "ihaleUsulAciklama": t.get("method"),
            "ihaleDurumAciklama": status_desc,
            "ihaleTip": type_code,
            "dokumanSayisi": t.get("document_count", 0),
        })

    return {
        "items": raw_items,
        "total_count": total_count,
        "page": page,
        "page_size": page_size,
    }


def generate_month_ranges(start_year: int = 2026, end_year: int = None):
    """Gelecek ihale ilanlarını da kapsayacak şekilde YYYY-MM-DD formatında tüm ay aralıklarını üretir."""
    now = datetime.now()
    if end_year is None:
        end_year = now.year + 1

    ranges = []
    for year in range(start_year, end_year + 1):
        for month in range(1, 13):
            if year == (now.year + 1) and month > now.month:
                break

            start_date = f"{year}-{month:02d}-01"
            if month == 12:
                end_date = f"{year}-12-31"
            else:
                next_month_first = datetime(year, month + 1, 1)
                last_day = (next_month_first - timedelta(days=1)).day
                end_date = f"{year}-{month:02d}-{last_day:02d}"

            month_key = f"{year}-{month:02d}"
            ranges.append((month_key, start_date, end_date))

    return ranges


async def fetch_phase1(
    client: EKAPClient,
    conn,
    start_year: int = 2026,
    page_size: int = 100,
    delay: float = 0.3,
):
    """Aşama 1: Tarih aralıklarıyla tüm ihalelerin liste verisini PostgreSQL'e çek."""
    month_ranges = generate_month_ranges(start_year=start_year)
    log.info(f"Aşama 1: Toplam {len(month_ranges)} ay aralığı taranacak (PostgreSQL).")

    total_saved = 0
    phase_start = time.time()

    for idx, (month_key, start_date, end_date) in enumerate(month_ranges, 1):
        log.info(f"[{idx}/{len(month_ranges)}] {month_key} ({start_date} - {end_date}) işleniyor...")

        try:
            first_page = await search_tenders_fast(
                client,
                date_start=start_date,
                date_end=end_date,
                page=1,
                page_size=page_size,
            )
        except Exception as e:
            log.error(f"  {month_key} ilk sayfa çekilemedi: {e}")
            continue

        total_in_month = first_page["total_count"]
        items = first_page["items"]
        total_pages = (total_in_month + page_size - 1) // page_size if page_size > 0 else 0

        log.info(f"  Toplam ihale: {total_in_month:,} ({total_pages} sayfa)")

        month_saved = 0
        for item in items:
            save_tender_from_raw(conn, item)
            month_saved += 1
        conn.commit()

        for page in range(2, total_pages + 1):
            await asyncio.sleep(delay)
            try:
                page_data = await search_tenders_fast(
                    client,
                    date_start=start_date,
                    date_end=end_date,
                    page=page,
                    page_size=page_size,
                )
                for item in page_data["items"]:
                    save_tender_from_raw(conn, item)
                    month_saved += 1
                conn.commit()
            except Exception as e:
                log.error(f"  Sayfa {page}/{total_pages} çekilemedi: {e}")

        total_saved += month_saved
        log.info(f"  ✓ {month_key} tamamlandı: {month_saved} ihale.")

    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM tenders")
    db_total = c.fetchone()[0]
    c.close()
    elapsed = time.time() - phase_start
    log.info(f"Aşama 1 tamamlandı! Toplam {db_total:,} ihale PostgreSQL'e kaydedildi.")


async def fetch_phase2(
    client: EKAPClient,
    conn,
    batch_size: int = 50,
    concurrency: int = 3,
    delay: float = 0.3,
):
    """Aşama 2: Detayı çekilmemiş ihalelerin detaylarını PostgreSQL'e doldur."""
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM tenders WHERE kapsam IS NULL AND isin_yeri IS NULL")
    remaining = c.fetchone()[0]
    c.close()

    if remaining == 0:
        log.info("Aşama 2: Detayı çekilecek ihale kalmadı. Tümü güncel!")
        return

    log.info(f"Aşama 2: Toplam {remaining:,} ihale detaylandırılacak...")
    processed = 0
    errors = 0
    sem = asyncio.Semaphore(concurrency)

    while True:
        c = conn.cursor()
        c.execute("SELECT id, ikn FROM tenders WHERE kapsam IS NULL AND isin_yeri IS NULL LIMIT %s", (batch_size,))
        batch = c.fetchall()
        c.close()

        if not batch:
            break

        async def process_one(tender_id, ikn):
            nonlocal processed, errors
            async with sem:
                try:
                    details = await client.get_tender_details(tender_id)
                    if not details.get("error"):
                        save_tender_details(conn, tender_id, details)
                    else:
                        errors += 1
                except Exception as e:
                    errors += 1

        tasks = [process_one(tid, ikn) for tid, ikn in batch]
        await asyncio.gather(*tasks)
        conn.commit()
        processed += len(batch)
        log.info(f"  Detay ilerleme: {processed}/{remaining}")


def print_status(conn=None, host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD):
    """PostgreSQL veritabanı durumunu ekrana yazdırır."""
    should_close = False
    if conn is None:
        try:
            conn = get_db_connection(host=host, port=port, dbname=dbname, user=user, password=password)
            should_close = True
        except Exception as e:
            print(f"\n  PostgreSQL Veritabanı Durumu: Bağlantı Kurulamadı ({e})")
            return

    c = conn.cursor()

    print("\n" + "=" * 60)
    print(f" POSTGRESQL VERİTABANI DURUM RAPORU ({dbname})")
    print("=" * 60)

    try:
        c.execute("SELECT COUNT(*) FROM tenders")
        total = c.fetchone()[0]

        c.execute("SELECT COUNT(*) FROM tenders WHERE kapsam IS NOT NULL OR isin_yeri IS NOT NULL")
        with_details = c.fetchone()[0]

        c.execute("SELECT COUNT(*) FROM tender_characteristics")
        chars = c.fetchone()[0]

        c.execute("SELECT COUNT(*) FROM tender_okas_codes")
        okas = c.fetchone()[0]

        c.execute("SELECT COUNT(*) FROM tender_announcements")
        anns = c.fetchone()[0]

        print(f"\n  Toplam ihale       : {total:>12,}")
        print(f"  Detayı çekilmiş   : {with_details:>12,}")
        print(f"  Detayı çekilmemiş : {total - with_details:>12,}")
        print(f"  Özellik kaydı     : {chars:>12,}")
        print(f"  OKAS kodu kaydı   : {okas:>12,}")
        print(f"  İlan kaydı        : {anns:>12,}")

        c.execute("SELECT pg_size_pretty(pg_database_size(%s))", (dbname,))
        db_size = c.fetchone()[0]
        print(f"\n  PostgreSQL DB Boyutu: {db_size:>10}")

    except Exception as e:
        print(f"\n  Veritabanı okunamadı: {e}")

    print("\n" + "=" * 60)
    c.close()
    if should_close:
        conn.close()


async def run(args):
    conn = get_db_connection(
        host=args.host,
        port=args.port,
        dbname=args.dbname,
        user=args.user,
        password=args.password
    )

    init_db(conn, wipe=args.wipe)

    if args.status:
        print_status(conn=conn, dbname=args.dbname)
        conn.close()
        return

    client = EKAPClient()

    try:
        if args.phase in (None, 1):
            await fetch_phase1(client, conn, start_year=args.start_year)

        if args.phase in (None, 2):
            await fetch_phase2(client, conn, concurrency=args.concurrency)
    finally:
        conn.commit()
        conn.close()

    print_status(host=args.host, port=args.port, dbname=args.dbname, user=args.user, password=args.password)


def main():
    parser = argparse.ArgumentParser(description="EKAP Toplu İhale Çekme Betiği (PostgreSQL)")
    parser.add_argument("--phase", type=int, choices=[1, 2], default=None, help="Aşama seçimi (1=liste, 2=detay)")
    parser.add_argument("--start-year", type=int, default=2026, help="Başlangıç yılı")
    parser.add_argument("--page-size", type=int, default=100, help="Sayfa boyutu")
    parser.add_argument("--concurrency", type=int, default=3, help="Eşzamanlılık")
    parser.add_argument("--delay", type=float, default=0.3, help="İstek arası bekleme")
    parser.add_argument("--status", action="store_true", help="Durum raporunu göster")
    parser.add_argument("--wipe", action="store_true", help="DB'yi sıfırla")

    # PostgreSQL Bağlantı Ayarları
    parser.add_argument("--host", type=str, default=DB_HOST, help="PostgreSQL Host")
    parser.add_argument("--port", type=int, default=DB_PORT, help="PostgreSQL Port")
    parser.add_argument("--dbname", type=str, default=DB_NAME, help="PostgreSQL DB Name")
    parser.add_argument("--user", type=str, default=DB_USER, help="PostgreSQL User")
    parser.add_argument("--password", type=str, default=DB_PASSWORD, help="PostgreSQL Password")

    args = parser.parse_args()

    if args.status:
        print_status(host=args.host, port=args.port, dbname=args.dbname, user=args.user, password=args.password)
    else:
        asyncio.run(run(args))


if __name__ == "__main__":
    main()
