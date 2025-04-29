import React, { useState, useEffect, FormEvent } from 'react'
import { loginUser } from '../../api/auth/login'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../../hooks/useAuth'
import styles from './Login.module.css'

function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()
  const { login, isAuthenticated, isLoading } = useAuth()

  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      console.log('✅ ログイン済みなのでマイページへ遷移')
      navigate('/mypage', { replace: true })
    }
  }, [isAuthenticated, isLoading, navigate])

  const handleSubmit = async (e?: FormEvent) => {
    if (e) e.preventDefault()
    if (!email || !password) {
      setError('メールアドレスとパスワードを入力してください')
      return
    }

    try {
      setLoading(true)
      setError('')
      const data = await loginUser({ email, password })
      login(data.token)
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