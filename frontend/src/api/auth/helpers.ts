// 認証ヘルパー関数

/**
 * 認証ヘッダーを取得する
 * ローカルストレージからトークンを取得してAuthorizationヘッダーを作成
 * @returns 認証ヘッダーオブジェクト
 */
export const getAuthHeader = () => {
  const token = localStorage.getItem('token');
  if (!token) return {};
  return {
    Authorization: `Bearer ${token}`
  };
};

/**
 * ローカルストレージから認証トークンを取得
 * @returns トークン文字列またはnull
 */
export const getToken = () => {
  return localStorage.getItem('token');
};

/**
 * ユーザーが認証済みかどうかを確認
 * @returns 認証済みならtrue、それ以外はfalse
 */
export const isAuthenticated = () => {
  return !!getToken();
};

/**
 * ログアウト処理
 * ローカルストレージからトークンを削除
 */
export const logout = () => {
  localStorage.removeItem('token');
}; 