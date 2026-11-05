
$ProjectPath = "F:\AI\SOLUSDT_SIGNAL_BOT"

$OutputFile = Join-Path $ProjectPath "overnight_diagnostic.txt"

$Files = @(
    "run_forward_b.py",
    "paper_trading\forward_engine_b.py",
    "strategies\strategy_b.py",
    "strategies\trend_filter.py"
)

$Report = @()

$Report += "SOLUSDT OVERNIGHT DIAGNOSTIC"
$Report += "Generated: $(Get-Date)"

foreach ($File in $Files) {

    $FullPath = Join-Path $ProjectPath $File

    $Report += ""
    $Report += "========================================"
    $Report += "FILE: $File"
    $Report += "========================================"

    if (Test-Path $FullPath) {
        $Report += Get-Content $FullPath -Raw
    }
    else {
        $Report += "FILE NOT FOUND"
    }
}

$Report | Out-File $OutputFile -Encoding utf8

Write-Host "Created: $OutputFile" -ForegroundColor Green
