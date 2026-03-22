@echo off
title ntsCuda - Bagimliliklari Kur
echo ============================================
echo        ntsCuda - Bagimlillik Kurulumu
echo ============================================
echo.

:: Python kontrolu
python --version >nul 2>&1
if errorlevel 1 (
    echo [HATA] Python bulunamadi! Lutfen Python 3.8+ kurun.
    echo https://www.python.org/downloads/
    pause
    exit /b 1
)

:: Sanal ortam olustur
if not exist "venv" (
    echo [1/3] Sanal ortam olusturuluyor...
    python -m venv venv
) else (
    echo [1/3] Sanal ortam zaten mevcut, atlanıyor...
)

:: Sanal ortami etkinlestir
call venv\Scripts\activate.bat

:: Temel bagimliliklari kur
echo [2/3] Temel bagimliliklar kuruluyor...
pip install --upgrade pip
pip install -r requirements.txt

:: CUDA secimi
echo.
echo ============================================
echo         CUDA / GPU Hizlandirma
echo ============================================
echo.
echo CUDA surumunuzu secin (GPU hizlandirma icin):
echo   1) CUDA 12.x
echo   2) CUDA 11.x
echo   3) CUDA 10.2
echo   4) CUDA kurma (sadece CPU)
echo.
set /p cuda_choice="Seciminiz (1-4): "

if "%cuda_choice%"=="1" (
    echo [3/3] CuPy CUDA 12.x kuruluyor...
    pip install cupy-cuda12x
) else if "%cuda_choice%"=="2" (
    echo [3/3] CuPy CUDA 11.x kuruluyor...
    pip install cupy-cuda11x
) else if "%cuda_choice%"=="3" (
    echo [3/3] CuPy CUDA 10.2 kuruluyor...
    pip install cupy-cuda102
) else (
    echo [3/3] CUDA kurulumu atlandi. CPU modu kullanilacak.
)

echo.
echo ============================================
echo   Kurulum tamamlandi!
echo   Uygulamayi baslatmak icin: start.bat
echo ============================================
pause
