import { useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { createThread } from '@/api/thread'
import { useAuth } from '@/hooks/useAuth'
import styles from './CreateThread.module.css'

function CreateThreadPage() {
  const [tag, setTag] = useState('')
  const [followersOnly, setFollowersOnly] = useState(false)
  const [content, setContent] = useState('')
  const [error, setError] = useState('')
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const { token } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!content.trim()) {
      setError('内容を入力してください')
      return
    }

    try {
      const newThread = await createThread({
        tag,
        content,
        visibility: {
          age: 'all',
          gender: 'all',
          followersOnly,
        },
      }, token!)

      navigate('/threads', { state: { newThread } })
    } catch {
      setError('スレッドの作成に失敗しました')
    }
  }

  const handleImageUploadClick = () => {
    fileInputRef.current?.click()
  }

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      setSelectedFile(file)
      const reader = new FileReader()
      reader.onloadend = () => {
        setPreviewUrl(reader.result as string)
      }
      reader.readAsDataURL(file)
    }
  }

  const cancelImage = () => {
    setSelectedFile(null)
    setPreviewUrl(null)
  }

  return (
    <div className={styles.pageBackground}>
      <div className={styles.container}>
        <div className={styles.headerRow}>
          <button
            className={styles.backButton}
            onClick={() => navigate('/threads')}
          >
            ←
          </button>
          <h2 className={styles.title}>スレッド作成</h2>
        </div>

        {error && <p className={styles.error}>{error}</p>}

        <form onSubmit={handleSubmit} className={styles.form}>
          <div className={styles.formGroup}>
            <input
              type="text"
              value={tag}
              onChange={(e) => setTag(e.target.value)}
              placeholder="種類（タグ）"
              list="tag-options"
            />
            <datalist id="tag-options">
              <option value="旅行" />
              <option value="グルメ" />
              <option value="趣味" />
              <option value="友達募集" />
              <option value="相談" />
            </datalist>
          </div>

          <div className={styles.formGroup}>
            <label className={styles.checkboxLabel}>
              <input
                type="checkbox"
                checked={followersOnly}
                onChange={(e) => setFollowersOnly(e.target.checked)}
              />
              フォロワーのみ
            </label>
          </div>

          <div className={styles.formGroup}>
            <label>内容</label>
            <textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              rows={4}
              placeholder="いまどうしてる？"
              required
              className={styles.textarea}
            />
          </div>

          <div className={styles.formGroup}>
            <input
              type="file"
              id="thread-image"
              accept="image/*"
              ref={fileInputRef}
              onChange={handleImageChange}
              className={styles.imageInput}
            />
            <button
              type="button"
              onClick={handleImageUploadClick}
              className={styles.imageUploadButton}
            >
              ＋画像を追加
            </button>
          </div>

          {previewUrl && (
            <div className={styles.imagePreviewWrapper}>
              <img
                src={previewUrl}
                alt="プレビュー"
                className={styles.imagePreview}
                style={{ maxWidth: '100%', height: 'auto', borderRadius: '8px' }}
              />
              <button
                type="button"
                onClick={cancelImage}
                className={styles.cancelPreviewButton}
              >
                × 画像を削除
              </button>
            </div>
          )}

          <button type="submit" className={styles.submitButton}>
            投稿する
          </button>
        </form>
      </div>
    </div>
  )
}

export default CreateThreadPage