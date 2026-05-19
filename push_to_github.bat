@echo off
echo ==================================================
echo       Nexus - Pushing to GitHub
echo ==================================================
cd /d "A:\nexus"
git remote remove origin >nul 2>&1
git remote add origin https://github.com/anasmohamedsalam9-lab/nexus-read.git
git branch -M main
echo.
echo [1/2] Connecting to repository...
echo [2/2] Pushing code (A browser window may pop up for authentication)...
git push -u origin main
echo.
echo ==================================================
if %ERRORLEVEL% equ 0 (
    echo [SUCCESS] Code uploaded successfully!
) else (
    echo [ERROR] Upload failed. Please make sure you are logged in.
)
echo ==================================================
pause
