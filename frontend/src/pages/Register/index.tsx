import { useState } from 'react'
import { registerUser } from '@/api/auth/register'
import { useNavigate, Link } from 'react-router-dom'

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
    
    // 入力検証
    if (!email || !password || !userName) {
      setError('すべての項目を入力してください')
      return
    }
    
    setIsSubmitting(true)
    setError('')
    
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
    <div className="max-w-md mx-auto p-6 bg-white rounded shadow-md mt-10">
      <h2 className="text-2xl font-bold mb-6 text-center">ユーザー登録</h2>
      
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
          <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="email">
            メールアドレス
          </label>
          <input
            id="email"
            type="email"
            className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
            placeholder="メールアドレス"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </div>
        
        <div className="mb-4">
          <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="userName">
            ユーザー名
          </label>
          <input
            id="userName"
            type="text"
            className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
            placeholder="ユーザー名"
            value={userName}
            onChange={(e) => setUserName(e.target.value)}
            required
          />
        </div>
        
        <div className="mb-6">
          <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="password">
            パスワード
          </label>
          <input
            id="password"
            type="password"
            className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
            placeholder="パスワード"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>
        
        <div className="flex items-center justify-between">
          <button
            className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline w-full"
            type="submit"
            disabled={isSubmitting}
          >
            {isSubmitting ? '処理中...' : '登録する'}
          </button>
        </div>
        
        <div className="mt-4 text-center">
          <Link to="/login" className="text-blue-500 hover:text-blue-700">
            すでにアカウントをお持ちの方はこちら
          </Link>
        </div>
      </form>
    </div>
  )
}

export default RegisterPage 