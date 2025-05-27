import { useEffect, useState } from 'react'
import { fetchProtected, updateProfile } from '@/api/auth/protected'
import { getTags, Tag } from '@/api/tag'
import { useAuth } from '@/hooks/useAuth'
import { useNavigate } from 'react-router-dom'
import CreatableSelect from 'react-select/creatable'
import styles from './EditMypage.module.css'

interface UserData {
  id: string;
  user_name: string;
  profile_message: string;
  profile_image_url: string;
  birthdate: string;
  living_place: string;
  gender: string;
  favorite_tags: string[];
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
  favorite_tags: string[];
  favorite_tags: string[];
}



function EditMypage() {
  const { token, logout } = useAuth()
  const [userData, setUserData] = useState<UserData | null>(null)
  const [message, setMessage] = useState('')
  const [selectedTags, setSelectedTags] = useState<{ value: string; label: string }[]>([])
  const [allTagOptions, setAllTagOptions] = useState<{ value: string; label: string }[]>([])
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

    getTags()
      .then(setAllTags)
      .catch((err) => {
      console.error("❌ タグ取得エラー:", err)
    })
  }, [token])
  
  // 🔧 現在は手動で空配列、/tags API 実装後にここで取得するようにする
  useEffect(() => {
    // axios.get('/tags')
    //   .then((res) => {
    //     const options = res.data.map((tag: string) => ({ value: tag, label: tag }))
    //     setAllTagOptions(options)
    //   })
    //   .catch((err) => console.error('タグ取得失敗:', err))
  }, [])

  // 初期化：userData.favorite_tags から selectedTags を作成
  useEffect(() => {
    if (userData?.favorite_tags) {
      const initialTags = userData.favorite_tags.map(tag => ({
        value: tag,
        label: tag
      }))
      setSelectedTags(initialTags)
      setAllTagOptions(initialTags)
    }
  }, [userData])

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    if (!userData) return
    const { name, value, multiple, options } = e.target

    if (multiple) {
      const selectedValues = Array.from(options)
        .filter(option => option.selected)
        .map(option => option.value)
      setUserData({ ...userData, [name]: selectedValues })
    } else {
      setUserData({ ...userData, [name]: value })
    }
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
        favorite_tags: selectedTags.map(tag => tag.value)
      }
      try {
        await updateProfile(updateData)
        alert('プロフィールを更新しました！')
        navigate('/mypage')
        window.location.reload()
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
            onClick={() => navigate(-1 as any)}
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
              <CreatableSelect
                isMulti
                options={allTagOptions} // 🔧 将来ここに /tags API の値を使う
                value={selectedTags}
                onChange={(selected: readonly { value: string; label: string }[] | null) =>
                  setSelectedTags(selected ? [...selected] : [])
                }                
                placeholder="タグを選択または入力してください"
                className={styles.tagSelect}
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