import React, { useState, useEffect, FormEvent } from 'react'
import { loginUser } from '../../api/auth/login'
import { useNavigate, Link, useLocation } from 'react-router-dom'
import { useAuth } from '../../hooks/useAuth'
import styles from './Login.module.css'

// 前のページからの情報を取得するための型
interface PrevLocationData {
  from?: string;
  message?: string;
}

function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()
  const location = useLocation()
  const { login, isAuthenticated, isLoading } = useAuth()
  // リダイレクト先URLを保存
  const [redirectUrl, setRedirectUrl] = useState('/mypage')

  useEffect(() => {
    // 前のページからのメッセージとリダイレクト先を取得
    const state = location.state as PrevLocationData
    
    if (state?.message) {
      setMessage(state.message)
    }
    
    // sessionStorageからエラーメッセージを確認
    const savedErrorMessage = sessionStorage.getItem('loginErrorMessage')
    if (savedErrorMessage) {
      console.log('👉 sessionStorageからエラーメッセージを復元:', savedErrorMessage)
      setMessage(savedErrorMessage)
      sessionStorage.removeItem('loginErrorMessage') // 一度表示したら削除
    }
    
    // sessionStorageからリダイレクト先を確認
    const savedRedirect = sessionStorage.getItem('redirectAfterLogin')
    if (savedRedirect) {
      console.log('👉 sessionStorageからリダイレクト先を復元:', savedRedirect)
      setRedirectUrl(savedRedirect)
    } else if (state?.from) {
      console.log('👉 stateからリダイレクト先を設定:', state.from)
      setRedirectUrl(state.from)
    }
  }, [location])

  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      console.log('✅ ログイン済みのためリダイレクトします')
      console.log('👉 リダイレクト先:', redirectUrl)
      
      // イベント作成ページへのリダイレクトの場合、直接URLを使用
      if (redirectUrl === '/event/create') {
        console.log('🎯 イベント作成ページへ直接リダイレクトします')
        window.location.href = redirectUrl
        return
      }
      
      // 通常のナビゲーション
      navigate(redirectUrl, { replace: true })
    }
  }, [isAuthenticated, isLoading, navigate, redirectUrl])

  const handleSubmit = async (e?: FormEvent) => {
    if (e) e.preventDefault()
    if (!email || !password) {
      setError('メールアドレスとパスワードを入力してください')
      return
    }

    try {
      setLoading(true)
      setError('')
      console.log('🔑 ログイン試行中...')
      const data = await loginUser({ email, password })
      console.log('✅ ログイン成功、トークンを保存します')
      await login(data.token)
      
      // ログイン成功後のリダイレクト先を再確認
      console.log('👉 ログイン後のリダイレクト先:', redirectUrl)
      
      // sessionStorageをクリア
      sessionStorage.removeItem('redirectAfterLogin')
      
    } catch (err: any) {
      console.error('❌ ログイン失敗:', err)
      setError(err.message || 'ログインできませんでした')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className={styles.pageBackground}>
      <div className={styles.loginContainer}>
        <h1 className={styles.loginTitle}>ログイン</h1>

        {/* デバッグ情報 */}
        {redirectUrl !== '/mypage' && (
          <div className={styles.redirectInfo}>
            ログイン後の遷移先: {redirectUrl}
          </div>
        )}

        {/* 前のページからのメッセージがあれば表示 */}
        {message && (
          <div className="bg-blue-100 border-l-4 border-blue-500 text-blue-700 p-4 mb-4 rounded">
            {message}
          </div>
        )}

        <form onSubmit={handleSubmit} className={styles.loginForm}>
          <div className={styles.formGroup}>
            <div className={styles.inputWrapper}>
              <input
                type="email"
                id="email"
                placeholder=" "
                value={email}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setEmail(e.target.value)}
                required
              />
              <label htmlFor="email">メールアドレス</label>
            </div>
          </div>

          <div className={styles.formGroup}>
            <div className={styles.inputWrapper}>
              <input
                type="password"
                id="password"
                placeholder=" "
                value={password}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setPassword(e.target.value)}
                required
              />
              <label htmlFor="password">パスワード</label>
            </div>
            <div className={styles.forgotPassword}>
              <Link to="/forgot-password">パスワードを忘れた方はこちら</Link>
            </div>
          </div>

          {error && <div className={styles.error}>{error}</div>}

          <button type="submit" disabled={loading} className={styles.loginButton}>
            {loading ? 'ログイン中...' : 'ログイン'}
          </button>
        </form>

        <div className={styles.divider}></div>

        <div className={styles.registerSection}>
          <Link to="/register" className={styles.registerButton}>
            新規登録
          </Link>
        </div>
      </div>
    </div>
  )
}

export default LoginPage