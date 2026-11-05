
$ProjectPath = "F:\AI\SOLUSDT_SIGNAL_BOT"
$OutputFile = Join-Path $ProjectPath "strategy_b_extra_review.txt"

$Files = @(
    "strategies\ema_triple_crossover.py",
    "paper_trading\forward_engine_b.py"
)

$Report = @()

foreach ($File in $Files) {

    $FullPath = Join-Path $ProjectPath $File

    $Report += ""
    $Report += "====================================================="
    $Report += "FILE: $File"
    $Report += "====================================================="

    if (Test-Path $FullPath) {
        $Report += Get-Content $FullPath -Raw
        Write-Host "[OK] $File" -ForegroundColor Green
    }
    else {
        $Report += "FILE NOT FOUND"
        Write-Host "[MISSING] $File" -ForegroundColor Red
    }
}

$Report | Out-File $OutputFile -Encoding utf8

Write-Host "Export completed: $OutputFile" -ForegroundColor Green
