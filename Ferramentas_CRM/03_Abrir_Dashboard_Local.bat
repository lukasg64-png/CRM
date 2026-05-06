@echo off
setlocal
cd /d "%~dp0.."
title Abrir Dashboard CRM - Local

echo ============================================================
echo   INICIANDO DASHBOARD CRM (LOCAL)
echo ============================================================
echo.
echo [*] Abrindo o Streamlit no seu navegador...
streamlit run app_crm.py --server.port 8502

pause
