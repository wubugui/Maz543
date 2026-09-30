param([string]$Archive = (Join-Path $PSScriptRoot 'MAZ543_COMPLETE_20260906.zip'))
$ErrorActionPreference = 'Stop'
$checksumFile = "$Archive.sha256"
$expected = ((Get-Content -LiteralPath $checksumFile -Raw).Trim() -split '\s+')[0]
$actual = (Get-FileHash -LiteralPath $Archive -Algorithm SHA256).Hash
if ($actual -ine $expected) { throw 'SHA256 mismatch: copy is damaged or incomplete.' }
Write-Host 'SHA256 OK: archive matches the verified source copy.'
