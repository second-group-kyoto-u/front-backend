// 汎用ライブラリ（axiosの設定)
import axios from 'axios'

console.log("🔧 API URL:", import.meta.env.VITE_API_URL)

const instance = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:5000/api/',
  timeout: 10000,
  withCredentials: false,  // ✅ 不要（トークンはヘッダーで送信するため）
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
  (config) => {
    // 認証トークンがあれば自動的にヘッダーに追加
    const token = localStorage.getItem('token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
      console.log('🔑 Authorizationヘッダー設定:', `Bearer ${token.substring(0, 15)}...`);
    }
    
    // withCredentialsを必ず有効にする
    // config.withCredentials = true;
    
    console.log('🚀 リクエスト送信:', config.method?.toUpperCase(), config.url, 
                'withCredentials:', config.withCredentials);
    return config;
  },
  (error) => {
    console.error('❌ リクエストエラー:', error);
    return Promise.reject(error);
  }
);

// レスポンスインターセプター
instance.interceptors.response.use(
  (response) => {
    console.log('✅ レスポンス受信:', response.status, response.data);
    return response;
  },
  (error) => {
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
    return Promise.reject(error);
  }
);

export default instance
