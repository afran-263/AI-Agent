using HrmsAgentApi.Services;
using HrmsAgentApi.Utils;
using Microsoft.Extensions.Options;
using System.Diagnostics;
using System.Reflection;

var builder = WebApplication.CreateBuilder(args);

// ─── Logging ──────────────────────────────────────────────────────────────────
builder.Logging.ClearProviders();
builder.Logging.AddConsole();
builder.Logging.SetMinimumLevel(LogLevel.Information);

// ─── Voyon HRMS configuration ─────────────────────────────────────────────────
// BearerToken comes from user-secrets (dev) or environment variable (prod).
// NEVER put the token in appsettings.json.
builder.Services.Configure<VoyonHrmsOptions>(
    builder.Configuration.GetSection(VoyonHrmsOptions.Section));

// ─── HTTP client for Voyon Folks API ─────────────────────────────────────────
builder.Services.AddHttpClient("VoyonFolks", (sp, client) =>
{
    var opts = sp.GetRequiredService<IOptions<VoyonHrmsOptions>>().Value;
    client.BaseAddress = new Uri(opts.BaseUrl);
    client.Timeout = TimeSpan.FromSeconds(30);
    client.DefaultRequestHeaders.Add("Accept", "application/json");
});

// ─── Application services ─────────────────────────────────────────────────────
builder.Services.AddScoped<VoyonHrmsClient>();

// ─── Controllers + Swagger ───────────────────────────────────────────────────
builder.Services.AddControllers();
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen(options =>
{
    var xmlFile = $"{Assembly.GetExecutingAssembly().GetName().Name}.xml";
    var xmlPath = Path.Combine(AppContext.BaseDirectory, xmlFile);
    if (File.Exists(xmlPath))
        options.IncludeXmlComments(xmlPath);

    options.SwaggerDoc("v1", new()
    {
        Title       = "HRMS Agent API",
        Version     = "v1",
        Description = "Proxies Voyon Folks HRMS attendance data to Azure AI Foundry Agent tools. " +
                      "All data is fetched live from Voyon using a pre-issued Bearer token."
    });

    options.CustomOperationIds(api =>
        api.ActionDescriptor.RouteValues["action"]);
});

// ─── CORS ─────────────────────────────────────────────────────────────────────
builder.Services.AddCors(options =>
    options.AddPolicy("AllowAll", p =>
        p.AllowAnyOrigin().AllowAnyMethod().AllowAnyHeader()));

var app = builder.Build();

// ─── Request logging + error handling middleware ──────────────────────────────
app.Use(async (context, next) =>
{
    var logger = context.RequestServices.GetRequiredService<ILogger<Program>>();
    var sw = Stopwatch.StartNew();
    logger.LogInformation("→ {Method} {Path}{Query}",
        context.Request.Method, context.Request.Path, context.Request.QueryString);
    try
    {
        await next();
        sw.Stop();
        var level = context.Response.StatusCode >= 500 ? LogLevel.Error
                  : context.Response.StatusCode >= 400 ? LogLevel.Warning
                  : LogLevel.Information;
        logger.Log(level, "← {Status} {Method} {Path} ({Ms}ms)",
            context.Response.StatusCode, context.Request.Method,
            context.Request.Path, sw.ElapsedMilliseconds);
    }
    catch (Exception ex)
    {
        logger.LogError(ex, "Unhandled exception on {Path}", context.Request.Path);
        if (!context.Response.HasStarted)
        {
            context.Response.StatusCode = 500;
            await context.Response.WriteAsJsonAsync(new
            {
                error   = "Internal Server Error",
                message = ex.Message,
                timestamp = DateTime.UtcNow
            });
        }
    }
});

// ─── Pipeline ─────────────────────────────────────────────────────────────────
app.UseCors("AllowAll");
app.UseSwagger();
app.UseSwaggerUI(o =>
{
    o.SwaggerEndpoint("/swagger/v1/swagger.json", "HRMS Agent API V1");
    o.RoutePrefix = string.Empty; // Swagger UI at root
});
app.UseAuthorization();
app.MapControllers();

// ─── Export OpenAPI file for Azure AI Foundry ─────────────────────────────────
var appLogger = app.Services.GetRequiredService<ILogger<Program>>();
try
{
    await OpenApiExporter.ExportAsync(app.Services, "hrms-openapi-foundry.json");
    appLogger.LogInformation("✓ OpenAPI file generated: hrms-openapi-foundry.json");
}
catch (Exception ex)
{
    appLogger.LogError(ex, "✗ OpenAPI export failed: {Message}", ex.Message);
}

app.Run();