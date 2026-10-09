@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

echo.
echo ========================================================================
echo   DataViz - Buyuk Veri, AI Guven Skoru ve Istatistik Platformu
echo   TUBITAK 2209-A Destekli Yerel Veri Analiz Studyosu
echo ========================================================================
echo.

:: 1. Python Tespiti
set "PY_CMD="

python -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1
if %errorlevel% equ 0 (
    set "PY_CMD=python"
    goto :python_bulundu
)

py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1
if %errorlevel% equ 0 (
    set "PY_CMD=py -3"
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
            set "PY_CMD=%%D\python.exe"
            goto :python_bulundu
        )
    )
)

for /d %%D in ("%ProgramFiles%\Python3*") do (
    if exist "%%D\python.exe" (
        "%%D\python.exe" -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1
        if %errorlevel% equ 0 (
            set "PY_CMD=%%D\python.exe"
            goto :python_bulundu
        )
    )
)

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
        echo   [OK] Kurulum komutu tamamlandi.
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
echo [OK] Python bulundu.

:: 2. Sanal Ortam Kontrolu
if not exist ".venv\Scripts\python.exe" goto :venv_olustur

.\.venv\Scripts\python.exe -c "import sys" >nul 2>&1
if %errorlevel% equ 0 goto :venv_hazir

echo [BILGI] Eski veya gecersiz sanal ortam tespit edildi, sifirlaniyor...
rmdir /s /q ".venv" >nul 2>&1

:venv_olustur
echo [1/3] Python sanal ortami hazirlaniyor...
%PY_CMD% -m venv .venv
if errorlevel 1 (
    echo [HATA] Sanal ortam olusturulamadi!
    pause
    exit /b 1
)
echo [OK] Sanal ortam hazirlandi.

:venv_hazir

:: 3. Kutuphanelerin Kontrolu
.\.venv\Scripts\python.exe -c "import flask, flask_cors, pandas, numpy, openpyxl, scipy, polars, pyarrow, sklearn, sqlalchemy" >nul 2>&1
if %errorlevel% equ 0 goto :kutuphaneler_tamam

echo [2/3] Gerekli kutuphaneler yukleniyor - requirements.txt...
echo Bu islem sadece ilk calistirmada bir defa yapilir, lutfen bekleyin...
echo.
.\.venv\Scripts\python.exe -m pip install --disable-pip-version-check -r requirements.txt
if errorlevel 1 (
    echo.
    echo [HATA] Kutuphaneler yuklenirken hata olustu.
    pause
    exit /b 1
)
echo [OK] Kutuphaneler basariyla kuruldu.

:kutuphaneler_tamam
echo [OK] Kutuphaneler hazir.

if not exist "uploads" mkdir "uploads"

:: 4. Uygulamayi Baslat
set "PORT=5000"
if exist ".env" (
    for /f "tokens=1,2 delims==" %%a in (.env) do (
        if "%%a"=="PORT" set "PORT=%%b"
    )
)

echo.
echo ========================================================================
echo   [3/3] DataViz Analiz Platformu Baslatiliyor...
echo.
echo   Adres     : http://127.0.0.1:%PORT%
echo   Durdurmak : Bu pencereyi kapatin veya Ctrl + C tuslarina basin
echo ========================================================================
echo.

start "" powershell -NoProfile -WindowStyle Hidden -Command "Start-Sleep -Seconds 2; Start-Process 'http://127.0.0.1:%PORT%'"

.\.venv\Scripts\python.exe app.py

echo.
echo [BILGI] Uygulama sonlandi.
pause