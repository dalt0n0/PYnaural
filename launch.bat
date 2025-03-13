@echo off
setlocal enabledelayedexpansion

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed! Please install Python 3.11 or later from https://www.python.org/downloads/
    pause
    exit /b 1
)

:: Check Python version
for /f "tokens=2 delims=." %%I in ('python -c "import sys; print(sys.version.split()[0])"') do set PYTHON_VERSION=%%I
if %PYTHON_VERSION% LSS 11 (
    echo Python version 3.11 or higher is required!
    echo Current version: %PYTHON_VERSION%
    pause
    exit /b 1
)

:: Check if virtual environment exists
if not exist env (
    echo Creating virtual environment...
    python -m venv env
    if errorlevel 1 (
        echo Failed to create virtual environment!
        pause
        exit /b 1
    )
)

:: Set the path to activate the virtual environment
set "VIRTUAL_ENV=%CD%\env"
set "PATH=%VIRTUAL_ENV%\Scripts;%PATH%"
call "%VIRTUAL_ENV%\Scripts\activate.bat"

:: Verify the environment is activated
where python | findstr /i "env" >nul 2>&1
if errorlevel 1 (
    echo Failed to activate virtual environment!
    pause
    exit /b 1
)

:: Check if requirements are installed
python -c "import pygame" >nul 2>&1
if errorlevel 1 (
    echo Installing dependencies...
    pip install -r requirements.txt
    pip install pygame>=2.5.0
    if errorlevel 1 (
        echo Failed to install dependencies!
        pause
        exit /b 1
    )
)

:: Launch the Python script
echo Launching PYnaural...
python binaural_app.py
if errorlevel 1 (
    echo Failed to run the application!
    pause
    exit /b 1
)

:: Keep the window open if there are any errors
if errorlevel 1 pause
exit /b 0 