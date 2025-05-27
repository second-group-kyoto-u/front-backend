#!/bin/bash

# EC2 ワンクリックデプロイスクリプト
# 使用方法: chmod +x deploy-ec2.sh && ./deploy-ec2.sh

set -e  # エラーが発生したら停止

echo "🚀 EC2デプロイメント開始..."

# システム更新
echo "📦 システムパッケージを更新中..."
sudo yum update -y

# Dockerのインストール
echo "🐳 Dockerをインストール中..."
sudo yum install -y docker
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -a -G docker ec2-user

# Docker Composeのインストール
echo "🔧 Docker Composeをインストール中..."
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Gitのインストール（まだインストールされていない場合）
echo "📥 Gitをインストール中..."
sudo yum install -y git

# 現在のディレクトリにプロジェクトファイルがあるかチェック
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ エラー: docker-compose.ymlが見つかりません"
    echo "このスクリプトはプロジェクトのルートディレクトリで実行してください"
    exit 1
fi

# EC2のパブリックIPアドレスを取得
echo "🔍 EC2のパブリックIPアドレスを取得中..."
PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)
if [ -z "$PUBLIC_IP" ]; then
    echo "❌ パブリックIPの取得に失敗しました"
    exit 1
fi
echo "✅ パブリックIP: $PUBLIC_IP"

# .envファイルを作成
echo "📝 .envファイルを作成中..."
cat > .env << EOF
# Flask Configuration
FLASK_ENV=production
FLASK_SECRET_KEY=your-super-secret-key-change-this-in-production-$(openssl rand -hex 16)
FLASK_DEBUG=False

# API Configuration
VITE_API_URL=http://$PUBLIC_IP/api/

# CORS Configuration
CORS_ALLOWED=http://$PUBLIC_IP,https://$PUBLIC_IP

# Public Host Configuration
PUBLIC_HOST=$PUBLIC_IP

# Database Configuration
DATABASE_URL=mysql://travel_user:travel_password@db:3306/travel_matching_db
DB_HOST=db
DB_PORT=3306
DB_NAME=travel_matching_db
DB_USER=travel_user
DB_PASSWORD=travel_password

# MinIO Configuration
MINIO_ENDPOINT=http://minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin123
MINIO_SECURE=false
MINIO_BUCKET=travel-images
PUBLIC_MINIO_ENDPOINT=http://$PUBLIC_IP:9000

# External APIs
OPENAI_API_KEY=your-openai-api-key-here
GOOGLE_PLACES_API_KEY=your-google-places-api-key-here

# JWT Configuration
JWT_SECRET_KEY=your-jwt-secret-key-change-this-in-production-$(openssl rand -hex 16)
JWT_ACCESS_TOKEN_EXPIRES=3600

# Other Configuration
UPLOAD_FOLDER=/app/uploads
MAX_CONTENT_LENGTH=16777216
EOF

# Dockerグループの権限を適用するため、新しいシェルセッションを開始
echo "🔄 Docker権限を適用中..."
newgrp docker << EOFGROUP

# 既存のコンテナを停止・削除
echo "🛑 既存のコンテナを停止中..."
docker-compose down --remove-orphans || true

# Dockerイメージをビルド
echo "🏗️  Dockerイメージをビルド中..."
docker-compose build --no-cache

# コンテナを起動
echo "🚀 コンテナを起動中..."
docker-compose up -d

# データベースの準備完了を待機
echo "⏳ データベースの準備完了を待機中..."
sleep 45

# データベース接続確認
echo "🔍 データベース接続を確認中..."
for i in {1..10}; do
    if docker-compose exec -T db mysqladmin ping -h localhost -u appuser -ppassword --silent; then
        echo "✅ データベース接続確認完了"
        break
    else
        echo "⏳ データベース接続待機中... ($i/10)"
        sleep 5
    fi
done

# seedデータの導入
echo "🌱 seedデータを導入中..."
docker-compose exec -T backend python scripts/seed.py

# コンテナの状態確認
echo "📊 コンテナの状態確認..."
docker-compose ps

EOFGROUP

echo ""
echo "🎉 デプロイ完了！"
echo "=================================="
echo "📱 フロントエンド: http://$PUBLIC_IP"
echo "🔧 バックエンドAPI: http://$PUBLIC_IP/api/"
echo "💾 MinIOコンソール: http://$PUBLIC_IP:9001"
echo "   ユーザー名: minioadmin"
echo "   パスワード: minioadmin"
echo "🌱 seedデータ: 導入完了"
echo "=================================="
echo ""
echo "⚠️  セキュリティグループで以下のポートが開放されていることを確認してください:"
echo "   - ポート 80 (HTTP) - フロントエンド・API"
echo "   - ポート 9000-9001 (MinIO)"
echo ""
echo "🔍 ログを確認する場合: docker-compose logs -f"
echo "🛑 停止する場合: docker-compose down"
echo "🌱 seedデータ再導入: docker-compose exec backend python scripts/seed.py" 