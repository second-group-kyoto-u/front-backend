# Tripple - 旅行マッチングアプリケーション

## 🌍 アプリケーション概要

Trippleは、同じ旅行先や期間で旅行を計画している人々をマッチングする革新的なWebアプリケーションです。一人旅の不安を解消し、新しい出会いと共に忘れられない旅行体験を提供します。

### アプリケーション画面

![アプリケーション画面(一部)](sample_images/スクリーンショット%202025-06-15%2020.39.52.png)
![生成AIバックエンド処理概要](sample_images/スクリーンショット%202025-06-15%2020.40.02.png)

### 主な特徴

- **旅行者マッチング**: 行き先、日程、興味が合う旅行者を自動的にマッチング
- **プロフィール機能**: 自己紹介、旅行スタイル、興味などを登録
- **チャット機能**: マッチした相手とリアルタイムでコミュニケーション
- **旅行内容共有**: 旅程や観光スポットの情報を共有

## 💻 技術スタック

### フロントエンド
- **React** (TypeScript) - ユーザーインターフェース
- **Vite** - 高速な開発環境
- **CSS Modules** - スタイリング

### バックエンド
- **Flask** (Python) - APIサーバー
- **PostgreSQL** - データベース
- **MinIO** - 画像ストレージ

### インフラ
- **Docker & Docker Compose** - コンテナ化
- **AWS EC2** - クラウドホスティング

## 🚀 クイックスタート

### 必要条件
- [Docker](https://www.docker.com/)
- [Docker Compose](https://docs.docker.com/compose/)

### ローカル環境での起動

1. **環境設定ファイルの準備**
   ```bash
   cp .env.example .env
   # .envファイルを編集して必要な設定を行う
   ```

2. **アプリケーションの起動**
   ```bash
   docker compose up --build -d
   ```

3. **初期データの投入**
   ```bash
   docker compose exec backend python scripts/seed.py
   ```

4. **アクセス**
   - フロントエンド: http://localhost:3000
   - バックエンドAPI: http://localhost:5000/api/
   - MinIOコンソール: http://localhost:9001

## 使い方

1. **アカウント登録**
   - メールアドレスとパスワードで新規登録
   - プロフィール情報（名前、年齢、趣味など）を入力

2. **旅行内容の投稿**
   - イベントに関する質問や過去のイベントの共有を実施

3. **マッチング**
   - 条件に合う旅行者が自動的に表示
   - 気になる相手にいいね！を送信

4. **コミュニケーション**
   - マッチが成立したらチャット開始
   - 旅行プランの詳細を相談


## 🔧 開発者向け情報

### プロジェクト構造
```
front-backend-1/
├── frontend/          # Reactアプリケーション
│   ├── src/
│   │   ├── api/      # API通信
│   │   ├── hooks/    # カスタムフック
│   │   ├── pages/    # ページコンポーネント
│   │   └── lib/      # ユーティリティ
│   └── public/       # 静的ファイル
├── backend/          # Flaskアプリケーション
├── docker-compose.yml
└── README.md
```

### 開発コマンド

**ログの確認**
```bash
docker compose logs -f backend
docker compose logs -f frontend
```

**環境の停止**
```bash
docker compose down
```

**データベースのリセット**
```bash
docker compose down -v
docker compose up -d
docker compose exec backend python scripts/seed.py
```


## 🌐 本番環境へのデプロイ

### AWS EC2でのワンクリックデプロイ

1. **EC2インスタンスの準備**
   - Amazon Linux 2023推奨
   - t3.micro以上のインスタンスタイプ
   - セキュリティグループで必要なポートを開放

2. **デプロイの実行**
   ```bash
   # プロジェクトをEC2にアップロード
   scp -r . ec2-user@<EC2のパブリックIP>:~/front-backend-1/
   
   # EC2にSSH接続してデプロイ
   ssh ec2-user@<EC2のパブリックIP>
   cd front-backend-1
   chmod +x deploy-ec2.sh
   ./deploy-ec2.sh
   ```

3. **アクセス確認**
   - `http://<EC2のパブリックIP>` でアプリケーションにアクセス
