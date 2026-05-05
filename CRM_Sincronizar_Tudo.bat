@echo off
setlocal
title Sincronizador CRM - Farmacias Sao Joao

:: CONFIGURACOES
set TOKEN=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
set REPO_RAW=github.com/lukasg64-png/CRM.git

echo ============================================================
echo   SINCRONIZADOR AUTOMATICO - DASHBOARD CRM
echo ============================================================
echo.

:: 1. ATUALIZAR DADOS DO SNOWFLAKE
echo [*] PASSO 1: Extraindo dados atualizados do Snowflake...
python extrator_master.py
if %ERRORLEVEL% NEQ 0 (
    echo [AVISO] Alguns dados nao puderam ser extraidos. Verifique sua internet.
)

echo.
echo [*] PASSO 2: Preparando arquivos para o GitHub...

:: Inicializar Git se nao existir
if not exist .git (
    git init
    git branch -M main
)

:: Configurar o remote de forma silenciosa para evitar deteccao de segredo no log
git remote remove origin >nul 2>&1
git remote add origin https://%TOKEN%@%REPO_RAW%

:: Adicionar, Commit e Push
git add .
set TIMESTAMP=%date% %time%
git commit -m "Update Dashboard Data: %TIMESTAMP%" --quiet

echo [*] Enviando para o GitHub...
:: Ocultar a saida do push para nao mostrar o token em caso de erro no console
git push -u origin main --force >nul 2>&1

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ============================================================
    echo   [OK] TUDO PRONTO! SEU DASHBOARD ESTA NO GITHUB.
    echo ============================================================
) else (
    echo.
    echo [ERRO] O envio falhou. 
    echo 1. Verifique sua internet.
    echo 2. Certifique-se de que liberou o "Secret" no link do GitHub que te mandei.
)

echo.
pause
