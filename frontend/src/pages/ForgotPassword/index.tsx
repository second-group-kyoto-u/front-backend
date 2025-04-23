import { useState } from 'react'
import { forgotPassword } from '@/api/auth/password'
import { Link } from 'react-router-dom'

function ForgotPasswordPage() {
  const [email, setEmail] = useState('')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!email) {
      setError('メールアドレスを入力してください')
      return
    }
    
    setIsSubmitting(true)
    setError('')
    
    try {
      const data = await forgotPassword({ email })
      setSuccess(data.message)
    } catch (err: any) {
      console.error("❌ リセット申請失敗:", err)
      setError('パスワードリセット申請に失敗しました')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="max-w-md mx-auto p-6 bg-white rounded shadow-md mt-10">
      <h2 className="text-2xl font-bold mb-6 text-center">パスワードをお忘れの方</h2>
      
      {success ? (
        <div className="text-center">
          <div className="bg-green-100 border-l-4 border-green-500 text-green-700 p-4 mb-4 text-left" role="alert">
            <p>{success}</p>
          </div>
          
          <p className="mb-4">
            メールに記載されたリンクからパスワードリセットを行ってください。
          </p>
          
          <Link 
            to="/login" 
            className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline inline-block"
          >
            ログイン画面に戻る
          </Link>
        </div>
      ) : (
        <>
          <p className="mb-4">
            登録済みのメールアドレスを入力してください。パスワードリセット用のリンクをメールでお送りします。
          </p>
          
          {error && (
            <div className="bg-red-100 border-l-4 border-red-500 text-red-700 p-4 mb-4" role="alert">
              <p>{error}</p>
            </div>
          )}
          
          <form onSubmit={handleSubmit}>
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
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setEmail(e.target.value)}
                required
              />
            </div>
            
            <div className="flex items-center justify-between">
              <button
                className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline w-full"
                type="submit"
                disabled={isSubmitting}
              >
                {isSubmitting ? '送信中...' : 'パスワードリセット申請'}
              </button>
            </div>
            
            <div className="mt-4 text-center">
              <Link to="/login" className="text-blue-500 hover:text-blue-700">
                ログイン画面に戻る
              </Link>
            </div>
          </form>
        </>
      )}
    </div>
  )
}

export default ForgotPasswordPage 