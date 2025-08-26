@echo off
REM IPSAS Financial Software - Windows Setup Script
REM This script automates the installation and configuration on Windows

echo.
echo =============================================
echo   IPSAS Financial Software - Windows Setup
echo =============================================
echo.

REM Check if running as administrator
net session >nul 2>&1
if %errorLevel% == 0 (
    echo Running as administrator - this is not recommended for development
    echo Please run this script as a regular user
    pause
    exit /b 1
)

echo Checking system requirements...

REM Check if Python is installed
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo Python is not installed. Please install Python 3.8+ from https://python.org
    echo After installation, restart this script
    pause
    exit /b 1
) else (
    echo ✓ Python is installed
)

REM Check if Node.js is installed
node --version >nul 2>&1
if %errorLevel% neq 0 (
    echo Node.js is not installed. Please install Node.js 16+ from https://nodejs.org
    echo After installation, restart this script
    pause
    exit /b 1
) else (
    echo ✓ Node.js is installed
)

REM Check if Git is installed
git --version >nul 2>&1
if %errorLevel% neq 0 (
    echo Git is not installed. Please install Git from https://git-scm.com
    echo After installation, restart this script
    pause
    exit /b 1
) else (
    echo ✓ Git is installed
)

echo.
echo Installing Python dependencies...
cd backend
python -m venv venv
call venv\Scripts\activate.bat
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn psycopg2-binary
cd ..

echo.
echo Installing Node.js dependencies...
cd frontend
npm install
npm install -g serve
cd ..

echo.
echo Setting up environment configuration...
if not exist "backend\.env" (
    copy "backend\env.example" "backend\.env"
    echo Environment file created. Please edit backend\.env with your database settings.
)

echo.
echo Creating startup scripts...

REM Backend startup script
echo @echo off > start_backend.bat
echo cd /d "%%~dp0backend" >> start_backend.bat
echo call venv\Scripts\activate.bat >> start_backend.bat
echo python manage.py runserver 0.0.0.0:8000 >> start_backend.bat
echo pause >> start_backend.bat

REM Frontend startup script
echo @echo off > start_frontend.bat
echo cd /d "%%~dp0frontend" >> start_frontend.bat
echo npm start >> start_frontend.bat
echo pause >> start_frontend.bat

REM Celery worker startup script
echo @echo off > start_celery.bat
echo cd /d "%%~dp0backend" >> start_celery.bat
echo call venv\Scripts\activate.bat >> start_celery.bat
echo celery -A ipsas_financial worker --loglevel=info >> start_celery.bat
echo pause >> start_celery.bat

REM Celery beat startup script
echo @echo off > start_celery_beat.bat
echo cd /d "%%~dp0backend" >> start_celery_beat.bat
echo call venv\Scripts\activate.bat >> start_celery_beat.bat
echo celery -A ipsas_financial beat --loglevel=info >> start_celery_beat.bat
echo pause >> start_celery_beat.bat

echo.
echo =============================================
echo   Setup Completed Successfully!
echo =============================================
echo.
echo Next steps:
echo 1. Install and configure PostgreSQL database
echo 2. Install and configure Redis (optional, for Celery)
echo 3. Edit backend\.env with your database settings
echo 4. Run Django migrations: cd backend ^&^& venv\Scripts\activate.bat ^&^& python manage.py migrate
echo 5. Create superuser: python manage.py createsuperuser
echo 6. Start the application using the created batch files
echo.
echo For detailed instructions, see docs/deployment.md
echo.
pause
