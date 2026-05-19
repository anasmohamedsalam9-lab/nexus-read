# Non-interactive Powershell Script to Run One Piece Chapter 2 Translation Engine
$ErrorActionPreference = "SilentlyContinue"

Write-Host "=================================================="
Write-Host "      NEXUS - ONE PIECE TRANSLATION RUNNER       "
Write-Host "=================================================="
Write-Host ""

# 1. Search for Python Interpreter
Write-Host "Searching for Python interpreter..."
$pythonExe = ""

$searchPaths = @(
    "A:\New folder\python.exe",
    "C:\Users\DELL\AppData\Local\Programs\Python\Python314\Scripts\python.exe",
    "C:\Users\DELL\AppData\Local\Programs\Python\Python314\python.exe",
    "C:\Users\DELL\AppData\Local\Programs\Python\Python314\Scripts\run.exe",
    "C:\Users\DELL\AppData\Local\Programs\Python\Python310\python.exe",
    "C:\Users\DELL\AppData\Local\Programs\Python\Python311\python.exe",
    "C:\Users\DELL\AppData\Local\Programs\Python\Python312\python.exe",
    "C:\Users\DELL\AppData\Local\Programs\Python\Python39\python.exe",
    "C:\Users\DELL\AppData\Local\Programs\Python\Python38\python.exe",
    "C:\Users\DELL\AppData\Local\Programs\Python\Launcher\py.exe"
)

foreach ($path in $searchPaths) {
    if (Test-Path $path) {
        $pythonExe = $path
        break
    }
}

if ($pythonExe -eq "") {
    $cmdPath = Get-Command python -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source
    if ($cmdPath -ne $null -and $cmdPath -ne "") {
        $pythonExe = $cmdPath
    }
}

if ($pythonExe -eq "") {
    Write-Host "Python executable not found in common directories. Defaulting to 'python'..."
    $pythonExe = "python"
} else {
    Write-Host "Found Python: $pythonExe"
}

# 2. Run Translation
Write-Host ""
Write-Host "Starting automated MangaDex scrape and translation..."
$env:PYTHONPATH = "A:\nexus"
& $pythonExe "A:\nexus\bot\translate_one_piece_ch2.py"

# 3. Post-run Database Repair
Write-Host ""
Write-Host "Healing database syntax formatting..."
if (Test-Path "A:\nexus\bot\fix_data_js_format.ps1") {
    & "A:\nexus\bot\fix_data_js_format.ps1"
}

Write-Host ""
Write-Host "=================================================="
Write-Host "Process completed successfully!"
Write-Host "=================================================="
