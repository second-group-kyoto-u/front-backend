import { useState } from 'react'
import { registerUser } from '@/api/auth/register'
import { useNavigate, Link } from 'react-router-dom'
import styles from './Register.module.css'

function RegisterPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [userName, setUserName] = useState('')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const navigate = useNavigate()

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!email || !password || !userName) {
      setError('すべての項目を入力してください')
      return
    }

    setIsSubmitting(true)
    setError('')

    try {
      const data = await registerUser({ email, password, userName })
      localStorage.setItem('token', data.token)
      setSuccess(data.message)
      setTimeout(() => navigate('/mypage'), 3000)
    } catch (err: any) {
      console.error('❌ 登録失敗:', err)
      setError('ユーザー登録に失敗しました')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className={styles.registerContainer}>
      <h2 className={styles.registerTitle}>ユーザー登録</h2>

      {success && <div className={styles.successMessage}>{success}</div>}
      {error && <div className={styles.errorMessage}>{error}</div>}

      <form onSubmit={handleRegister}>
        <div className={styles.formGroup}>
          <input
            type="email"
            id="email"
            placeholder=" "
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className={styles.input}
            required
          />
          <label htmlFor="email" className={styles.label}>メールアドレス</label>
        </div>

        <div className={styles.formGroup}>
          <input
            type="text"
            id="userName"
            placeholder=" "
            value={userName}
            onChange={(e) => setUserName(e.target.value)}
            className={styles.input}
            required
          />
          <label htmlFor="userName" className={styles.label}>ユーザー名</label>
        </div>

        <div className={styles.formGroup}>
          <input
            type="password"
            id="password"
            placeholder=" "
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className={styles.input}
            required
          />
          <label htmlFor="password" className={styles.label}>パスワード</label>
        </div>

        <button
          type="submit"
          className={styles.registerButton}
          disabled={isSubmitting}
        >
          {isSubmitting ? '処理中...' : '登録する'}
        </button>

        <div className={styles.loginLink}>
          <Link to="/login">すでにアカウントをお持ちの方はこちら</Link>
        </div>
      </form>
    </div>
  )
}

export default RegisterPage