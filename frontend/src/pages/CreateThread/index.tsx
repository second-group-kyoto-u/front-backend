import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { createThread } from '@/api/thread'
import { useAuth } from '@/hooks/useAuth'
import styles from './CreateThread.module.css'

function CreateThreadPage() {
  const [tag, setTag] = useState('')
  const [age, setAge] = useState<'all' | 'teens' | '20s' | '30s' | '40s' | '50s' | '60s+'>('all')
  const [gender, setGender] = useState<'all' | 'male' | 'female' | 'other'>('all')
  const [followersOnly, setFollowersOnly] = useState(false)
  const [content, setContent] = useState('')
  const [error, setError] = useState('')
  const { token } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!content.trim()) {
      setError('内容を入力してください')
      return
    }

    try {
      await createThread({
        tag,
        content,
        visibility: {
          age,
          gender,
          followersOnly,
        },
      }, token!)
      navigate('/threads')
    } catch (err: any) {
      setError('スレッドの作成に失敗しました')
    }
  }

  return (
    <div className={styles.pageBackground}>
      <div className={styles.container}>
        <h2 className={styles.title}>スレッド作成</h2>

        {error && <p className={styles.error}>{error}</p>}

        <form onSubmit={handleSubmit} className={styles.form}>
          <div className={styles.formGroup}>
            <input
              type="text"
              value={tag}
              onChange={(e) => setTag(e.target.value)}
              placeholder="種類（タグ）"
            />
          </div>
          
          <div className={styles.visibilitySection}>
            <label className={styles.sectionLabel}>公開範囲</label>

            {/* ユーザー範囲 */}
            <div className={styles.formGroup}>
              <label className={styles.subLabel}>ユーザー</label>
              <label>
                <input
                  type="checkbox"
                  checked={followersOnly}
                  onChange={(e) => setFollowersOnly(e.target.checked)}
                />
                フォロワーのみ
              </label>
            </div>

            {/* 性別 */}
            <div className={styles.formGroup}>
              <label className={styles.subLabel}>性別</label>
              <select value={gender} onChange={(e) => setGender(e.target.value as any)}>
                <option value="all">すべての性別</option>
                <option value="male">男性</option>
                <option value="female">女性</option>
                <option value="other">その他</option>
              </select>
            </div>

            {/* 年齢 */}
            <div className={styles.formGroup}>
              <label className={styles.subLabel}>年齢</label>
              <select value={age} onChange={(e) => setAge(e.target.value as any)}>
                <option value="all">すべての年齢</option>
                <option value="teens">10代</option>
                <option value="20s">20代</option>
                <option value="30s">30代</option>
                <option value="40s">40代</option>
                <option value="50s">50代</option>
                <option value="60s+">60代以上</option>
              </select>
            </div>
          </div>

          <div className={styles.formGroup}>
            <label>内容</label>
            <textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              rows={4}
              placeholder="いまどうしてる？"
              required
            />
          </div>

          <button type="submit" className={styles.submitButton}>
            投稿する
          </button>
        </form>
      </div>
    </div>
  )
}

export default CreateThreadPage