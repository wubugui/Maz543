param([string]$Destination = 'D:\maz543-references')
$ErrorActionPreference = 'Stop'
$source = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\external\maz543-references'))
$target = [IO.Path]::GetFullPath($Destination)
if (-not (Test-Path -LiteralPath $source -PathType Container)) { throw 'Extract the complete archive first.' }
if (Test-Path -LiteralPath $target) { throw "Destination already exists. Compare it with $source before merging: $target" }
New-Item -ItemType Directory -Path $target | Out-Null
Get-ChildItem -LiteralPath $source -Force | ForEach-Object {
    Copy-Item -LiteralPath $_.FullName -Destination $target -Recurse
}
Write-Host "References restored to $target"
