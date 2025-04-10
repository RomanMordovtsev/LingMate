@echo off
chcp 65001 >nul
title Language Mentor Server

:: Автоматический запуск от админа
fltmc >nul 2>&1 || (
    echo Запускаем от имени администратора...
    powershell Start-Process -FilePath "%~dpnx0" -Verb RunAs
    exit /b
)

:: Основной код
set "PROJECT_DIR=%~dp0"
cd /d "%PROJECT_DIR%"

echo [✓] Проект: %PROJECT_DIR%
echo [✓] Python: %python.version%

:: Запуск с обработкой Ctrl+C
python -c "from main import app; import uvicorn; uvicorn.run(app, host='0.0.0.0', port=8000, workers=1)"

pause