# build.ps1 — produce a one-folder distributable in dist/ProjectSaruman/
# Usage: .\build.ps1
# Requires: uv on PATH (run from project root)

$ErrorActionPreference = "Stop"
$env:PATH = "C:\Users\develogics\.local\bin;$env:PATH"

Write-Host "==> Installing PyInstaller..."
uv add --dev pyinstaller | Out-Null

Write-Host "==> Building ProjectSaruman..."
uv run pyinstaller `
    --onedir `
    --name "ProjectSaruman" `
    --add-data "assets;assets" `
    --hidden-import pytmx `
    --hidden-import pytmx.util_pygame `
    --noconsole `
    --clean `
    saruman/__main__.py

Write-Host ""
Write-Host "==> Done. Distributable folder: dist\ProjectSaruman\"
Write-Host "    Run: dist\ProjectSaruman\ProjectSaruman.exe"
