@echo off
echo ========================================================
echo Iniciando o Dashboard Executivo de CRM...
echo ========================================================
echo O Streamlit abrira o painel no seu navegador padrao.
echo Caso apareca o popup de login do Snowflake (SSO), basta autorizar.
echo Para desligar o dashboard, basta fechar esta janela preta.
echo.

cd /d "c:\Users\lucas.alves6\.gemini\antigravity\scratch\CRM"
python -m streamlit run app_crm.py
pause
