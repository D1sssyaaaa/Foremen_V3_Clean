@echo off
echo Starting Cloudflare Tunnel for localhost:8000...
.\cloudflared.exe tunnel --protocol http2 --url http://localhost:8000
pause
