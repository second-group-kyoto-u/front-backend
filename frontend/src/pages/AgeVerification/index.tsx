import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import styles from './AgeVerification.module.css';
import { useAuth } from '@/hooks/useAuth'; // 認証トークンを取得するためにuseAuthをインポート
import { uploadAgeVerificationImage, AgeVerificationUploadResponse } from '@/api/upload'; // 新しいAPI関数と型をインポート

const AgeVerification: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [message, setMessage] = useState<string>('');
  const navigate = useNavigate();
  // token: 認証トークンをAPIリクエストヘッダーに含めるため
  // fetchProtectedUser: 年齢認証後、ユーザー情報を再取得してUIに反映させるため (例: Mypageの表示更新)
  const { token, fetchProtectedUser } = useAuth(); 

  // ファイルが選択されたときのハンドラー
  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files[0]) {
      const file = event.target.files[0];
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file)); // 画像プレビューのためにURLを生成
      setMessage(''); // ファイルが選択されたらメッセージをクリア
    } else {
      setSelectedFile(null);
      setPreviewUrl(null);
    }
  };

  // フォーム送信時のハンドラー
  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault(); // フォームのデフォルトの送信動作を防ぐ

    if (!selectedFile) {
      setMessage('本人確認書類を選択してください。');
      return;
    }

    // 認証トークンがない場合はログインを促す
    if (!token) {
      setMessage('認証トークンが見つかりません。ログインし直してください。');
      navigate('/login'); // ログインページへリダイレクト
      return;
    }

    setIsLoading(true); // ローディング状態を開始
    setMessage('ファイルをアップロード中...'); // ユーザーへのフィードバック

    try {
      // API呼び出し。upload.tsで定義したuploadAgeVerificationImage関数を使用し、トークンを渡す
      // この関数が内部でFormDataを作成し、'file'キーで画像をappendします。
      const data: AgeVerificationUploadResponse = await uploadAgeVerificationImage(selectedFile, token);

      setMessage(`${data.message}`); // バックエンドからのメッセージをそのまま表示
      console.log('Upload successful:', data);

      // バックエンドから返された最新のユーザー情報でフロントエンドの状態を更新
      // fetchProtectedUser() を呼び出すことで、Mypageでデータが再取得され最新の状態になることを期待します。
      if (data.user) {
        fetchProtectedUser(); // ユーザー情報を再取得してMypageなどに反映させる
      }
      
      // 成功したらマイページへ遷移
      setTimeout(() => {
        navigate('/mypage');
      }, 3000); // 3秒後に遷移

    } catch (error: any) { // エラーをany型でキャッチし、詳細なメッセージを抽出
      console.error('Upload failed:', error);
      // バックエンドからのエラーレスポンス構造に応じてメッセージを抽出
      const errorMessage = error.message || (error.response && error.response.data && error.response.data.message) || error.error || '不明なエラーが発生しました。';
      setMessage(`アップロードに失敗しました: ${errorMessage}`);
    } finally {
      setIsLoading(false); // ローディング状態を終了
    }
  };

  // コンポーネントのレンダリング
  return (
    <div className={styles.pageBackground}>
      <div className={styles.container}>
        <h1 className={styles.title}>年齢認証</h1>
        <p className={styles.description}>
          旅行好きのためのマッチングアプリのご利用には、年齢認証が必要です。<br />
          運転免許証、パスポート、マイナンバーカードなどの本人確認書類をアップロードしてください。
        </p>

        <form onSubmit={handleSubmit} className={styles.form}>
          <div className={styles.fileInputGroup}>
            <label htmlFor="document-upload" className={styles.fileInputLabel}>
              {selectedFile ? selectedFile.name : '本人確認書類を選択...'}
            </label>
            <input
              type="file"
              id="document-upload"
              accept="image/*" // 画像ファイルのみ許可
              onChange={handleFileChange}
              className={styles.hiddenFileInput}
            />
          </div>

          {previewUrl && (
            <div className={styles.imagePreview}>
              <img src={previewUrl} alt="プレビュー" className={styles.previewImage} />
            </div>
          )}

          {/* メッセージ表示エリア */}
          {message && <p className={styles.message}>{message}</p>}

          <button
            type="submit"
            className={styles.submitButton}
            disabled={!selectedFile || isLoading} // ファイルが選択されていない、またはローディング中は無効化
          >
            {isLoading ? '送信中...' : '提出する'}
          </button>
        </form>

        <button onClick={() => navigate('/mypage')} className={styles.backButton}>
          マイページに戻る
        </button>
      </div>
    </div>
  );
};

export default AgeVerification;