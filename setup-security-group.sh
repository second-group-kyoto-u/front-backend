#!/bin/bash

# EC2セキュリティグループ自動設定スクリプト
# 使用方法: ./setup-security-group.sh <security-group-id>

if [ $# -eq 0 ]; then
    echo "使用方法: $0 <security-group-id>"
    echo "例: $0 sg-1234567890abcdef0"
    exit 1
fi

SECURITY_GROUP_ID=$1

echo "🔒 セキュリティグループ ($SECURITY_GROUP_ID) にルールを追加中..."

# HTTP (ポート80) - フロントエンド
aws ec2 authorize-security-group-ingress \
    --group-id $SECURITY_GROUP_ID \
    --protocol tcp \
    --port 80 \
    --cidr 0.0.0.0/0 \
    --output text 2>/dev/null || echo "ポート80は既に開放されています"

# MinIO API (ポート9000)
aws ec2 authorize-security-group-ingress \
    --group-id $SECURITY_GROUP_ID \
    --protocol tcp \
    --port 9000 \
    --cidr 0.0.0.0/0 \
    --output text 2>/dev/null || echo "ポート9000は既に開放されています"

# MinIO Console (ポート9001)
aws ec2 authorize-security-group-ingress \
    --group-id $SECURITY_GROUP_ID \
    --protocol tcp \
    --port 9001 \
    --cidr 0.0.0.0/0 \
    --output text 2>/dev/null || echo "ポート9001は既に開放されています"

echo "✅ セキュリティグループの設定完了！"
echo ""
echo "開放されたポート:"
echo "- 80 (HTTP) - フロントエンド（APIプロキシ含む）"
echo "- 9000 - MinIO API"
echo "- 9001 - MinIO Console" 