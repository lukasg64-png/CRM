@echo off
setlocal
cd /d "%~dp0.."
title Sincronizador Rapido (Apenas Git) - CRM

:: CONFIGURACOES
set TOKEN=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
set REPO_RAW=github.com/lukasg64-png/CRM.git

echo ============================================================
echo   SINCRONIZADOR RAPIDO - APENAS CODIGO/FRONT-END
echo ============================================================
echo.

:: 1. CONFIGURAR REMOTE
git remote remove origin >nul 2>&1
git remote add origin https://%TOKEN%@%REPO_RAW%

:: 2. ENVIAR MUDANCAS
echo [*] Adicionando mudancas...
git add .

set TIMESTAMP=%date% %time%
echo [*] Criando commit...
git commit -m "Update UI/Front-end: %TIMESTAMP%" --quiet

echo [*] Enviando para o GitHub...
git push -u origin main --force >nul 2>&1

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ============================================================
    echo   [OK] MUDANCAS ENVIADAS! ATUALIZE O STREAMLIT EM 30s.
    echo ============================================================
) else (
    echo.
    echo [ERRO] O envio falhou. Verifique sua internet.
)

echo.
pause
