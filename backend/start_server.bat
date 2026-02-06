@echo off
cd /d "c:\Users\milena\Desktop\new 2\backend"
echo ======================================
echo  Starting API Server
echo ======================================
echo.
python -c "import uvicorn; uvicorn.run('main:app', host='0.0.0.0', port=8000, reload=True)"
pause
