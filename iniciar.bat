@echo off
setlocal EnableDelayedExpansion
title FinanceAgent Desktop - Executive Conciliator
chcp 65001 > nul

REM Navega para o diretorio base do script de forma resiliente
cd /d "%~dp0"

echo ============================================================
echo   FinanceAgent Desktop - Executive Dark Edition
echo   Plataforma de Conciliacao OFX e Inteligencia Financeira
echo ============================================================
echo.

REM 1. Verificar se o ambiente virtual ja existe
if exist ".venv\Scripts\python.exe" goto INICIAR_APP

REM 2. Criacao do ambiente virtual quando ausente
echo [AVISO] Ambiente virtual nao detectado.
echo [STATUS] Criando ambiente virtual isolado...
echo.

python -m venv .venv
if errorlevel 1 goto ERRO_VENV

echo [STATUS] Atualizando pip e instalando dependencias de requirements.txt...
".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto ERRO_PIP

echo.
echo [SUCESSO] Ambiente configurado com exito!
echo.

:INICIAR_APP
echo [STATUS] Inicializando FinanceAgent Desktop...
echo [INFO] Diretorio de execucao: %CD%
echo.

".venv\Scripts\python.exe" app.py
if errorlevel 1 goto ERRO_APP

goto FIM

:ERRO_VENV
echo.
echo [ERRO] Nao foi possivel criar o ambiente virtual com 'python -m venv .venv'.
echo Certifique-se de ter o Python 3.10 ou superior instalado e adicionado ao PATH do Windows.
echo.
pause
exit /b 1

:ERRO_PIP
echo.
echo [ERRO] Ocorreu uma falha ao instalar as dependencias via pip.
echo Verifique sua conexao com a internet ou os pacotes em requirements.txt.
echo.
pause
exit /b 1

:ERRO_APP
echo.
echo [AVISO] O aplicativo foi finalizado com codigo de erro %ERRORLEVEL%.
echo.
pause
exit /b %ERRORLEVEL%

:FIM
endlocal
