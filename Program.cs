using Microsoft.EntityFrameworkCore;
using EkapBackend.Data;

var builder = WebApplication.CreateBuilder(args);

//DbContext'i uygulamaya kaydet
builder.Services.AddDbContext<EkapDbContext>(options =>
    options.UseNpgsql(builder.Configuration.GetConnectionString("DefaultConnection")));

var app = builder.Build();
app.Run();
