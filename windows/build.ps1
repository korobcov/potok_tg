#Requires -Version 5.1
<#
.SYNOPSIS
    Собирает нативный Windows-билд бота: один .exe + ffmpeg.exe + .env.example
    в папке dist/PotokBot/. Ничего кроме этой папки конечному пользователю
    не нужно - ни Python, ни ffmpeg отдельно ставить не надо.

.USAGE
    Запустите из корня репозитория:
        powershell -ExecutionPolicy Bypass -File windows\build.ps1
#>

$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $RepoRoot

$DistDir = Join-Path $RepoRoot "dist\PotokBot"
$FfmpegUrl = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"

Write-Host "==> Проверка Python..." -ForegroundColor Cyan
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    throw "Python не найден в PATH. Установите Python 3.11+ с python.org и добавьте его в PATH."
}
python --version

Write-Host "==> Создание виртуального окружения для сборки (.venv-build)..." -ForegroundColor Cyan
if (-not (Test-Path ".venv-build")) {
    python -m venv .venv-build
}
$venvPython = Join-Path $RepoRoot ".venv-build\Scripts\python.exe"

Write-Host "==> Установка зависимостей проекта и PyInstaller..." -ForegroundColor Cyan
& $venvPython -m pip install --upgrade pip | Out-Null
& $venvPython -m pip install -r requirements.txt pyinstaller

Write-Host "==> Сборка PotokBot.exe (PyInstaller)..." -ForegroundColor Cyan
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
& $venvPython -m PyInstaller --noconfirm windows\potok_tg.spec

New-Item -ItemType Directory -Force -Path $DistDir | Out-Null
Move-Item -Force (Join-Path $RepoRoot "dist\PotokBot.exe") (Join-Path $DistDir "PotokBot.exe")

Write-Host "==> Загрузка ffmpeg..." -ForegroundColor Cyan
$ffmpegExeTarget = Join-Path $DistDir "ffmpeg.exe"
if (Test-Path $ffmpegExeTarget) {
    Write-Host "ffmpeg.exe уже есть в dist, пропускаем загрузку."
} else {
    $zipPath = Join-Path $env:TEMP "ffmpeg-release-essentials.zip"
    Invoke-WebRequest -Uri $FfmpegUrl -OutFile $zipPath
    $extractDir = Join-Path $env:TEMP "ffmpeg-extract"
    if (Test-Path $extractDir) { Remove-Item -Recurse -Force $extractDir }
    Expand-Archive -Path $zipPath -DestinationPath $extractDir
    $ffmpegExe = Get-ChildItem -Path $extractDir -Recurse -Filter "ffmpeg.exe" | Select-Object -First 1
    if (-not $ffmpegExe) {
        throw "Не удалось найти ffmpeg.exe в скачанном архиве."
    }
    Copy-Item $ffmpegExe.FullName $ffmpegExeTarget
    Remove-Item -Force $zipPath
    Remove-Item -Recurse -Force $extractDir
}

Write-Host "==> Копирование .env.example и README..." -ForegroundColor Cyan
Copy-Item -Force (Join-Path $RepoRoot ".env.example") (Join-Path $DistDir ".env.example")
Copy-Item -Force (Join-Path $RepoRoot "windows\README-WINDOWS.txt") (Join-Path $DistDir "README.txt")

Write-Host ""
Write-Host "Готово! Папка с готовым ботом: $DistDir" -ForegroundColor Green
Write-Host "Скопируйте её пользователю целиком (или заархивируйте) - внутри всё, что нужно."
