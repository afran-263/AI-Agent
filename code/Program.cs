using HrmsAgentApi;
using HrmsAgentApi.Services;
using Microsoft.OpenApi;
using System.Diagnostics;

var builder = WebApplication.CreateBuilder(args);

// ======================================================
// LOGGING CONFIGURATION
// Note: Console logging captures all levels (Info, Warning, Error)
// Errors are logged with ✗ prefix, Responses with ✓ prefix
// ======================================================

builder.Logging.ClearProviders();
builder.Logging.AddConsole();
builder.Logging.SetMinimumLevel(LogLevel.Information);

// ======================================================
// SERVICES
// ======================================================

builder.Services.AddControllers();

builder.Services.AddSingleton<HrmsDataService>();

// ======================================================
// SWAGGER / OPENAPI
// ======================================================

builder.Services.AddEndpointsApiExplorer();

builder.Services.AddSwaggerGen(options =>
{
    options.SwaggerDoc("v1", new OpenApiInfo
    {
        Title = "HRMS Agent API",
        Version = "v1",
        Description = "Provides employee and task data tools for Azure AI Foundry Agent"
    });

    // IMPORTANT FOR AZURE AI FOUNDRY
    options.CustomOperationIds(api =>
    {
        return api.ActionDescriptor.RouteValues["action"];
    });
});

// ======================================================
// CORS
// ======================================================

builder.Services.AddCors(options =>
{
    options.AddPolicy("AllowAll", policy =>
    {
        policy.AllowAnyOrigin()
              .AllowAnyMethod()
              .AllowAnyHeader();
    });
});

var app = builder.Build();

// ======================================================
// ERROR HANDLING & REQUEST LOGGING MIDDLEWARE
// Note: Catches unhandled exceptions and logs all requests/responses
// Status indicator: ✓ for success, ✗ for errors
// ======================================================

app.Use(async (context, next) =>
{
    var logger =
        context.RequestServices.GetRequiredService<ILogger<Program>>();

    try
    {
        var stopwatch = Stopwatch.StartNew();

        logger.LogInformation(
            "➤ [REQUEST] {Method} {Path}{Query}",
            context.Request.Method,
            context.Request.Path,
            context.Request.QueryString);

        await next();

        stopwatch.Stop();

        // Determine log level based on status code
        var statusCode = context.Response.StatusCode;
        var logLevel = statusCode >= 500 ? LogLevel.Error 
                     : statusCode >= 400 ? LogLevel.Warning 
                     : LogLevel.Information;

        logger.Log(
            logLevel,
            "✓ [RESPONSE] {Method} {Path}{Query} => {StatusCode} ({ElapsedMilliseconds}ms)",
            context.Request.Method,
            context.Request.Path,
            context.Request.QueryString,
            statusCode,
            stopwatch.ElapsedMilliseconds);
    }
    catch (Exception ex)
    {
        logger.LogError(
            ex,
            "✗ [ERROR] Unhandled exception: {Message} | Path: {Path}",
            ex.Message,
            context.Request.Path);

        // Send error response if response hasn't started
        if (!context.Response.HasStarted)
        {
            context.Response.StatusCode = 500;
            await context.Response.WriteAsJsonAsync(new
            {
                error = "Internal Server Error",
                message = ex.Message,
                timestamp = DateTime.UtcNow
            });
        }
    }
});

// ======================================================
// PIPELINE
// ======================================================

app.UseCors("AllowAll");

app.UseSwagger();

app.UseSwaggerUI(options =>
{
    options.SwaggerEndpoint(
        "/swagger/v1/swagger.json",
        "HRMS Agent API V1");

    options.RoutePrefix = string.Empty;
});

app.UseAuthorization();

app.MapControllers();

// ======================================================
// EXPORT OPENAPI FILE
// ======================================================

var appLogger = app.Services.GetRequiredService<ILogger<Program>>();

try
{
    await OpenApiExporter.ExportAsync(
        app.Services,
        "hrms-openapi-foundry.json");

    appLogger.LogInformation(
        "✓ [SUCCESS] OpenAPI file generated: hrms-openapi-foundry.json");
}
catch (Exception ex)
{
    appLogger.LogError(
        ex,
        "✗ [CRITICAL] OpenAPI export failed: {Message}",
        ex.Message);
}

app.Run();