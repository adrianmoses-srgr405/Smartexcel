@echo off
title SmartExcel PTPN Launcher
echo ==============================================================
echo   MENJALANKAN SISTEM SMART EXCEL PTPN IV (BACKEND & FRONTEND)
echo ==============================================================
echo.

echo [1/2] Menjalankan Server Backend (FastAPI Port 8000)...
start "SmartExcel Backend API (Port 8000)" cmd /k "cd /d %~dp0backend && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"

timeout /t 2 /nobreak >nul

echo [2/2] Menjalankan Server Frontend (React Port 5173)...
start "SmartExcel Frontend UI (Port 5173)" cmd /k "cd /d %~dp0frontend && npm run dev"

timeout /t 3 /nobreak >nul

echo [3/3] Membuka browser otomatis ke http://localhost:5173...
start http://localhost:5173

echo.
echo ==============================================================
echo   SUKSES! Server berjalan dan browser telah dibuka otomatis.
echo   URL Aplikasi: http://localhost:5173
echo   (JANGAN tutup jendela command prompt agar server tetap hidup)
echo ==============================================================
echo.
pause
