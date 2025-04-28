import { useState } from 'react'
import { registerUser } from '@/api/auth/register'
import { useNavigate, Link } from 'react-router-dom'

function RegisterPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [userName, setUserName] = useState('')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const navigate = useNavigate()

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault()
    
    // 入力検証
    if (!email || !password || !userName) {
      setError('すべての項目を入力してください')
      return
    }
    
    if (password !== confirmPassword) {
      setError('パスワードが一致しません')
      return
    }

    if (password.length < 6 || password.length > 32) {
      setError('パスワードは6文字以上32文字以下で入力してください')
      return
    }

    setIsSubmitting(true)
    setError('')
    setSuccess('')
    
    try {
      const data = await registerUser({ email, password, userName })
      console.log("✅ 登録成功:", data)
      
      // トークンを保存
      localStorage.setItem('token', data.token)
      
      // 成功メッセージを表示
      setSuccess(data.message)
      
      // 3秒後にマイページに遷移
      setTimeout(() => {
        navigate('/mypage')
      }, 3000)
    } catch (err: any) {
      console.error("❌ 登録失敗:", err)
      setError('ユーザー登録に失敗しました')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#f9f7f1]">
      <div className="max-w-md w-full p-8 bg-white rounded shadow-md">
        <h2 className="text-2xl font-bold mb-6 text-center text-[#5c4033]">新規登録</h2>

        {success && (
          <div className="bg-green-100 border-l-4 border-green-500 text-green-700 p-4 mb-4" role="alert">
            <p>{success}</p>
          </div>
        )}

        {error && (
          <div className="bg-red-100 border-l-4 border-red-500 text-red-700 p-4 mb-4" role="alert">
            <p>{error}</p>
          </div>
        )}

        <form onSubmit={handleRegister}>
          <div className="mb-4">
            <label className="block text-[#5c4033] text-sm font-bold mb-2" htmlFor="email">
              メールアドレス
            </label>
            <input
              id="email"
              type="email"
              className="shadow appearance-none border border-[#cccccc] rounded-md w-full py-2 px-3 text-[#cccccc] leading-tight focus:outline-none focus:shadow-outline"
              placeholder="メールアドレス"
              value={email}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setEmail(e.target.value)}
              required
            />
          </div>

          <div className="mb-4">
            <label className="block text-[#5c4033] text-sm font-bold mb-2" htmlFor="userName">
              ユーザー名
            </label>
            <input
              id="userName"
              type="text"
              className="shadow appearance-none border border-[#cccccc] rounded-md w-full py-2 px-3 text-[#cccccc] leading-tight focus:outline-none focus:shadow-outline"
              placeholder="ユーザー名"
              value={userName}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setUserName(e.target.value)}
              required
            />
          </div>

          <div className="mb-4">
            <label className="block text-[#5c4033] text-sm font-bold mb-2" htmlFor="password">
              パスワード
            </label>
            <input
              id="password"
              type="password"
              className="shadow appearance-none border border-[#cccccc] rounded-md w-full py-2 px-3 text-[#cccccc] leading-tight focus:outline-none focus:shadow-outline"
              placeholder="パスワード"
              value={password}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setPassword(e.target.value)}
              required
            />
            <p className="text-xs text-[#5c4033] mt-1">6文字以上32文字以下の英数字で入力</p>
          </div>

          <div className="mb-6">
            <label className="block text-[#5c4033] text-sm font-bold mb-2" htmlFor="confirmPassword">
              パスワード（確認用）
            </label>
            <input
              id="confirmPassword"
              type="password"
              className="shadow appearance-none border border-[#cccccc] rounded-md w-full py-2 px-3 text-[#cccccc] leading-tight focus:outline-none focus:shadow-outline"
              placeholder="パスワード再入力"
              value={confirmPassword}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setConfirmPassword(e.target.value)}
              required
            />
          </div>

          <div className="flex items-center justify-between">
            <button
              type="submit"
              disabled={isSubmitting}
              className="bg-[#5c4033] hover:bg-[#3e2b22] text-white font-bold py-2 px-4 rounded-full focus:outline-none focus:shadow-outline w-full"
            >
              {isSubmitting ? '処理中...' : '登録する'}
            </button>
          </div>

          <div className="mt-4 text-center">
            <Link to="/login" className="text-[#5c4033] hover:underline">
              すでにアカウントをお持ちの方はこちら
            </Link>
          </div>
        </form>
      </div>
    </div>
  )
}

export default RegisterPage 