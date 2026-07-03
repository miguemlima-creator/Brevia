# Levanta un MCP local como servidor HTTP + tunel publico de Cloudflare.
# Uso:
#   .\start-connector.ps1                                        # expone el MCP de Brevia
#   .\start-connector.ps1 -McpCommand "python C:\x\mi_mcp.py"    # expone otro MCP
#   .\start-connector.ps1 -Transport sse                         # modo SSE (fallback)
param(
    [string]$McpCommand = "",
    [int]$Port = 8100,
    [ValidateSet("streamableHttp", "sse")]
    [string]$Transport = "streamableHttp"
)

$RepoRoot = Split-Path -Parent $PSScriptRoot
if ($McpCommand -eq "") {
    $McpCommand = "python `"$RepoRoot\brevia\mcp_server.py`""
}

foreach ($tool in @("node", "npx", "cloudflared")) {
    if (-not (Get-Command $tool -ErrorAction SilentlyContinue)) {
        Write-Error "Falta '$tool'. Revisa los requisitos en remote-connector\README.md"
        exit 1
    }
}

$gatewayArgs = "-y supergateway --stdio `"$McpCommand`" --port $Port --outputTransport $Transport"
if ($Transport -eq "streamableHttp") { $gatewayArgs += " --streamableHttpPath /mcp" }

Write-Host "[1/2] Gateway MCP->HTTP en puerto $Port ($Transport)..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", "npx $gatewayArgs"

Start-Sleep -Seconds 3

Write-Host "[2/2] Tunel Cloudflare... (copia la URL https://....trycloudflare.com que aparece)"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cloudflared tunnel --url http://localhost:$Port"

$path = if ($Transport -eq "streamableHttp") { "/mcp" } else { "/sse" }
Write-Host ""
Write-Host "Listo. En claude.ai -> Settings -> Connectors -> Add custom connector:"
Write-Host "    https://<url-del-tunel>$path"
