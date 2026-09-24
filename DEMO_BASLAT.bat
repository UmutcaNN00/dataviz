@echo off
chcp 65001 >nul
title DataViz - Büyük Veri ve Analitik Platformu
echo.
echo  ========================================================
echo     DataViz - Büyük Veri ve Analitik Platformu
echo     Polars Engine ^& Akademik İstatistik
echo  ========================================================
echo.
echo  [1/2] Sunucu başlatılıyor (Polars ^& Flask)...
if exist ".venv\Scripts\python.exe" (
    start /B .venv\Scripts\python.exe app.py > sunucu.log 2>&1
) else (
    start /B uv run python app.py > sunucu.log 2>&1
)
echo  [2/2] Tarayıcı açılıyor...
timeout /t 3 /nobreak >nul
start http://127.0.0.1:5000
echo.
echo  Platform aktif!  -^>  http://127.0.0.1:5000
echo.
echo  Bu pencereyi KAPATMAYIN
echo.
pause
