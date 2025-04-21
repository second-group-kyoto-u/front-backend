// ログインPOST処理
import axios from '@/lib/axios'
import { AxiosError } from 'axios'

export type LoginRequest = {
  email: string
  password: string
}

export type LoginResponse = {
  token: string
}

export type ApiError = {
  error?: string
  message?: string
}

// baseURLに/apiが含まれているので、前に/apiを付けない
const LOGIN_ENDPOINT = 'auth/login'

export const loginUser = async (
  data: LoginRequest
): Promise<LoginResponse> => {
  try {
    console.log('🔄 ログインリクエスト:', LOGIN_ENDPOINT, data)
    const res = await axios.post<LoginResponse>(LOGIN_ENDPOINT, data)
    
    // 成功したらトークンをローカルストレージに保存
    localStorage.setItem('token', res.data.token)
    
    return res.data
  } catch (error) {
    // エラーをAxiosError型にキャスト
    const axiosError = error as AxiosError<ApiError>
    
    // 認証エラー（401）の場合は統一したメッセージを表示
    if (axiosError.response?.status === 401) {
      throw new Error('メールアドレスまたはパスワードが異なっています。')
    }
    
    // ネットワークエラーの場合
    if (axiosError.code === 'ECONNABORTED') {
      throw new Error('サーバーとの接続がタイムアウトしました')
    }
    if (axiosError.code === 'ERR_NETWORK') {
      throw new Error('ネットワークエラーが発生しました')
    }
    
    // isAxiosErrorメソッドを使ってAxiosのエラーかどうか確認
    if (axios.isAxiosError(error)) {
      // APIからのエラーメッセージがあればそれを使用
      if (axiosError.response?.data) {
        const apiError = axiosError.response.data
        throw new Error(apiError.error || apiError.message || 'ログインに失敗しました')
      }
    }
    
    // その他の予期せぬエラー
    throw new Error('ログインに失敗しました')
  }
}

// ログアウト関数
export const logoutUser = () => {
  localStorage.removeItem('token')
}

// 認証状態を確認する関数
export const isAuthenticated = (): boolean => {
  return localStorage.getItem('token') !== null
}
