using Microsoft.EntityFrameworkCore;
using EkapBackend.Models;

namespace EkapBackend.Data;

public class EkapDbContext : DbContext
{
    public EkapDbContext(DbContextOptions<EkapDbContext> options)
        : base(options) { }

    // Her DbSet, bir tabloya karşılık gelir
    public DbSet<Tender> Tenders => Set<Tender>();
    public DbSet<TenderCharacteristic> TenderCharacteristics => Set<TenderCharacteristic>();
    public DbSet<TenderOkasCode> TenderOkasCodes => Set<TenderOkasCode>();
    public DbSet<TenderAnnouncement> TenderAnnouncements => Set<TenderAnnouncement>();

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        // Tablo isimlerini SQLite'takiyle aynı tutuyoruz (küçük harf)
        modelBuilder.Entity<Tender>().ToTable("tenders");
        modelBuilder.Entity<TenderCharacteristic>().ToTable("tender_characteristics");
        modelBuilder.Entity<TenderOkasCode>().ToTable("tender_okas_codes");
        modelBuilder.Entity<TenderAnnouncement>().ToTable("tender_announcements");

        // İlişkiler: bir ihale → çok özellik/kod/ilan
        modelBuilder.Entity<Tender>()
            .HasMany(t => t.Characteristics)
            .WithOne(c => c.Tender)
            .HasForeignKey(c => c.TenderId);

        modelBuilder.Entity<Tender>()
            .HasMany(t => t.OkasCodes)
            .WithOne(o => o.Tender)
            .HasForeignKey(o => o.TenderId);

        modelBuilder.Entity<Tender>()
            .HasMany(t => t.Announcements)
            .WithOne(a => a.Tender)
            .HasForeignKey(a => a.TenderId);
            
    }
}