// 認証済みユーザー画面
import { useEffect, useState } from 'react'
import { fetchProtected } from '@/api/auth/protected'
import { useAuth } from '@/hooks/useAuth'
import { useNavigate } from 'react-router-dom'

interface UserData {
  id: string;
  user_name: string;
  profile_message: string;
  profile_image_url: string;
}

interface MypageResponse {
  user: UserData;
  joined_events_count: number;
  favorite_tags: string[];
  message: string;
}

function Mypage() {
  const { token, logout } = useAuth()
  const [userData, setUserData] = useState<UserData | null>(null)
  const [message, setMessage] = useState('')
  const [joinedEventsCount, setJoinedEventsCount] = useState(0)
  const [favoriteTags, setFavoriteTags] = useState<string[]>([])
  const navigate = useNavigate()
  const handleLogout = () => {
    logout()
    navigate('/login')
  }
  

  useEffect(() => {
    console.log('🧪 useEffect 発火: token =', token)
  
    if (token === null) return
  
    if (!token) {
      console.warn("⚠️ トークンが存在しません")
      setMessage('トークンがありません')
      return
    }
  
    fetchProtected()
      .then((res: MypageResponse) => {
        console.log("✅ /protected/mypage 成功:", res)
        setMessage(res.message)
        setUserData(res.user)
        setJoinedEventsCount(res.joined_events_count)
        setFavoriteTags(res.favorite_tags)
      })  
      .catch((err) => {
        console.error("❌ /protected/mypageエラー:", err.response ?? err)
        setMessage('認証エラー')
        logout()
        navigate('/login')
      })
  }, [token])
  
  
  

  return (
    <div className="p-4">
      <h2 className="text-xl font-bold mb-4">マイページ</h2>
      
      {message && <p className="mb-4">{message}</p>}
      
      {userData && (
        <div className="mb-6">
          <div className="flex items-center mb-4">
            {userData.profile_image_url && (
              <img 
                src={userData.profile_image_url} 
                alt="プロフィール画像" 
                className="w-20 h-20 rounded-full object-cover mr-4" 
              />
            )}
            <div>
              <h3 className="text-lg font-semibold">{userData.user_name}</h3>
              <p className="text-gray-600">{userData.profile_message}</p>
            </div>
          </div>
          
          <div className="mb-4">
            <p className="font-medium">参加中のイベント数: {joinedEventsCount}</p>
          </div>
          
          {favoriteTags.length > 0 && (
            <div>
              <p className="font-medium mb-2">お気に入りタグ:</p>
              <div className="flex flex-wrap gap-2">
                {favoriteTags.map(tag => (
                  <span 
                    key={tag} 
                    className="bg-blue-100 text-blue-800 px-2 py-1 rounded-full text-sm"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
      
      <button 
        onClick={handleLogout} 
        className="mt-4 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
      >
        ログアウト
      </button>
    </div>
  )
}

export default Mypage
