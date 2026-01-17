# =========================
# Usage
#   .\deploy.ps1 -EnvName dev
#   .\deploy.ps1 -EnvName prod
#
# Notes
#   Uses .env.<EnvName> if present, otherwise .env
#   Uses backend/.env.<EnvName> for Cloud Run env vars if present
# =========================
# =========================
# .env loader
# =========================
function Get-Environment {
    param (
        [string]$Path = ".env"
    )

    if (!(Test-Path $Path)) {
        Write-Error "❌ .env file not found: $Path"
        exit 1
    }

    Get-Content $Path | ForEach-Object {
        if ($_ -match '^\s*#' -or $_ -match '^\s*$') {
            return
        }

        $name, $value = $_ -split '=', 2
        $name = $name.Trim()
        $value = $value.Trim()

        Set-Item -Path "Env:$name" -Value $value
    }
}

# =========================
# main
# =========================
param (
    [string]$EnvName = "local"
)

$RootEnvPath = ".env.$EnvName"
if (Test-Path $RootEnvPath) {
    Get-Environment -Path $RootEnvPath
    Write-Host "Loaded env file: $RootEnvPath"
} else {
    Get-Environment -Path ".env"
    Write-Host "Loaded env file: .env"
}

$ProjectId = $Env:PROJECT_ID
$Region = $Env:REGION
$ServiceName = $Env:SERVICE_NAME
$Repository = $Env:REPOSITORY
$ImageName = $Env:IMAGE_NAME

$Image = "$Region-docker.pkg.dev/$ProjectId/${Repository}/${ImageName}:latest"
$CacheImage = "$Region-docker.pkg.dev/$ProjectId/${Repository}/$ImageName-cache"

$BackendEnvPath = "backend/.env.$EnvName"
if (!(Test-Path $BackendEnvPath)) {
    $BackendEnvPath = "backend/.env"
}
Write-Host "Backend env file: $BackendEnvPath"

$Substitutions = @(
    "_REGION=$Region"
    "_SERVICE_NAME=$ServiceName"
    "_IMAGE=$Image"
    "_CACHE_IMAGE=$CacheImage"
    "_BACKEND_ENV_FILE=$BackendEnvPath"
) -join ","

Write-Host "IMAGE = $Image"
Write-Host "CACHE = $CacheImage"
Write-Host "SUBS  = $Substitutions"

gcloud beta builds submit `
    --project $ProjectId `
    --region $Region `
    --config cloudbuild.yaml `
    --substitutions "$Substitutions"

if ($LASTEXITCODE -ne 0) {
    Write-Error "❌ Cloud Build failed"
    exit 1
}
