Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Starting Multimodal LLMOps System" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

Write-Host "`nStarting Backend (FastAPI)..." -ForegroundColor Green
Start-Process cmd -ArgumentList "/c uv run python -m backend.src.api.server" -WorkingDirectory $PWD

Write-Host "`nStarting Frontend (Vite/React)..." -ForegroundColor Green
Start-Process cmd -ArgumentList "/c npm run dev" -WorkingDirectory "$PWD\frontend"

Write-Host "`nBoth servers have been started in new windows!" -ForegroundColor Yellow
Write-Host "Close the command prompt windows to stop the servers.`n" -ForegroundColor Yellow
