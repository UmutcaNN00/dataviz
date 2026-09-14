@echo off
chcp 65001 >nul
title DataViz Pro - Demo Sunucusu
echo.
echo  ========================================================
echo     DataViz Pro  -  Demo Surumu
echo     Akademik Istatistik ve Veri Analizi
echo  ========================================================
echo.
echo  [1/2] Sunucu baslatiliyor...
start /B uv run python app.py > sunucu.log 2>&1
echo  [2/2] Tarayici aciliyor...
timeout /t 3 /nobreak >nul
start http://127.0.0.1:5000
echo.
echo  Demo aktif!  ->  http://127.0.0.1:5000
echo.
echo  Bu pencereyi KAPATMAYIN - kapatirsan sunucu durur.
echo.
pause
