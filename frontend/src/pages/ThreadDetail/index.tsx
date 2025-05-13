import { useEffect, useState, useRef } from 'react'
import {
  deleteThread,
  getThreadDetail,
  postMessage,
  heartThread,
  unheartThread,
  ThreadDetailResponse
} from '@/api/thread'
import { useParams, useNavigate } from 'react-router-dom'
import { useAuth } from '@/hooks/useAuth'
import { uploadImage } from '@/api/upload'
import styles from './ThreadDetail.module.css'

function ThreadDetailPage() {
  const { threadId } = useParams<{ threadId?: string }>()
  const { token } = useAuth()
  const navigate = useNavigate()
  const [threadData, setThreadData] = useState<ThreadDetailResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [newMessage, setNewMessage] = useState('')
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isDeleting, setIsDeleting] = useState(false)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    if (threadId) fetchThreadDetail(threadId)
  }, [threadId])

  const fetchThreadDetail = async (id: string) => {
    setLoading(true)
    try {
      const data = await getThreadDetail(id, token)
      setThreadData(data)
    } catch {
      setError('スレッドの詳細取得に失敗しました')
    } finally {
      setLoading(false)
    }
  }

  const handleHeart = async () => {
    if (!token || !threadId || !threadData) return
    try {
      threadData.thread.is_hearted
        ? await unheartThread(threadId, token)
        : await heartThread(threadId, token)
      fetchThreadDetail(threadId)
    } catch {
      setError('いいね処理に失敗しました')
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!token || !threadId || isSubmitting) return
    if (!newMessage.trim() && !selectedFile) return
    setIsSubmitting(true)
    try {
      if (selectedFile) {
        const uploadResult = await uploadImage(selectedFile, token)
        await postMessage(threadId, { content: uploadResult.image.id, message_type: 'image' }, token)
        setSelectedFile(null)
      } else {
        await postMessage(threadId, { content: newMessage, message_type: 'text' }, token)
        setNewMessage('')
      }
      fetchThreadDetail(threadId)
    } catch {
      setError('メッセージの投稿に失敗しました')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleDelete = async () => {
    if (!threadId || !token) return
    if (!window.confirm('本当に削除しますか？')) return
    setIsDeleting(true)
    try {
      await deleteThread(threadId, token)
      navigate('/threads')
    } catch {
      setError('削除に失敗しました')
    } finally {
      setIsDeleting(false)
    }
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.[0]) setSelectedFile(e.target.files[0])
  }

  if (loading) return <div className={styles.loading}>読み込み中...</div>
  if (error) return <div className={styles.error}>{error}</div>
  if (!threadData) return <div className={styles.error}>スレッドが見つかりません</div>

  const uniqueUserCount = new Set(threadData.messages.map(msg => msg.created_by.id)).size

  return (
    <div className={styles.threadContainer}>
      <button onClick={() => navigate('/threads')} className={styles.backButton}>← 戻る</button>

      {/* 原始スレッドの表示 */}
      <div className={styles.threadItem}>
        <div className={styles.threadAuthor}>
          <a
            href={`/user/${threadData.thread.created_by.id}`}
            onClick={(e) => e.stopPropagation()}
            className={styles.authorLink}
          >
            <img
              className={styles.authorAvatar}
              src={threadData.thread.created_by.profile_image_url || '/default-avatar.png'}
              onError={(e) => {
                e.currentTarget.src = '/default-avatar.png'
              }}
              alt={`${threadData.thread.created_by.user_name}のプロフィール画像`}
            />
            <div className={styles.authorName}>{threadData.thread.created_by.user_name}</div>
          </a>
          <div className={styles.threadTime}>
            {new Date(threadData.thread.created_at).toLocaleTimeString([], {
              hour: '2-digit',
              minute: '2-digit',
            })}
          </div>
        </div>
        <div className={styles.threadContent}>{threadData.thread.title}</div>
        <div className={styles.threadActions}>
          <button
            onClick={handleHeart}
            className={threadData.thread.is_hearted ? styles.hearted : styles.heartButton}
          >
            {threadData.thread.is_hearted ? '❤️' : '🤍'} {threadData.thread.hearts_count}
          </button>
          <div className={styles.replyCount}>
            💬 {uniqueUserCount}
          </div>
        </div>
      </div>

      <hr className={styles.divider} />

      {/* メッセージ表示 */}
      <section className={styles.messagesSection}>
        {threadData.messages.length === 0 ? (
          <p>まだ返信はありません</p>
        ) : (
          threadData.messages.map(msg => (
            <div key={msg.id} className={styles.threadItem}>
              <div className={styles.threadAuthor}>
                <a
                  href={`/user/${msg.created_by.id}`}
                  onClick={(e) => e.stopPropagation()}
                  className={styles.authorLink}
                >
                  <img
                    className={styles.authorAvatar}
                    src={msg.created_by.profile_image_url || '/default-avatar.png'}
                    onError={(e) => {
                      e.currentTarget.src = '/default-avatar.png'
                    }}
                    alt={`${msg.created_by.user_name}のプロフィール画像`}
                  />
                  <div className={styles.authorName}>{msg.created_by.user_name}</div>
                </a>
                <div className={styles.threadTime}>
                  {new Date(msg.created_at).toLocaleTimeString([], {
                    hour: '2-digit',
                    minute: '2-digit',
                  })}
                </div>
              </div>
              <div className={styles.threadContent}>
                {msg.message_type === 'text'
                  ? <p>{msg.content}</p>
                  : <img src={msg.content} alt="画像" className={styles.messageImage} />}
              </div>
            </div>
          ))
        )}
      </section>

      <form className={styles.replyForm} onSubmit={handleSubmit}>
        <textarea
          ref={inputRef}
          value={newMessage}
          onChange={e => setNewMessage(e.target.value)}
          className={styles.textarea}
          placeholder="返信を入力..."
          rows={3}
        />

        <label className={styles.uploadLabel}>
          画像をアップロード
          <input
            type="file"
            accept="image/*"
            onChange={handleFileChange}
            className={styles.hiddenFileInput}
          />
        </label>

        {selectedFile && (
          <div className={styles.fileName}>選択済み: {selectedFile.name}</div>
        )}

        <button type="submit" disabled={isSubmitting} className={styles.sendButton}>
          {isSubmitting ? '送信中...' : '返信'}
        </button>
      </form>

      <button onClick={handleDelete} className={styles.deleteButton} disabled={isDeleting}>
        {isDeleting ? '削除中...' : 'スレッドを削除'}
      </button>
    </div>
  )
}

export default ThreadDetailPage
