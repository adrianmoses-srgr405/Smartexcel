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

echo.
echo ==============================================================
echo   SUKSES! Kedua server sedang berjalan di jendela terpisah.
echo   Silakan buka browser di: http://localhost:5173
echo   (JANGAN tutup jendela hitam yang baru muncul agar server tetap hidup)
echo ==============================================================
echo.
pause
