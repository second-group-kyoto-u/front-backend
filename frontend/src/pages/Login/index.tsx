// ログインフォーム
import { useState } from 'react'
import { loginUser } from '@/api/auth/login'
import { useNavigate } from 'react-router-dom'

function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const navigate = useNavigate()

  const handleLogin = async () => {
    try {
      const data = await loginUser({ email, password })
      console.log("✅ ログイン成功:", data)
      localStorage.setItem('token', data.token)
      navigate('/mypage')
    } catch (err: any) {
      console.error("❌ ログイン失敗:", err.response ?? err)
      setError('ログインできませんでした')
    }
  }

  return (
    <div className="p-4">
      <h2>ログイン</h2>
      <input
        type="email"
        placeholder="メールアドレス"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
      />
      <input
        type="password"
        placeholder="パスワード"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
      />
      <button onClick={handleLogin}>ログイン</button>
      {error && <p>{error}</p>}
    </div>
  )
}

export default LoginPage
