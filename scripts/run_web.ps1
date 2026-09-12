$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

Write-Host "Starting Promptly API on http://127.0.0.1:8000 ..."
$api = Start-Process powershell.exe -ArgumentList @(
    "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command",
    "Set-Location '$projectRoot'; python -m uvicorn api.index:app --reload --port 8000"
) -PassThru

try {
    Set-Location (Join-Path $projectRoot "frontend")
    npm run dev
}
finally {
    if ($api -and -not $api.HasExited) { Stop-Process -Id $api.Id }
}
