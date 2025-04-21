import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import axios from '@/lib/axios'

function VerificationSuccessPage() {
  const { token } = useParams<{ token: string }>()
  const [verified, setVerified] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  
  useEffect(() => {
    const verifyEmail = async () => {
      if (!token) {
        setError('無効な認証リンクです')
        setLoading(false)
        return
      }
      
      try {
        await axios.get(`/auth/verify-email/${token}`)
        setVerified(true)
        setLoading(false)
      } catch (err: any) {
        console.error('メール認証エラー:', err)
        setError('メール認証に失敗しました。リンクが無効または期限切れの可能性があります。')
        setLoading(false)
      }
    }
    
    verifyEmail()
  }, [token])
  
  if (loading) {
    return (
      <div className="max-w-md mx-auto p-6 bg-white rounded shadow-md mt-10 text-center">
        <h2 className="text-2xl font-bold mb-6">メール認証中...</h2>
        <p>しばらくお待ちください。</p>
      </div>
    )
  }
  
  return (
    <div className="max-w-md mx-auto p-6 bg-white rounded shadow-md mt-10 text-center">
      <h2 className="text-2xl font-bold mb-6">メール認証</h2>
      
      {verified ? (
        <div>
          <div className="bg-green-100 border-l-4 border-green-500 text-green-700 p-4 mb-4 text-left" role="alert">
            <p>メールアドレスの認証が完了しました。</p>
          </div>
          
          <p className="mb-6">
            アカウントが有効化されました。ログインしてサービスをご利用ください。
          </p>
          
          <Link 
            to="/login" 
            className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline inline-block"
          >
            ログインページへ
          </Link>
        </div>
      ) : (
        <div>
          <div className="bg-red-100 border-l-4 border-red-500 text-red-700 p-4 mb-4 text-left" role="alert">
            <p>{error}</p>
          </div>
          
          <p className="mb-6">
            メール認証に問題が発生しました。
            お手数ですが、再度登録を行うか、サポートにお問い合わせください。
          </p>
          
          <div className="flex flex-col space-y-4">
            <Link 
              to="/register" 
              className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline inline-block"
            >
              新規登録ページへ
            </Link>
            
            <Link 
              to="/login" 
              className="text-blue-500 hover:text-blue-700"
            >
              ログインページへ戻る
            </Link>
          </div>
        </div>
      )}
    </div>
  )
}

export default VerificationSuccessPage 