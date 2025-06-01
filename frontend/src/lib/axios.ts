// 汎用ライブラリ（axiosの設定)
import axios, { AxiosRequestConfig, AxiosResponse, AxiosError } from 'axios'

console.log("🔧 API URL:", import.meta.env.VITE_API_URL)

const instance = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:5000/api/',
  timeout: 60000,  // 20000から60000に増量（音声チャットの複数API呼び出し対応）
  withCredentials: true,  // CORS設定のためにtrueに変更
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  }
})

// 実際の設定を確認するためのデバッグログ
console.log("🔧 Axios設定:", {
  baseURL: instance.defaults.baseURL,
  timeout: instance.defaults.timeout,
  withCredentials: instance.defaults.withCredentials
});

// リクエストインターセプター
instance.interceptors.request.use(
  (config: AxiosRequestConfig) => {
    // 認証トークンがあれば自動的にヘッダーに追加
    const token = localStorage.getItem('token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
      console.log('🔑 Authorizationヘッダー設定:', `Bearer ${token.substring(0, 15)}...`);
    }
    
    // withCredentialsを必ず有効にする
    config.withCredentials = true;
    
    console.log('🚀 リクエスト送信:', config.method?.toUpperCase(), config.url, 
                'withCredentials:', config.withCredentials);
    return config;
  },
  (error: AxiosError) => {
    console.error('❌ リクエストエラー:', error);
    return Promise.reject(error);
  }
);

// レスポンスインターセプター
instance.interceptors.response.use(
  (response: AxiosResponse) => {
    console.log('✅ レスポンス受信:', response.status, response.data);
    return response;
  },
  (error: AxiosError) => {
    // CORS関連のエラーをより詳細にログ
    if (error.message && error.message.includes('Network Error')) {
      console.error('❌ ネットワークエラー (可能性のあるCORS問題):', error.message);
    } else {
      console.error('❌ レスポンスエラー:', 
        error.response ? {
          status: error.response.status,
          data: error.response.data,
          headers: error.response.headers
        } : error.message);
    }

    // 認証エラー（401）の場合のみログイン画面にリダイレクト
    if (error.response && error.response.status === 401) {
      console.warn('🔒 認証エラーのため、ログイン画面に遷移します');
      
      const errorMessage = '認証が必要です。ログインしてください。';
      
      // トークンを削除
      localStorage.removeItem('token');
      
      // ログイン画面にリダイレクト（現在のページを保存）
      const currentPath = window.location.pathname;
      if (currentPath !== '/login') {
        console.log('📍 現在のページ:', currentPath);
        sessionStorage.setItem('redirectAfterLogin', currentPath);
        sessionStorage.setItem('loginErrorMessage', errorMessage);
        
        // 少し遅延してリダイレクト（ユーザーがエラーメッセージを読めるように）
        setTimeout(() => {
          window.location.href = '/login';
        }, 1500);
      }
    }

    return Promise.reject(error);
  }
);

export default instance
