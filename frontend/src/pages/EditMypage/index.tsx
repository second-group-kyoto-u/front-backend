import { useEffect, useState } from 'react'
import { fetchProtected } from '@/api/auth/protected'
import { useAuth } from '@/hooks/useAuth'
import { useNavigate } from 'react-router-dom'
import styles from './EditMypage.module.css'

interface UserData {
  id: string;
  user_name: string;
  profile_message: string;
  profile_image_url: string;
  age: number;
  location: string;
  gender: string;
}

interface MypageResponse {
  user: UserData;
  message: string;
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
        // （特にuserオブジェクトにage, location, genderが不足しています）
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

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (userData) {
      console.log('送信するデータ:', userData)
      // ここで updateProfile(userData) を呼び出す
      alert('プロフィールを更新しました！（仮）')
      navigate('/mypage')
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
              <label>年齢</label>
              <input
                type="number"
                name="age"
                value={userData.age}
                onChange={handleChange}
              />
            </div>

            <div className={styles.formGroup}>
              <label>居住地</label>
              <input
                type="text"
                name="location"
                value={userData.location}
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
                <option value="男性">男性</option>
                <option value="女性">女性</option>
                <option value="その他">その他</option>
              </select>
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