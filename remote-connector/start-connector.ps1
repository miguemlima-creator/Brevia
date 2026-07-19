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
# Ruta corta 8.3 (sin espacios): las comillas anidadas no sobreviven el viaje
# PowerShell -> npx -> node en Windows y "C:\Users\Miguel Marrero\..." se parte.
$fso = New-Object -ComObject Scripting.FileSystemObject
$RepoRootShort = $fso.GetFolder($RepoRoot).ShortPath
if ($McpCommand -eq "") {
    $McpCommand = "python $RepoRootShort\brevia\mcp_server.py"
}

foreach ($tool in @("node", "npx", "cloudflared")) {
    if (-not (Get-Command $tool -ErrorAction SilentlyContinue)) {
        Write-Error "Falta '$tool'. Revisa los requisitos en remote-connector\README.md"
        exit 1
    }
}

$gatewayCmd = "npx -y supergateway --stdio `"$McpCommand`" --port $Port --outputTransport $Transport"
if ($Transport -eq "streamableHttp") { $gatewayCmd += " --streamableHttpPath /mcp" }

# Ventanas via archivos .cmd: es la unica forma determinista de que las comillas
# de --stdio lleguen intactas a node (Start-Process powershell -Command las come).
$tmpDir = Join-Path $env:TEMP "brevia-connector"
New-Item -ItemType Directory -Force $tmpDir | Out-Null
Set-Content -Path "$tmpDir\gateway.cmd" -Value "@echo off`r`n$gatewayCmd" -Encoding ascii
Set-Content -Path "$tmpDir\tunnel.cmd" -Value "@echo off`r`ncloudflared tunnel --url http://localhost:$Port" -Encoding ascii

Write-Host "[1/2] Gateway MCP->HTTP en puerto $Port ($Transport)..."
Start-Process cmd -ArgumentList "/k", "$tmpDir\gateway.cmd"

Start-Sleep -Seconds 3

Write-Host "[2/2] Tunel Cloudflare... (copia la URL https://....trycloudflare.com que aparece)"
Start-Process cmd -ArgumentList "/k", "$tmpDir\tunnel.cmd"

$path = if ($Transport -eq "streamableHttp") { "/mcp" } else { "/sse" }
Write-Host ""
Write-Host "Listo. En claude.ai -> Settings -> Connectors -> Add custom connector:"
Write-Host "    https://<url-del-tunel>$path"
