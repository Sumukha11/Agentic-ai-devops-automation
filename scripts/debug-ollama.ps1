# Debug script for Ollama startup issues

Write-Host "=== Checking Docker and Docker-Compose ===" -ForegroundColor Cyan
docker --version
docker-compose --version

Write-Host "`n=== Checking for port conflicts ===" -ForegroundColor Cyan
netstat -ano | findstr :11434

Write-Host "`n=== Removing existing containers ===" -ForegroundColor Cyan
docker-compose down -v

Write-Host "`n=== Pulling latest Ollama image ===" -ForegroundColor Cyan
docker pull ollama/ollama:latest

Write-Host "`n=== Starting Ollama service with verbose output ===" -ForegroundColor Cyan
cd "c:\Users\rampr\OneDrive\Desktop\IITP-3rd-sem-project-Agentic_AI_DevOps_Tools"
docker-compose up -d ollama

Write-Host "`n=== Waiting 10 seconds for Ollama to start ===" -ForegroundColor Cyan
Start-Sleep -Seconds 10

Write-Host "`n=== Checking container status ===" -ForegroundColor Cyan
docker-compose ps

Write-Host "`n=== Ollama logs ===" -ForegroundColor Cyan
docker-compose logs ollama --tail=50

Write-Host "`n=== Checking if Ollama is responding ===" -ForegroundColor Cyan
try {
    $response = Invoke-WebRequest -Uri "http://localhost:11434/" -TimeoutSec 5 -ErrorAction Stop
    Write-Host "Ollama is responding: $($response.StatusCode)" -ForegroundColor Green
} catch {
    Write-Host "Ollama not responding: $_" -ForegroundColor Red
}

Write-Host "`n=== Done ===" -ForegroundColor Cyan
