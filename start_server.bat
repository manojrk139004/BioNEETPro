@echo off
title BioNEET Pro Backend Server
echo ========================================================
echo   Starting BioNEET Pro AI Tutor Backend...
echo ========================================================
echo.
echo   Opening app at http://127.0.0.1:5000 in your browser...
start "" http://127.0.0.1:5000
echo.
echo   KEEP THIS WINDOW OPEN while using BioNEET Pro!
echo   (Closing this window or pressing Ctrl+C stops the server)
echo ========================================================
echo.
python app.py
pause
