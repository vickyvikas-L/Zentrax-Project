@echo off
echo ================================================
echo    ZENTRAX APPLICATION BUILDER
echo ================================================
echo.

REM Activate virtual environment if exists
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)

REM Install PyInstaller
echo Installing PyInstaller...
pip install pyinstaller

echo.
echo Building Zentrax Application...
echo This may take several minutes...
echo.

REM Build using spec file for better control
pyinstaller zentrax.spec --clean

echo.
echo ================================================
if exist "dist\Zentrax\Zentrax.exe" (
    echo BUILD SUCCESSFUL!
    echo.
    echo Your application is ready at:
    echo   dist\Zentrax\Zentrax.exe
    echo.
    echo To run: Double-click Zentrax.exe
    echo ================================================
    
    REM Ask to run the app
    set /p run="Do you want to run Zentrax now? (y/n): "
    if /i "%run%"=="y" (
        start "" "dist\Zentrax\Zentrax.exe"
    )
) else (
    echo BUILD FAILED!
    echo Check the error messages above.
    echo ================================================
)

pause
