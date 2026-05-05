@echo off
setlocal
title Sincronizador CRM - Farmacias Sao Joao

:: CONFIGURACOES
set REPO_URL=https://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@github.com/lukasg64-png/CRM.git

echo ============================================================
echo   SINCRONIZADOR AUTOMATICO - DASHBOARD CRM
echo ============================================================
echo.

:: 1. ATUALIZAR DADOS DO SNOWFLAKE
echo [*] PASSO 1: Extraindo dados atualizados do Snowflake...
python extrator_master.py
if %ERRORLEVEL% NEQ 0 (
    echo [ERRO] Falha ao extrair dados do Snowflake. Verifique sua conexao ODBC.
    pause
    exit /b
)

echo.
echo [*] PASSO 2: Preparando arquivos para o GitHub...

:: Inicializar Git se nao existir
if not exist .git (
    echo [!] Repositorio nao inicializado. Configurando agora...
    git init
    git remote add origin %REPO_URL%
    git branch -M main
)

:: Garantir que o remote esta correto (com o token atual)
git remote set-url origin %REPO_URL%

:: Adicionar, Commit e Push
git add .
set TIMESTAMP=%date% %time%
git commit -m "Auto-update CRM Data/Code: %TIMESTAMP%"
echo [*] Enviando para o GitHub...
git push -u origin main --force

echo.
echo ============================================================
echo   [OK] TUDO PRONTO! SEU DASHBOARD ESTA NO GITHUB.
echo ============================================================
echo.
pause
