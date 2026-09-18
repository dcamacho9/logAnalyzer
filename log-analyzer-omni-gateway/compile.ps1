# Script simplificado para compilar

Write-Host "================================" -ForegroundColor Green
Write-Host "Compilando para CloudHub..." -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green
Write-Host ""

# Limpiar
Write-Host "Limpiando build anterior..." -ForegroundColor Cyan
mvn clean

# Compilar
Write-Host "Compilando aplicacion..." -ForegroundColor Cyan
mvn package

Write-Host ""
Write-Host "================================" -ForegroundColor Green
Write-Host "Compilacion completada" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green
