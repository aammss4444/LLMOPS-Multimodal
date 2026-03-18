@echo off
echo =========================================
echo Starting Multimodal LLMOps System
echo =========================================

echo.
echo Starting Backend (FastAPI)...
start "Backend Server" cmd /k "uv run python -m backend.src.api.server"

echo.
echo Starting Frontend (Vite/React)...
cd frontend
start "Frontend Server" cmd /k "npm run dev"
cd ..

echo.
echo Both servers have been started in new windows!
echo Close the command prompt windows to stop the servers.
pause
