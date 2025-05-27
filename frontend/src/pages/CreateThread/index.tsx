import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { createThread } from '@/api/thread'
import { useAuth } from '@/hooks/useAuth'
import styles from './CreateThread.module.css'
import { getTags } from '@/api/tag'

function CreateThreadPage() {
  const [tag, setTag] = useState('')
  const [followersOnly, setFollowersOnly] = useState(false)
  const [title, setTitle] = useState('')
  const [content, setContent] = useState('')
  const [error, setError] = useState('')
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [availableTags, setAvailableTags] = useState<string[]>([])
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
        title,
        message: content,
        image_id: null,
        area_id: null,
        tags: selectedTags
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

  const handleTagToggle = (tag: string) => {
  setSelectedTags(prev =>
    prev.includes(tag) ? prev.filter(t => t !== tag) : [...prev, tag]
  );
};


  const cancelImage = () => {
    setSelectedFile(null)
    setPreviewUrl(null)
  }

  useEffect(() => {
    const fetchTags = async () => {
      try {
        const tags = await getTags()
        const tagNames = tags.map(t => t.tag_name)
        setAvailableTags(tagNames)
      } catch (e) {
        console.error('タグの取得に失敗しました', e)
      }
    }
    fetchTags()
  }, [])

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
          <h2 className={styles.title}>スレッド作成</h2>
        </div>

        {error && <p className={styles.error}>{error}</p>}

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
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="タイトル（例: 楽しかった旅行の話）"
              required
            />
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

        <form onSubmit={handleSubmit} className={styles.form}>
          {/* タグ選択 */}
          <div className={styles.formGroup}>
            <label className={styles.formLabel}>タグ:</label>
            <div className={styles.tagContainer}>
              {availableTags.map(tag => (
                <button
                  type="button"
                  key={tag}
                  className={`${styles.tagButton} ${selectedTags.includes(tag) ? styles.tagSelected : ''}`}
                  onClick={() => handleTagToggle(tag)}
                >
                  {tag}
                </button>
              ))}
            </div>
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