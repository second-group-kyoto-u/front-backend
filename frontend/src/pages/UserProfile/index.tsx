// 他のユーザーのプロフィール表示画面
import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useAuth } from '@/hooks/useAuth'
import styles from './UserProfile.module.css'
import axios from '@/lib/axios'

interface UserData {
  id: string;
  user_name: string;
  profile_message: string;
  user_image_url: string;
  email_verified: boolean;
  is_certificated: boolean;
}

interface FollowStatus {
  is_following: boolean;
  is_followed_by: boolean;
  relationship_id: string | null;
  relationship_status: string | null;
}

interface UserProfileResponse {
  user: UserData;
  joined_events_count: number;
  favorite_tags: string[];
  created_events: any[];
  follow_status: FollowStatus;
  is_authenticated: boolean;
}

function UserProfilePage() {
  const { userId } = useParams<{ userId: string }>()
  const { isAuthenticated } = useAuth()
  const [userData, setUserData] = useState<UserData | null>(null)
  const [favoriteTags, setFavoriteTags] = useState<string[]>([])
  const [createdEvents, setCreatedEvents] = useState<any[]>([])
  const [followStatus, setFollowStatus] = useState<FollowStatus>({
    is_following: false,
    is_followed_by: false,
    relationship_id: null,
    relationship_status: null
  })
  const [loading, setLoading] = useState(true)
  const [followLoading, setFollowLoading] = useState(false)
  const [error, setError] = useState('')
  const navigate = useNavigate()

  useEffect(() => {
    if (!userId) return

    const fetchUserProfile = async () => {
      setLoading(true)
      try {
        // ユーザープロフィールAPIを呼び出し
        const response = await axios.get(`/user/${userId}/profile`)
        const data = response.data as UserProfileResponse
        
        setUserData(data.user)
        setFavoriteTags(data.favorite_tags || [])
        setCreatedEvents(data.created_events || [])
        setFollowStatus(data.follow_status || {
          is_following: false,
          is_followed_by: false,
          relationship_id: null,
          relationship_status: null
        })
      } catch (error) {
        console.error('ユーザープロフィール取得エラー:', error)
        setError('プロフィール情報の取得に失敗しました')
      } finally {
        setLoading(false)
      }
    }

    fetchUserProfile()
  }, [userId])

  // フォロー/フォロー解除の処理
  const handleFollowToggle = async () => {
    if (!isAuthenticated || !userId) {
      // 未認証の場合はログインページへリダイレクト
      navigate('/login', { 
        state: { 
          from: `/user/${userId}`,
          message: 'フォローするにはログインが必要です'
        } 
      })
      return
    }

    setFollowLoading(true)
    try {
      if (followStatus.is_following) {
        // フォロー解除
        const response = await axios.post(`/user/${userId}/unfollow`)
        console.log('フォロー解除成功:', response.data)
        
        // フォロー状態を更新
        setFollowStatus({
          ...followStatus,
          is_following: false,
          relationship_id: null,
          relationship_status: null
        })
      } else {
        // フォロー
        const response = await axios.post(`/user/${userId}/follow`)
        console.log('フォロー成功:', response.data)
        
        // フォロー状態を更新
        setFollowStatus({
          ...followStatus,
          is_following: true,
          relationship_id: response.data.relationship.id,
          relationship_status: response.data.relationship.status
        })
      }
    } catch (error) {
      console.error('フォロー処理エラー:', error)
      setError('フォロー処理中にエラーが発生しました')
    } finally {
      setFollowLoading(false)
    }
  }

  // 画像URLを処理する関数
  const processImageUrl = (url: string | null): string => {
    if (!url) return 'https://via.placeholder.com/200x200?text=No+Image';
    
    // MinIOのURLを修正（内部ネットワークのURLを外部アクセス可能なURLに変換）
    if (url.includes(':9000/')) {
      // MinIOのURLの場合、nginxプロキシ経由に変換
      const urlParts = url.split(':9000/');
      if (urlParts.length === 2) {
        const newUrl = `http://${window.location.hostname}/minio/${urlParts[1]}`;
        return newUrl;
      }
    }
    
    return url;
  };

  // フォローボタンの表示テキストを取得
  const getFollowButtonText = () => {
    if (followLoading) return '処理中...'
    if (followStatus.is_following) {
      return followStatus.relationship_status === 'accepted' ? 'フォロー中' : 'リクエスト中'
    }
    return 'フォローする'
  }

  const handleBack = () => {
    navigate(-1 as any) // 前のページに戻る
  }

  if (loading) {
    return (
      <div className={styles.pageBackground}>
        <div className={styles.container}>
          <p>読み込み中...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className={styles.pageBackground}>
        <div className={styles.container}>
          <p className={styles.errorMessage}>{error}</p>
          <button onClick={handleBack} className={styles.backButton}>
            戻る
          </button>
        </div>
      </div>
    )
  }

  if (!userData) {
    return (
      <div className={styles.pageBackground}>
        <div className={styles.container}>
          <p>ユーザーが見つかりません</p>
          <button onClick={handleBack} className={styles.backButton}>
            戻る
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className={styles.pageBackground}>
      <div className={styles.container}>
        <button onClick={handleBack} className={styles.backButton}>
          ← 戻る
        </button>

        <div className={styles.profileHeader}>
          {userData.user_image_url && (
            <img 
              src={processImageUrl(userData.user_image_url)} 
              alt="プロフィール画像" 
              className={styles.profileImage} 
            />
          )}
          <h2 className={styles.userName}>{userData.user_name}</h2>
          {userData.is_certificated && (
            <span className={styles.verified}>✓ 認証済み</span>
          )}
          <p className={styles.profileMessage}>{userData.profile_message || "自己紹介はありません"}</p>

          {/* フォローボタン（自分以外のユーザープロフィールの場合のみ表示） */}
          {isAuthenticated && (
            <div className={styles.followSection}>
              <button 
                className={`${styles.followButton} ${followStatus.is_following ? styles.following : ''}`}
                onClick={handleFollowToggle}
                disabled={followLoading}
              >
                {getFollowButtonText()}
              </button>
              
              {followStatus.is_followed_by && (
                <span className={styles.followedByBadge}>
                  あなたをフォローしています
                </span>
              )}
            </div>
          )}
        </div>

        {favoriteTags.length > 0 && (
          <div className={styles.tagsSection}>
            <p className={styles.sectionTitle}>興味のあるタグ</p>
            <div className={styles.tagsList}>
              {favoriteTags.map(tag => (
                <span key={tag} className={styles.tag}>{tag}</span>
              ))}
            </div>
          </div>
        )}

        {createdEvents.length > 0 && (
          <div className={styles.eventsSection}>
            <p className={styles.sectionTitle}>主催イベント</p>
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
          </div>
        )}
      </div>
    </div>
  )
}

export default UserProfilePage 