param(
  [string]$ServiceName = 'taxsphere_backup',
  [Parameter(Mandatory=$true)][string]$OutputDirectory
)
$ErrorActionPreference = 'Stop'
if (-not $env:PGSERVICEFILE -or -not $env:PGPASSFILE) { throw 'Set PGSERVICEFILE and PGPASSFILE to protected PostgreSQL client config files first.' }
New-Item -ItemType Directory -Force -Path $OutputDirectory | Out-Null
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$target = Join-Path $OutputDirectory "taxsphere-$stamp.dump"
& pg_dump --dbname="service=$ServiceName" --format=custom --file=$target --no-password
if ($LASTEXITCODE -ne 0) { throw "pg_dump failed with exit code $LASTEXITCODE" }
Get-FileHash -Algorithm SHA256 -LiteralPath $target | Select-Object Hash, Path
