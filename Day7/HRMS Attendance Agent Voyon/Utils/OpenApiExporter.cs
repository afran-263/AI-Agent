using Swashbuckle.AspNetCore.Swagger;
using Microsoft.OpenApi;

namespace HrmsAgentApi.Utils;

public static class OpenApiExporter
{
    public static async Task ExportAsync(
        IServiceProvider services,
        string outputFile)
    {
        using var scope = services.CreateScope();

        var swaggerProvider =
            scope.ServiceProvider.GetRequiredService<ISwaggerProvider>();

        var swaggerDocument =
            swaggerProvider.GetSwagger("v1");

        await using var stream = File.Create(outputFile);

        await swaggerDocument.SerializeAsJsonAsync(
            stream,
            OpenApiSpecVersion.OpenApi3_0,
            CancellationToken.None);
    }
}
