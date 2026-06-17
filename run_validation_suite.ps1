# run_validation_suite.ps1
Write-Host "🚀 Starting MEOS V0.3 Multi-Seed Long-Run Validation Suite" -ForegroundColor Cyan
Write-Host "=============================================================" -ForegroundColor Cyan
Write-Host ""

$seeds = @(42, 1337, 9001, 12345, 8675309)
$results = @()

foreach ($seed in $seeds) {
    Write-Host "🧬 Initiating Scale Run: Seed $seed | 50 Generations | Target 0.89" -ForegroundColor Green
    Write-Host "-------------------------------------------------------------"
    
    # Kill stale processes
    Stop-Process -Name python -Force -ErrorAction SilentlyContinue
    
    # Run with unbuffered output
    python -u meos_v0.3.py --seed $seed --generations 50 --threshold 0.89
    
    # Capture best fitness from output
    # We'll parse this from the database later
    Write-Host ""
    Write-Host "✅ Seed $seed complete" -ForegroundColor Green
    Write-Host ""
}

Write-Host "=============================================================" -ForegroundColor Cyan
Write-Host "✅ All validation runs complete!" -ForegroundColor Cyan
Write-Host ""

# Run analytics
python src/analytics/analyze_evolution.py

Write-Host ""
Write-Host "📊 Results saved in: data/meos_v0.3.db" -ForegroundColor Yellow
