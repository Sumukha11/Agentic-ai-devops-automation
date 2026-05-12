@echo off
REM Debug script for Ollama startup issues

echo === Checking Docker ===
docker --version

echo.
echo === Stopping existing containers ===
docker-compose down -v

echo.
echo === Pulling latest Ollama image ===
docker pull ollama/ollama:latest

echo.
echo === Starting just Ollama ===
cd /d c:\Users\rampr\OneDrive\Desktop\IITP-3rd-sem-project-Agentic_AI_DevOps_Tools
docker-compose up -d ollama

echo.
echo === Waiting 15 seconds ===
timeout /t 15

echo.
echo === Container status ===
docker-compose ps

echo.
echo === Ollama logs ===
docker-compose logs ollama --tail=100

echo.
echo === Checking port 11434 ===
netstat -ano | findstr :11434

echo.
echo === Testing curl to localhost ===
curl -v http://localhost:11434/

echo.
echo === Done ===
pause
