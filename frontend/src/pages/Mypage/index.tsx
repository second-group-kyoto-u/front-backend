// 認証済みユーザー画面
import { useEffect, useState } from 'react'
import { fetchProtected } from '@/api/auth/protected'
import { useAuth } from '@/hooks/useAuth'
import { useNavigate } from 'react-router-dom'
import styles from './Mypage.module.css'

interface UserData {
  id: string;
  user_name: string;
  profile_message: string;
  profile_image_url: string;
  age: number;
  location: string;
  gender: string;
  is_certificated: boolean;
}

interface EventData {
  id: string;
  title: string;
  description: string;
}

interface MypageResponse {
  user: UserData;
  joined_events_count: number;
  favorite_tags: string[];
  created_events: EventData[];
  message: string;
}

function Mypage() {
  const { token, logout } = useAuth()
  const [userData, setUserData] = useState<UserData | null>(null)
  const [favoriteTags, setFavoriteTags] = useState<string[]>([])
  const [createdEvents, setCreatedEvents] = useState<EventData[]>([])
  const [message, setMessage] = useState('')
  const navigate = useNavigate()

  useEffect(() => {
    if (!token) {
      logout()
      navigate('/login')
      return
    }
  
    fetchProtected()
      .then((res) => {
        // 🔵 【注意】現在のfetchProtected()の戻り値型(ProtectedResponse)は、
        // 期待するデータ型(MypageResponse)と一致していません。
        // （特にcreated_eventsフィールドが存在しないため、型エラーになります）
        // 仮対応として型アサーション(as MypageResponse)を使用していますが、
        // 将来的にはバックエンドのレスポンス仕様を確認・統一する必要があります。
        const data = res as MypageResponse
        console.log('取得的ユーザーデータ:', data)
        setUserData(data.user)
        setFavoriteTags(data.favorite_tags)
        setCreatedEvents(data.created_events)
        setMessage(data.message)
      })
      .catch((err) => {
        console.error("❌ 認証エラー:", err)
        logout()
        navigate('/login')
      })
  }, [token])
  

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const handleShareProfile = () => {
    if (!userData) return
  
    const publicProfileUrl = `${window.location.origin}/user/${userData.id}`
    navigator.clipboard.writeText(publicProfileUrl)
      .then(() => alert('シェアリンクをコピーしました'))
      .catch(() => alert('コピーに失敗しました'))
  }

  return (
    <div className={styles.pageBackground}>
      <div className={styles.container}>
        {message && <p className={styles.message}>{message}</p>}
        {userData && (
          <>
            <div className={styles.profileHeader}>
              {userData.profile_image_url && (
                <img src={userData.profile_image_url} alt="プロフィール画像" className={styles.profileImage} />
              )}
              <h2 className={styles.userName}>{userData.user_name}</h2>
              {userData.is_certificated && (
                <span className={styles.verified}>✓ 認証済み</span>
              )}
              <p className={styles.profileMessage}>{userData.profile_message || "自己紹介未設定"}</p>

              <div className={styles.buttonGroup}>
                <button onClick={() => navigate('/edit-mypage')} className={styles.editButton}>
                  プロフィールを編集
                </button>
                <button onClick={handleShareProfile} className={styles.shareButton}>
                  プロフィールをシェア
                </button>
              </div>
            </div>

            <div className={styles.userInfo}>
              <p><strong>年齢:</strong> {userData.age}歳</p>
              <p><strong>居住地:</strong> {userData.location}</p>
              <p><strong>性別:</strong> {userData.gender === 'male' ? '男' : userData.gender === 'female' ? '女' : '未設定'}</p>
            </div>

            <div className={styles.tagsSection}>
              <p className={styles.sectionTitle}>旅のキーワード</p>
              <div className={styles.tagsList}>
                {favoriteTags.map(tag => (
                  <span key={tag} className={styles.tag}>{tag}</span>
                ))}
              </div>
            </div>

            <div className={styles.eventsSection}>
              <p className={styles.sectionTitle}>主催イベント</p>
              {createdEvents.length > 0 ? (
                <div className={styles.eventList}>
                  {createdEvents.map(event => (
                    <div 
                      key={event.id} 
                      className={styles.eventCard}
                      onClick={() => navigate(`/event/${event.id}`)}
                    >
                      <h3 className={styles.eventTitle}>{event.title}</h3>
                      <p className={styles.eventDescription}>{event.description}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <p>まだ主催したイベントがありません</p>
              )}
            </div>


            <button onClick={handleLogout} className={styles.logoutButton}>
              ログアウト
            </button>
          </>
        )}

        {!userData && <p>読み込み中...</p>}
      </div>
    </div>
  )
}

export default Mypage