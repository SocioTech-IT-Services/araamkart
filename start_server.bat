@echo off
cd /d "%~dp0"
echo.
echo  AaramKart — http://127.0.0.1:8000
echo  Leave this window open. Press Ctrl+C to stop the server.
echo.
python manage.py runserver 0.0.0.0:8000
pause
