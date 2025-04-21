// トークンやログイン状態の管理
import { useState, useEffect, useCallback } from 'react'
import { logoutUser } from '../api/auth/login'
import axios from '../lib/axios'

export function useAuth() {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false)
  const [isLoading, setIsLoading] = useState<boolean>(true)

  // 🔧 これを追加
  const getToken = useCallback((): string | null => {
    return localStorage.getItem('token')
  }, [])

  const verifyToken = useCallback(async (): Promise<boolean> => {
    const token = getToken()
    if (!token) {
      console.warn('⚠️ トークンが存在しません（未ログイン状態）')
      return false
    }

    try {
      console.log('🔍 トークン検証API呼び出し中...')
      const response = await axios.get('/auth/verify')
      console.log('✅ トークン有効！レスポンス:', response.data)
      return true
    } catch (error: any) {
      console.error('❌ トークン無効または検証失敗:')
      if (error.response) {
        console.error('🧾 サーバーレスポンス:', {
          status: error.response.status,
          data: error.response.data,
          headers: error.response.headers
        })
      } else if (error.request) {
        console.error('📡 リクエスト送信済みだが応答なし:', error.request)
      } else {
        console.error('⚠️ その他のエラー:', error.message)
      }

      localStorage.removeItem('token')
      return false
    }
  }, [getToken])


  // 認証状態の初期化
  useEffect(() => {
    const initAuth = async () => {
      setIsLoading(true)
      try {
        const isValid = await verifyToken()
        setIsAuthenticated(isValid)
      } catch (error) {
        console.error('認証状態の初期化に失敗:', error)
        setIsAuthenticated(false)
      } finally {
        setIsLoading(false)
      }
    }

    initAuth()
  }, [verifyToken])
  
  // ログイン処理
  const login = useCallback(async (token: string) => {
    console.log('🔑 トークンをローカルストレージに保存')
    localStorage.setItem('token', token)
  
    const valid = await verifyToken()
    setIsAuthenticated(valid)
  }, [verifyToken])
  
  
  // ログアウト処理
  const logout = useCallback(() => {
    console.log('🚪 ログアウト処理')
    localStorage.removeItem('token')
    setIsAuthenticated(false)
  }, [])

  const token = getToken()

  return {
    isAuthenticated,
    isLoading,
    login,
    logout,
    getToken,
    token
  }
}