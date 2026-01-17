# =========================
# Usage
#   .\deploy-local.ps1 -EnvName dev
#   .\deploy-local.ps1 -EnvName prod
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

$Image = "$Region-docker.pkg.dev/${ProjectId}/${Repository}/${ImageName}:latest"

$ProxyArgs = @()

if ($Env:HTTP_PROXY) {
    $ProxyArgs += @("--build-arg", "HTTP_PROXY=$Env:HTTP_PROXY")
}

if ($Env:HTTPS_PROXY) {
    $ProxyArgs += @("--build-arg", "HTTPS_PROXY=$Env:HTTPS_PROXY")
}

if ($Env:NO_PROXY) {
    $ProxyArgs += @("--build-arg", "NO_PROXY=$Env:NO_PROXY")
}

$BackendEnvPath = "$PSScriptRoot/backend/.env.$EnvName"
if (!(Test-Path $BackendEnvPath)) {
    $BackendEnvPath = "$PSScriptRoot/backend/.env"
}
Write-Host "Backend env file: $BackendEnvPath"

# Write-Host "Project : $ProjectId"
# Write-Host "Image   : $Image"
# Write-Host "Service : $ServiceName"

# Write-Host "`nBuild image..."
# wsl docker build -t $Image @ProxyArgs .
# if ($LASTEXITCODE -ne 0) { exit 1 }

# Write-Host "`nPush image..."
# wsl docker push $Image
# if ($LASTEXITCODE -ne 0) { exit 1 }

# Write-Host "`nDeploy to Cloud Run..."
gcloud run deploy $ServiceName `
    --project $ProjectId `
    --region $Region `
    --image $Image `
    --platform managed `
    --allow-unauthenticated `
    --env-vars-file $BackendEnvPath

Write-Host "`nDeployment completed successfully."