#!/bin/bash
# ==============================================================================
# Fetch secrets from AWS Systems Manager (SSM) Parameter Store into environment
# ==============================================================================
set -e

REGION="${AWS_REGION:-ap-south-1}"

echo "[SSM] Checking parameters under /resumo/ in region $REGION..."

FETCHED_SECRET_KEY=$(aws ssm get-parameter --name "/resumo/SECRET_KEY" --with-decryption --region "$REGION" --query "Parameter.Value" --output text 2>/dev/null | tr -d '\r\n' || true)
FETCHED_DATABASE_URL=$(aws ssm get-parameter --name "/resumo/DATABASE_URL" --with-decryption --region "$REGION" --query "Parameter.Value" --output text 2>/dev/null | tr -d '\r\n' || true)

if [ -n "$FETCHED_SECRET_KEY" ]; then
    export SECRET_KEY="$FETCHED_SECRET_KEY"
    echo "✓ [SSM] Retrieved SECRET_KEY"
else
    echo "i [SSM] No /resumo/SECRET_KEY in SSM; fallback to .env value"
fi

if [ -n "$FETCHED_DATABASE_URL" ]; then
    export DATABASE_URL="$FETCHED_DATABASE_URL"
    echo "✓ [SSM] Retrieved DATABASE_URL"
else
    echo "i [SSM] No /resumo/DATABASE_URL in SSM; fallback to .env value"
fi

export S3_BUCKET="resumo-files-vicky"
export S3_REGION="$REGION"
export STORAGE_BACKEND="s3"

# Detect Public IP via IMDSv2 or external fallback
TOKEN=$(curl -s -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 60" 2>/dev/null || true)
if [ -n "$TOKEN" ]; then
    PUBLIC_IP=$(curl -s -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || true)
fi
if [ -z "$PUBLIC_IP" ]; then
    PUBLIC_IP=$(curl -s ifconfig.me 2>/dev/null || echo "65.2.6.163")
fi

export FRONTEND_ORIGIN="http://${PUBLIC_IP}"
echo "✓ Target Frontend Origin: ${FRONTEND_ORIGIN}"
