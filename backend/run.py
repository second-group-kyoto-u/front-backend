from app import create_app

app = create_app() # バックエンドコンテナの起動コマンド。プロジェクトの動作に不可欠なコアファイル

if __name__ == '__main__':
    # app.run(debug=True, port=5000) # debug=Trueとは、Flaskアプリを **「ローカル開発モード」で起動する」設定。
    app.run(host='0.0.0.0', port=5000, debug=True)  # ← host='0.0.0.0' が重要！ Dockerはコンテナの中で動くので、localhost のままだと 外のPC（ホスト）からアクセスできない
