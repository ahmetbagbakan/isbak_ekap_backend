using Microsoft.EntityFrameworkCore;
using EkapBackend.Data;
using EFCore.NamingConventions;

var builder = WebApplication.CreateBuilder(args);

//DbContext'i uygulamaya kaydet
builder.Services.AddDbContext<EkapDbContext>(options =>
    options.UseNpgsql(builder.Configuration.GetConnectionString("DefaultConnection"))
            .UseSnakeCaseNamingConvention());

var app = builder.Build();
app.Run();


