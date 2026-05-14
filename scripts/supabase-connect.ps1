# Supabase Postgres: verifies connection, then runs migrations (unless -SkipMigrate).
# In .env set DATABASE_URL or SUPABASE_DATABASE_URL to the URI from Supabase (Project Settings → Database).
param(
    [switch]$SkipMigrate
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

Write-Host "Project root: $Root" -ForegroundColor Cyan
if ($SkipMigrate) {
    python manage.py check_database
} else {
    python manage.py check_database --migrate
}
exit $LASTEXITCODE
