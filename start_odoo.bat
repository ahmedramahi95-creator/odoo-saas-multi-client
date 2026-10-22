@echo off
set PATH=C:\Users\pc\wkhtmltox\bin;%PATH%
cd /d "%~dp0"
if exist odoo-20.0 (
    cd odoo-20.0
)

echo Checking Docker and PostgreSQL container...
docker ps -q -f name=odoo-db | findstr . >nul
if %errorlevel% neq 0 (
    echo Starting odoo-db container...
    docker start odoo-db 2>nul || docker run -d --name odoo-db -p 5432:5432 -e POSTGRES_USER=odoo -e POSTGRES_PASSWORD=odoo -e POSTGRES_HOST_AUTH_METHOD=trust -v odoo_pgdata:/var/lib/postgresql/data postgres:16
)

echo Starting Odoo 20.0...
python odoo-bin -c odoo.conf
pause
