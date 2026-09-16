[CmdletBinding()]
param(
    [string]$PythonExecutable = "python",
    [string]$EnvFile = ""
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$buildVenv = Join-Path $projectRoot ".build-venv"
$buildPython = Join-Path $buildVenv "Scripts\python.exe"
$distRoot = Join-Path $projectRoot "dist\label_printing"
$internalRoot = Join-Path $distRoot "_internal"
$installerScript = Join-Path $projectRoot "installer\label_printing.iss"
$installerSource = Get-Content -LiteralPath $installerScript -Raw
$versionMatch = [regex]::Match(
    $installerSource,
    '#define MyAppVersion "([^"]+)"'
)
if (-not $versionMatch.Success) {
    throw "Could not read MyAppVersion from the installer script."
}
$appVersion = $versionMatch.Groups[1].Value
$releaseBaseName = "label_printing_$($appVersion)_setup"

Push-Location $projectRoot
try {
    if (-not (Test-Path -LiteralPath $buildPython -PathType Leaf)) {
        & $PythonExecutable -m venv $buildVenv
        if ($LASTEXITCODE -ne 0) {
            throw "Could not create the build virtual environment."
        }
    }

    & $buildPython -m pip install --disable-pip-version-check --upgrade `
        pyinstaller environs yadisk requests pywin32
    if ($LASTEXITCODE -ne 0) {
        throw "Could not install build dependencies."
    }

    & $buildPython -m PyInstaller `
        --noconfirm `
        --clean `
        --windowed `
        --name label_printing `
        --icon (Join-Path $projectRoot "ico.ico") `
        --contents-directory "_internal" `
        --add-data "$(Join-Path $projectRoot 'articles_dict.json');." `
        --add-data "$(Join-Path $projectRoot 'template.btw');." `
        (Join-Path $projectRoot "label_printing.py")
    if ($LASTEXITCODE -ne 0) {
        throw "PyInstaller could not build the application."
    }

    Copy-Item -LiteralPath (Join-Path $projectRoot "ico.ico") `
        -Destination (Join-Path $distRoot "ico.ico") -Force
    Copy-Item -LiteralPath (Join-Path $projectRoot "articles_dict.json") `
        -Destination (Join-Path $distRoot "articles_dict.json") -Force
    New-Item -ItemType Directory -Path (Join-Path $internalRoot "stickers") `
        -Force | Out-Null

    if (-not $EnvFile) {
        $envCandidates = @(
            Get-ChildItem -LiteralPath (Join-Path $projectRoot "programma") `
                -File -Filter ".env*" -ErrorAction SilentlyContinue
        )
        if ($envCandidates.Count -ne 1) {
            throw "Specify the .env path with the -EnvFile parameter."
        }
        $EnvFile = $envCandidates[0].FullName
    }
    if (-not (Test-Path -LiteralPath $EnvFile -PathType Leaf)) {
        throw "The .env file for the build was not found."
    }
    Copy-Item -LiteralPath $EnvFile `
        -Destination (Join-Path $internalRoot ".env") -Force

    $innoCandidates = @(
        (Join-Path $env:LOCALAPPDATA "Programs\Inno Setup 6\ISCC.exe"),
        "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        "C:\Program Files\Inno Setup 6\ISCC.exe"
    )
    $innoCompiler = $innoCandidates |
        Where-Object { Test-Path -LiteralPath $_ -PathType Leaf } |
        Select-Object -First 1
    if (-not $innoCompiler) {
        throw "Inno Setup 6 is not installed. Install JRSoftware.InnoSetup."
    }

    $installerBuilt = $false
    for ($attempt = 1; $attempt -le 3; $attempt++) {
        & $innoCompiler $installerScript
        if ($LASTEXITCODE -eq 0) {
            $installerBuilt = $true
            break
        }
        if ($attempt -lt 3) {
            Start-Sleep -Seconds 2
        }
    }
    if (-not $installerBuilt) {
        throw "Could not build the installer."
    }

    $setupFile = Join-Path $projectRoot "release\$releaseBaseName.exe"
    $zipFile = Join-Path $projectRoot "release\$releaseBaseName.zip"
    for ($attempt = 1; $attempt -le 5; $attempt++) {
        try {
            Compress-Archive -LiteralPath $setupFile `
                -DestinationPath $zipFile -Force
            break
        }
        catch {
            if ($attempt -eq 5) {
                throw
            }
            Start-Sleep -Seconds 1
        }
    }

    Write-Host "Ready: $setupFile"
    Write-Host "ZIP: $zipFile"
}
finally {
    Pop-Location
}
