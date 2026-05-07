@echo off
echo Launching Production RAG System locally...
echo.
echo Opening backend terminal on port 8000...
start "RAG Backend" cmd /k "cd /d %~dp0backend && python -m uvicorn main:app --host 127.0.0.1 --port 8000"
timeout /t 2 /nobreak

echo Opening frontend terminal on port 3000...
start "RAG Frontend" cmd /k "cd /d %~dp0frontend\react-app && npm run dev"
timeout /t 2 /nobreak

echo.
echo Both services launched!
echo Frontend: http://127.0.0.1:3000
echo Backend:  http://127.0.0.1:8000
echo.
pause
