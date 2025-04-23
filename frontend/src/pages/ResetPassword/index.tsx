import { useState, useEffect } from 'react'
import { resetPassword } from '@/api/auth/password'
import { useParams, Link, useNavigate } from 'react-router-dom'

function ResetPasswordPage() {
  const { token } = useParams<{ token: string }>()
  const navigate = useNavigate()
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  
  useEffect(() => {
    if (!token) {
      setError('無効なリセットリンクです')
    }
  }, [token])
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!token) {
      setError('無効なリセットリンクです')
      return
    }
    
    if (!password || !confirmPassword) {
      setError('すべての項目を入力してください')
      return
    }
    
    if (password !== confirmPassword) {
      setError('パスワードが一致しません')
      return
    }
    
    setIsSubmitting(true)
    setError('')
    
    try {
      const data = await resetPassword(token, { password })
      setSuccess(data.message)
      
      // 3秒後にログインページにリダイレクト
      setTimeout(() => {
        navigate('/login')
      }, 3000)
    } catch (err: any) {
      console.error("❌ パスワードリセット失敗:", err)
      setError('パスワードリセットに失敗しました。リンクが無効または期限切れの可能性があります。')
    } finally {
      setIsSubmitting(false)
    }
  }
  
  return (
    <div className="max-w-md mx-auto p-6 bg-white rounded shadow-md mt-10">
      <h2 className="text-2xl font-bold mb-6 text-center">パスワードリセット</h2>
      
      {success ? (
        <div className="text-center">
          <div className="bg-green-100 border-l-4 border-green-500 text-green-700 p-4 mb-4 text-left" role="alert">
            <p>{success}</p>
          </div>
          
          <p className="mb-4">
            新しいパスワードが設定されました。3秒後にログインページに移動します。
          </p>
          
          <Link 
            to="/login" 
            className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline inline-block"
          >
            ログインページへ
          </Link>
        </div>
      ) : (
        <>
          {error && (
            <div className="bg-red-100 border-l-4 border-red-500 text-red-700 p-4 mb-4" role="alert">
              <p>{error}</p>
            </div>
          )}
          
          <form onSubmit={handleSubmit}>
            <div className="mb-4">
              <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="password">
                新しいパスワード
              </label>
              <input
                id="password"
                type="password"
                className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
                placeholder="新しいパスワード"
                value={password}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setPassword(e.target.value)}
                required
              />
            </div>
            
            <div className="mb-6">
              <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="confirmPassword">
                新しいパスワード（確認）
              </label>
              <input
                id="confirmPassword"
                type="password"
                className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
                placeholder="新しいパスワード（確認）"
                value={confirmPassword}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setConfirmPassword(e.target.value)}
                required
              />
            </div>
            
            <div className="flex items-center justify-between">
              <button
                className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline w-full"
                type="submit"
                disabled={isSubmitting}
              >
                {isSubmitting ? '処理中...' : 'パスワードを更新'}
              </button>
            </div>
            
            <div className="mt-4 text-center">
              <Link to="/login" className="text-blue-500 hover:text-blue-700">
                ログインページへ戻る
              </Link>
            </div>
          </form>
        </>
      )}
    </div>
  )
}

export default ResetPasswordPage 