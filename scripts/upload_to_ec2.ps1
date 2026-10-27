<#
.SYNOPSIS
    Uploads the Resumo deployment files from your Windows laptop to your EC2 instance.
.EXAMPLE
    .\scripts\upload_to_ec2.ps1 -PublicIp "13.232.100.50" -KeyPath "$HOME\.ssh\resumo-key.pem"
#>
param(
    [Parameter(Mandatory=$true)]
    [string]$PublicIp,

    [Parameter(Mandatory=$false)]
    [string]$KeyPath = "$HOME\.ssh\resumo-key.pem",

    [Parameter(Mandatory=$false)]
    [string]$User = "ec2-user"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $KeyPath)) {
    Write-Error "SSH Key not found at '$KeyPath'. Please check the path to your .pem file."
}

Write-Host "Connecting to $User@$PublicIp using $KeyPath..." -ForegroundColor Cyan

# Ensure remote destination directory exists
ssh -i $KeyPath -o StrictHostKeyChecking=no "$User@$PublicIp" "mkdir -p /home/$User/resumo"

Write-Host "Transferring backend, frontend, configuration and scripts..." -ForegroundColor Cyan

scp -i $KeyPath -r `
    backend `
    frontend `
    docker-compose.aws.yml `
    scripts `
    .env.example `
    "$User@$PublicIp`:/home/$User/resumo"

Write-Host "`n✓ Upload complete!" -ForegroundColor Green
Write-Host "To deploy on the server, SSH in and run:" -ForegroundColor Yellow
Write-Host "  ssh -i `"$KeyPath`" $User@$PublicIp" -ForegroundColor White
Write-Host "  cd ~/resumo && bash scripts/deploy_aws.sh`n" -ForegroundColor White
