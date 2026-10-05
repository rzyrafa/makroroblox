@echo off
chcp 65001 >nul
title Roblox Market Sniper

:wybor
cls
echo ======================================================
echo           ROBLOX MARKET SNIPER MACRO
echo ======================================================
echo.
echo   [1] Uruchom Panel Graficzny (Menedzer GUI)
echo   [2] Uruchom Makro bezposrednio (Konsola)
echo   [3] Wyjdz
echo.
echo ======================================================
choice /C 123 /M "Wybierz opcje"
if errorlevel 3 goto koniec
if errorlevel 2 goto tryb_konsolowy
if errorlevel 1 goto tryb_gui

:tryb_gui
cls
echo Uruchamianie panelu GUI...
start "" ".\venv\Scripts\pythonw.exe" gui.py
goto koniec

:tryb_konsolowy
:menu
cls
echo ======================================================
echo           ROBLOX MARKET SNIPER MACRO
echo ======================================================
echo Uruchamianie bota...
call .\venv\Scripts\python.exe makro.py
echo.
echo ======================================================
echo Makro zostalo zatrzymane (Kill Switch / exit).
echo ======================================================
choice /C TN /M "Czy chcesz wznowic makro? [T=Tak, N=Nie]"
if errorlevel 2 goto koniec
if errorlevel 1 goto menu

:koniec
echo.
echo Zamykanie...
timeout /t 2 >nul
