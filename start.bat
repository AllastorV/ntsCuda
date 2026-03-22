@echo off
title ntsCuda
echo ============================================
echo            ntsCuda Baslatiliyor...
echo ============================================
echo.

:: Sanal ortam kontrolu
if not exist "venv\Scripts\activate.bat" (
    echo [HATA] Sanal ortam bulunamadi!
    echo Lutfen once install.bat dosyasini calistirin.
    pause
    exit /b 1
)

:: Sanal ortami etkinlestir
call venv\Scripts\activate.bat

:: CUDA durumu kontrol
echo GPU/CUDA durumu kontrol ediliyor...
python -c "import cupy; print('[CUDA] GPU hizlandirma AKTIF - ' + cupy.cuda.runtime.getDeviceProperties(0)['name'].decode())" 2>nul
if errorlevel 1 (
    echo [CPU] GPU hizlandirma devre disi - CPU modu kullanilacak.
)
echo.

:: Uygulamayi baslat ve CMD'yi arka plana al
echo Uygulama baslatiliyor...
start /min "" pythonw ntsCuda.py
exit
