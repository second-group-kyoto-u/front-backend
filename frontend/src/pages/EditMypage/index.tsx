import { useEffect, useState } from 'react'
import { fetchProtected, updateProfile } from '@/api/auth/protected'
import { useAuth } from '@/hooks/useAuth'
import { useNavigate } from 'react-router-dom'
import styles from './EditMypage.module.css'

interface UserData {
  id: string;
  user_name: string;
  profile_message: string;
  profile_image_url: string;
  birthdate: string;
  living_place: string;
  gender: string;
}

interface MypageResponse {
  user: UserData;
  message: string;
}

interface UpdateUserData {
  user_name: string;
  profile_message: string;
  birthdate: string;
  living_place: string;
  gender: string;
}



function EditMypage() {
  const { token, logout } = useAuth()
  const [userData, setUserData] = useState<UserData | null>(null)
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
        // 仮対応として型アサーション(as MypageResponse)を使用していますが、
        // 将来的にはバックエンドのレスポンス仕様を確認・統一する必要があります。
        const data = res as MypageResponse
        setUserData(data.user)
        setMessage(data.message)
      })
      .catch((err) => {
        console.error("❌ 認証エラー:", err)
        logout()
        navigate('/login')
      })
  }, [token])
  

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    if (!userData) return
    const { name, value } = e.target
    setUserData({ ...userData, [name]: value })
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (userData) {
      const updateData: UpdateUserData = {
        user_name: userData.user_name,
        profile_message: userData.profile_message,
        birthdate: new Date(userData.birthdate).toISOString().slice(0, 10),
        living_place: userData.living_place,
        gender: userData.gender,
      }
      try {
        await updateProfile(updateData)
        alert('プロフィールを更新しました！')
        navigate('/mypage')
      } catch (err) {
        console.error('プロフィール更新エラー:', err)
        alert('更新に失敗しました。もう一度お試しください。')
      }
    } else {
      alert('すべての項目を入力してください。')
    }
  }


  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <div className={styles.pageBackground}>
      <div className={styles.container}>
        <div className={styles.headerRow}>
          <button
            className={styles.backButton}
            onClick={() => navigate('/mypage')}
          >
            ←
          </button>
          <h2 className={styles.title}>プロフィール編集</h2>
        </div>

        {message && <p className={styles.message}>{message}</p>}

        {userData && (
          <form onSubmit={handleSubmit} className={styles.form}>
            <div className={styles.formGroup}>
              <label>ユーザー名</label>
              <input
                type="text"
                name="user_name"
                value={userData.user_name}
                onChange={handleChange}
              />
            </div>

            <div className={styles.formGroup}>
              <label>自己紹介</label>
              <textarea
                name="profile_message"
                value={userData.profile_message}
                onChange={handleChange}
                rows={4}
              />
            </div>

            <div className={styles.formGroup}>
              <label>誕生日</label>
              <input
                type="date"
                name="birthdate"
                value={
                  userData.birthdate
                    ? new Date(userData.birthdate).toISOString().slice(0, 10)
                    : ''
                }
                onChange={handleChange}
              />
            </div>

            <div className={styles.formGroup}>
              <label>居住地</label>
              <input
                type="text"
                name="living_place"
                value={userData.living_place}
                onChange={handleChange}
              />
            </div>

            <div className={styles.formGroup}>
              <label>性別</label>
              <select
                name="gender"
                value={userData.gender}
                onChange={handleChange}
              >
                <option value="">選択してください</option>
                <option value="male">男性</option>
                <option value="female">女性</option>
                <option value="other">その他</option>
              </select>
            </div>

            <div className={styles.formGroup}>
              <label>旅のキーワード</label>
              <input
                type="text"
                name="tag"
                value={userData.tag}
                onChange={handleChange}
              />
            </div>

            <button type="submit" className={styles.submitButton}>
              プロフィールを更新
            </button>
          </form>
        )}

        <button onClick={handleLogout} className={styles.logoutButton}>
          ログアウト
        </button>
      </div>
    </div>
  )
}

export default EditMypage