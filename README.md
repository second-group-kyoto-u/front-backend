# Riskdog Backend

## 説明

旅行用のマッチングアプリケーションの開発レポジトリです。

## 準備(必須条件)

次のツールがインストールされている必要があります。

- [Docker](https://www.docker.com/)
- [Docker Compose](https://docs.docker.com/compose/)

## 使い方
# .env を生成する
（ただし、共有した内容を入力・保存した上で実行）
```sh
cp .env.example .env
```

### Dockerの立ち上げ
1. Docker.app が起動していることを確認
2. 以下で一括起動（-dを付けることで、ターミナルがそのまま使える）

```sh
docker-compose up --build -d
```

## （例）Docker環境での npm run dev 再起動方法
```sh
docker-compose up -d --build frontend
```


## 状況を確認
### フロントエンド
React: http://localhost:3000

### バックエンド（/api/helloのルートの場合(多分使わないし、使っても拒否されると思う。)）
Flask: http://localhost:5000/api/login

## Docker環境の終了
```sh
docker-compose down
```

## うまくいっているかログを確認したい時
方法1. アプリブラウザ>検証>console 
方法2. docker desktop上でログを確認




<開発の際につまづいた時のメモ(過去の遺物)>
<関本>
## npm install等で社内プロキシサーバーに引っかかるとき
'''
### 一時的に緩める
npm config set strict-ssl false
npm config set registry http://registry.npmjs.org/

### 再実行
npm install

### 成功後に戻す
npm config set strict-ssl true
npm config set registry https://registry.npmjs.org/
'''

## Viteプロジェクトの基本構成
my-vite-app/
├── index.html                 ← エントリHTML(ビルドの起点)
├── package.json               ← プロジェクト情報や依存ライブラリ、npmスクリプトを定義・管理
├── tsconfig.json              ← TypeScript設定。型チェックの厳密さやパスエイリアスなどを定義できる。
├── vite.config.ts             ← Vite用の設定ファイル
├── node_modules/              ← npm依存ライブラリ（install後）
├── public/                    ← 静的ファイル（favicon, imagesなど）
└── src/                       ← アプリ本体
    ├── main.tsx              ← アプリのエントリポイント(JSのスタート地点。ここで、App.tsxを呼び出し、#rootにマウントする)
    ├── App.tsx               ← 最初に表示されるReactコンポーネント。最初の画面UI。!!まずはここを書き換えてUIを構築していく。
    └── その他のComponentやPage

## 実行系のコマンド
'''　React（TypeScript）プロジェクトのルート（frontend/）で以下を実行
npm run dev //開発サーバー起動（http://localhost:5173）
'''
npm run build //本番用ビルド（dist/に出力）
'''
npm run preview //ビルド成果物のローカル確認用サーバー起動
'''

## フロント（React + Vite + TypeScript）開発環境の立ち上げ
'''
cd frontend
npm install //package.jsonでライブラリ等を一括読み込み
npm run dev //package.json の中にある scripts の "dev" に定義されたコマンド"vite"を実行し、開発用サーバーを起動
'''

## 今のプロジェクト構成の状況
src/
├── api/               # ✅ バックエンドとの通信を管理
│   ├── auth/          # 認証関連API
│   │   ├── login.ts        ← ログインPOST処理
│   │   ├── protected.ts    ← 認証済みページの取得
│   │   └── register.ts     ← 新規登録（予定）
│   ├── user/          # ユーザー情報取得API（予定）
│   └── index.ts       # （将来的にまとめ用）
│
├── assets/            # 🎨 画像やアイコンなど（現状なし）
│
├── hooks/             # 🔄 React用の状態・ロジック管理
│   ├── useAuth.ts     ← トークンやログイン状態の管理
│   └── useUser.ts     ← ユーザー情報の取得・管理（予定）
│
├── lib/               # 🧩 汎用ライブラリ（axiosの設定など）
│   └── axios.ts       ← 共通APIクライアント
│
├── pages/             # 📄 ページUIコンポーネント
│   ├── Login/
│   │   └── index.tsx       ← ログインフォーム
│   └── Mypage/
│       ├── index.tsx       ← 認証済みユーザー画面
│       └── Mypage.module.css ← スタイル
│
├── App.tsx            # 🌳 アプリのルート（ルーティングなど）
├── main.tsx           # アプリ起動のエントリーポイント
└── vite-env.d.ts      # 環境変数定義


<大林>

<中塚>

<山本>

<陳>
