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

  // ✅ ログイン済みユーザーはリダイレクト
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
    <div className={styles.loginContainer}>
      <h1>ログイン</h1>
      <form onSubmit={handleSubmit} className={styles.loginForm}>
        <div className={styles.formGroup}>
          <label htmlFor="email">メールアドレス</label>
          <input
            type="email"
            id="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </div>
        <div className={styles.formGroup}>
          <label htmlFor="password">パスワード</label>
          <input
            type="password"
            id="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>
        {error && <div className={styles.error}>{error}</div>}
        <button type="submit" disabled={loading} className={styles.loginButton}>
          {loading ? 'ログイン中...' : 'ログイン'}
        </button>
      </form>

      <div className={styles.links}>
        <Link to="/threads" className={styles.featureLink}>スレッド一覧を見る</Link>
        <Link to="/events" className={styles.featureLink}>イベント一覧を見る</Link>
        <p>アカウントをお持ちでない方は <Link to="/register">新規登録</Link></p>
      </div>
    </div>
  )
}

export default LoginPage
