@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

:: Windows UTF-8 zorunlulugu (Turkce karakter ve cp1254 cokuslerini engeller)
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"

echo.
echo ========================================================================
echo   DataViz - Buyuk Veri, AI Guven Skoru ve Istatistik Platformu
echo   TUBITAK 2209-A Destekli Yerel Veri Analiz Studyosu
echo ========================================================================
echo.

:: 1. Python Tespiti (En guvenli sirada: py -3, python, dogrudan dizinler)
set "PY_CMD="

py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1
if %errorlevel% equ 0 (
    set "PY_CMD=py -3"
    goto :python_bulundu
)

python -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1
if %errorlevel% equ 0 (
    set "PY_CMD=python"
    goto :python_bulundu
)

py -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1
if %errorlevel% equ 0 (
    set "PY_CMD=py"
    goto :python_bulundu
)

for /d %%D in ("%LOCALAPPDATA%\Programs\Python\Python3*") do (
    if exist "%%D\python.exe" (
        "%%D\python.exe" -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1
        if %errorlevel% equ 0 (
            set PY_CMD="%%D\python.exe"
            goto :python_bulundu
        )
    )
)

for /d %%D in ("%ProgramFiles%\Python3*") do (
    if exist "%%D\python.exe" (
        "%%D\python.exe" -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1
        if %errorlevel% equ 0 (
            set PY_CMD="%%D\python.exe"
            goto :python_bulundu
        )
    )
)

for /d %%D in ("%ProgramFiles(x86)%\Python3*") do (
    if exist "%%D\python.exe" (
        "%%D\python.exe" -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1
        if %errorlevel% equ 0 (
            set PY_CMD="%%D\python.exe"
            goto :python_bulundu
        )
    )
)

:: Python Bulunamadi - Otomatik winget Cozumu veya Manuel Yonlendirme
echo ========================================================================
echo   [!] BILGI: Bilgisayarinizda Python 3.10 veya daha yeni bulunamadi.
echo ========================================================================
echo.
echo   DataViz platformunun calisabilmesi icin Python 3.10+ gereklidir.
echo.
where winget >nul 2>&1
if %errorlevel% equ 0 (
    echo   Windows Paket Yoneticisi (winget) tespit edildi!
    echo   Python 3.11 otomatik olarak kurulabilir.
    echo.
    set /p "KUR_PYTHON=Python 3.11 otomatik kurulsun mu? (E/H): "
    if /i "%KUR_PYTHON%"=="E" (
        echo.
        echo   Python 3.11 kuruluyor, lutfen acilan pencereleri onaylayin...
        winget install -e --id Python.Python.3.11 --accept-package-agreements --accept-source-agreements
        echo.
        echo   [OK] Kurulum tamamlandi.
        echo   Yeni ortam degiskenlerinin taninmasi icin lutfen Baslat.bat dosyasini tekrar calistirin.
        pause
        exit /b 0
    )
)
echo.
echo   Manuel Kurulum Icin:
echo   1. https://www.python.org/downloads/ adresinden Python indirin.
echo   2. Kurulum ekraninda: "Add python.exe to PATH" secenegini ISARETLEYIN!
echo   3. Kurulum bitince bu Baslat.bat dosyasini tekrar calistirin.
echo.
echo ========================================================================
pause
exit /b 1

:python_bulundu
echo [OK] Python bulundu: %PY_CMD%

:: 2. Sanal Ortam Kontrolu (.venv)
set "VENV_DIR=%~dp0.venv"
set "VENV_PY=%VENV_DIR%\Scripts\python.exe"

if not exist "%VENV_PY%" goto :venv_olustur

"%VENV_PY%" -c "import sys" >nul 2>&1
if %errorlevel% equ 0 goto :venv_hazir

echo [BILGI] Eski veya gecersiz sanal ortam tespit edildi, sifirlaniyor...
rmdir /s /q "%VENV_DIR%" >nul 2>&1
if exist "%VENV_DIR%" (
    echo [HATA] .venv klasoru baska bir program tarafindan kilitli.
    echo Lutfen calisan Python sureclerini kapatip tekrar deneyin.
    pause
    exit /b 1
)

:venv_olustur
echo [1/3] Python sanal ortami hazirlaniyor (.venv)...
%PY_CMD% -m venv "%VENV_DIR%"
if errorlevel 1 (
    echo [HATA] Sanal ortam olusturulamadi!
    pause
    exit /b 1
)
echo [OK] Sanal ortam hazirlandi.

:venv_hazir

:: 3. Kutuphanelerin Kontrolu
echo [2/3] Kutuphaneler kontrol ediliyor...
"%VENV_PY%" -c "import flask, flask_cors, pandas, numpy, openpyxl, scipy, polars, pyarrow, sklearn, sqlalchemy, reportlab" >nul 2>&1
if %errorlevel% equ 0 goto :kutuphaneler_tamam

echo Gerekli kutuphaneler yukleniyor - requirements.txt...
echo Bu islem sadece ilk calistirmada bir defa yapilir, lutfen bekleyin...
echo.
"%VENV_PY%" -m pip install --disable-pip-version-check --prefer-binary -r requirements.txt
if errorlevel 1 (
    echo.
    echo [HATA] Kutuphaneler yuklenirken hata olustu.
    echo Lutfen internet baglantinizi kontrol edin.
    pause
    exit /b 1
)
echo [OK] Kutuphaneler basariyla kuruldu.

:kutuphaneler_tamam
echo [OK] Kutuphaneler eksiksiz ve hazir.

if not exist "uploads" mkdir "uploads"

:: 4. Port Tespiti ve Port Cakismasi Korumasi
set "PORT=5000"
if exist ".env" (
    for /f "tokens=1,2 delims==" %%a in (.env) do (
        if "%%a"=="PORT" set "PORT=%%b"
    )
)

netstat -ano 2>nul | findstr /R /C:":%PORT% .*LISTENING" >nul 2>&1
if %errorlevel% equ 0 (
    echo [BILGI] Port %PORT% su anda kullanimda, alternatif port 5001 deneniyor...
    set "PORT=5001"
    netstat -ano 2>nul | findstr /R /C:":5001 .*LISTENING" >nul 2>&1
    if %errorlevel% equ 0 (
        echo [BILGI] Port 5001 de mesgul, 5050 portuna geciliyor.
        set "PORT=5050"
    )
)

:: 5. Uygulamayi Baslat
echo.
echo ========================================================================
echo   [3/3] DataViz Analiz Platformu Baslatiliyor...
echo.
echo   Adres     : http://127.0.0.1:%PORT%
echo   Durdurmak : Bu pencereyi kapatin veya Ctrl + C tuslarina basin
echo ========================================================================
echo.

start "" powershell -NoProfile -WindowStyle Hidden -Command "Start-Sleep -Seconds 2; Start-Process 'http://127.0.0.1:%PORT%'"

"%VENV_PY%" app.py

echo.
echo ========================================================================
echo   [BILGI] Uygulama sonlandi.
echo ========================================================================
pause