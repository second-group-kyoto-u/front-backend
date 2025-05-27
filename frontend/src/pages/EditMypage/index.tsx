import { useEffect, useState } from 'react'
import { fetchProtected, updateProfile } from '@/api/auth/protected'
import { getTags } from '@/api/tag'
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
}

function EditMypage() {
  const { token, logout } = useAuth()
  const [userData, setUserData] = useState<UserData | null>(null)
  const [message, setMessage] = useState('')
  const [selectedTags, setSelectedTags] = useState<{ value: string; label: string }[]>([])
  const [allTagOptions, setAllTagOptions] = useState<{ value: string; label: string }[]>([])
  const [isLoading, setIsLoading] = useState(true) // ローディング状態を追加
  const navigate = useNavigate()

  useEffect(() => {
    if (!token) {
      logout()
      navigate('/login')
      return
    }

    const fetchData = async () => {
      try {
        setIsLoading(true)
        
        // ユーザーデータとタグデータを並行で取得
        const [userRes, tagsRes] = await Promise.all([
          fetchProtected(),
          getTags()
        ])
        
        const responseData = userRes as any // 実際の構造がインターフェースと一致しないため型を修正
        
        // レスポンスデータからユーザー情報を抽出し、favorite_tagsを追加
        const userDataWithTags = {
          ...responseData.user,
          favorite_tags: responseData.favorite_tags || []
        }
        
        setUserData(userDataWithTags)
        setMessage(responseData.message)

        // 全てのタグオプションを設定
        const tagOptions = tagsRes.map(tag => ({
          value: tag.tag_name,
          label: tag.tag_name
        }))
        setAllTagOptions(tagOptions)

        // ユーザーが選択済みのタグを設定 - ルートレベルからfavorite_tagsを取得
        if (responseData.favorite_tags && responseData.favorite_tags.length > 0) {
          const initialSelected = responseData.favorite_tags.map(tag => ({
            value: tag,
            label: tag
          }))
          console.log('初期選択タグを設定:', initialSelected) // デバッグ用
          setSelectedTags(initialSelected)
        }
        
      } catch (err) {
        console.error("❌ 初期データ取得エラー:", err)
        logout()
        navigate('/login')
      } finally {
        setIsLoading(false)
      }
    }

    fetchData()
  }, [token, logout, navigate])

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
        favorite_tags: selectedTags.map(tag => tag.value)
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

  // ローディング中の表示
  if (isLoading) {
    return (
      <div className={styles.pageBackground}>
        <div className={styles.container}>
          <p>読み込み中...</p>
        </div>
      </div>
    )
  }

  return (
    <div className={styles.pageBackground}>
      <div className={styles.container}>
        <div className={styles.headerRow}>
          <button
            className={styles.backButton}
            onClick={() => navigate(-1)}
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
                options={allTagOptions}
                value={selectedTags}
                onChange={(selected) => {
                  console.log('タグ選択変更:', selected) // デバッグ用
                  setSelectedTags(selected ? [...selected] : [])
                }}
                placeholder="タグを選択または入力してください"
                className={styles.tagSelect}
                isClearable
                isSearchable
                styles={{
                  option: (provided) => ({
                    ...provided,
                    color: '#5c4033',
                  }),
                  multiValueLabel: (provided) => ({
                    ...provided,
                    color: '#5c4033',
                  }),
                  input: (provided) => ({
                    ...provided,
                    color: '#5c4033',
                  }),
                  placeholder: (provided) => ({
                    ...provided,
                    color: '#5c4033',
                  }),
                }}
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