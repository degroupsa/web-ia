@echo off
TITLE LAUNCHER KORTEXA ENTERPRISE (Secure)
CLS

:: Rutas Absolutas
SET "RAIZ=%~dp0"
SET "RAIZ=%RAIZ:~0,-1%"
SET "NODE_DIR=%RAIZ%\node"
SET "BACKEND_DIR=%RAIZ%\backend"
SET "FRONTEND_DIR=%RAIZ%\frontend"

ECHO ==========================================
ECHO    INICIANDO KORTEXA (MODO SEGURO)
ECHO ==========================================
ECHO.

:: 1. BACKEND (Python leera el .env automaticamente)
ECHO [1/2] Iniciando Cerebro...
start "CEREBRO (Python)" /D "%BACKEND_DIR%" cmd /k "python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000"

timeout /t 4 /nobreak >nul

:: 2. FRONTEND
ECHO [2/2] Iniciando Visual...
start "VISUAL (Frontend)" /D "%FRONTEND_DIR%" cmd /k "set PATH=%NODE_DIR%;%PATH% && "%NODE_DIR%\node.exe" "%NODE_DIR%\node_modules\npm\bin\npm-cli.js" run dev -- -p 3010"

ECHO.
ECHO ==========================================
ECHO    SISTEMA OPERATIVO
ECHO ==========================================
ECHO Accede a: http://localhost:3010
ECHO.
PAUSE