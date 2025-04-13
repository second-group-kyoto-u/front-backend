// 認証済みユーザー画面
import { useEffect, useState } from 'react'
import { fetchProtected } from '@/api/auth/protected'
import { useAuth } from '@/hooks/useAuth'
import { useNavigate } from 'react-router-dom'
// import styles from './Mypage.module.css' // TODO: スタイルを将来的にまとめる

function Mypage() {
  const { token, logout } = useAuth()
  const [message, setMessage] = useState('')
  const navigate = useNavigate()

  useEffect(() => {
    // token が null の間は何もしない（useAuth の setToken を待つ）
    if (token === null) return
  
    if (!token) {
      console.warn("⚠️ トークンが存在しません")
      setMessage('トークンがありません')
      return
    }
  
    fetchProtected(token)
      .then((res) => {
        console.log("✅ /mypage 成功:", res)
        setMessage(res.message)
      })  
      .catch((err) => {
        console.error("❌ /mypage エラー:", err.response ?? err)
        setMessage('認証エラー')
        logout()
        navigate('/login')
      })
  }, [token])

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <div className="p-4">
      <h2 className="text-xl font-bold mb-4">マイページ</h2>
      <p>{message}</p>
      <button onClick={handleLogout} className="mt-4 px-4 py-2 border rounded">
        ログアウト
      </button>
    </div>
  )
}

export default Mypage
