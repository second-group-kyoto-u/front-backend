import { useEffect, useState } from 'react'
import { deleteThread } from '@/api/thread'
import { useParams, useNavigate } from 'react-router-dom'
import { useAuth } from '@/hooks/useAuth'
import { getThreadDetail, postMessage, heartThread, unheartThread, ThreadDetailResponse } from '@/api/thread'
import { uploadImage } from '@/api/upload'
import styles from './ThreadDetail.module.css'

function ThreadDetailPage() {
  const { threadId } = useParams<{ threadId?: string }>()
  const { token } = useAuth()
  const [threadData, setThreadData] = useState<ThreadDetailResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [newMessage, setNewMessage] = useState('')
  const [messageType, setMessageType] = useState<'text' | 'image'>('text')
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isDeleting, setIsDeleting] = useState(false)
  const navigate = useNavigate()

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

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0])
      setMessageType('image')
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!token || !threadId || isSubmitting) return
    if ((messageType === 'text' && !newMessage) || (messageType === 'image' && !selectedFile)) return
    setIsSubmitting(true)
    try {
      if (messageType === 'text') {
        await postMessage(threadId, { content: newMessage, message_type: 'text' }, token)
        setNewMessage('')
      } else if (selectedFile) {
        const uploadResult = await uploadImage(selectedFile, token)
        await postMessage(threadId, { content: uploadResult.image.id, message_type: 'image' }, token)
        setSelectedFile(null)
      }
      fetchThreadDetail(threadId)
    } catch {
      setError('メッセージの投稿に失敗しました')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleDeleteThread = async () => {
    if (!threadId) {
      setError('スレッドIDが存在しません')
      return
    }

    if (!token) {
      setError('認証情報がありません')
      return
    }

    const confirmed = window.confirm('本当にこのスレッドを削除しますか？')
    if (!confirmed) return

    setIsDeleting(true)
    setError('')

    try {
      await deleteThread(threadId, token)
      alert('スレッドを削除しました')
      navigate('/threads')
    } catch (err) {
      console.error('スレッド削除エラー:', err)
      setError('スレッドの削除に失敗しました')
    } finally {
      setIsDeleting(false)
    }
  }

  const handleBackToList = () => navigate('/threads')

  if (loading) return <div className={styles.loading}>読み込み中...</div>
  if (error) return (
    <div className={styles.error}>
      <p>{error}</p>
      <button onClick={handleBackToList} className={styles.backButton}>スレッド一覧に戻る</button>
    </div>
  )
  if (!threadData) return (
    <div className={styles.error}>
      <p>スレッドが見つかりません</p>
      <button onClick={handleBackToList} className={styles.backButton}>スレッド一覧に戻る</button>
    </div>
  )

  return (
    <div className={styles.threadContainer}>
      <button onClick={handleBackToList} className={styles.backButton}>← スレッド一覧に戻る</button>

      <div className={styles.threadHeader}>
        <h1 className={styles.threadTitle}>{threadData.thread.title}</h1>
        <span className={styles.threadTimestamp}>{new Date(threadData.thread.created_at).toLocaleString()}</span>
      </div>
      <div className={styles.threadAuthor}>作成者: {threadData.thread.created_by.user_name}</div>

      {threadData.thread.tags.length > 0 && (
        <div className={styles.tagsContainer}>
          {threadData.thread.tags.map(tag => (
            <span key={tag.id} className={styles.tag}>{tag.name}</span>
          ))}
        </div>
      )}

      <button
        onClick={handleHeart}
        className={`${styles.heartButton} ${threadData.thread.is_hearted ? styles.hearted : styles.notHearted}`}
      >
        {threadData.thread.is_hearted ? '❤️' : '🤍'} {threadData.thread.hearts_count}
      </button>

      <div className={styles.messageSection}>
        <h2>メッセージ</h2>
        {threadData.messages.length === 0 ? (
          <p>メッセージはまだありません</p>
        ) : (
          threadData.messages.map(message => (
            <div key={message.id} className={styles.messageCard}>
              <div className={styles.messageMeta}>
                <span>{message.created_by.user_name}</span>
                <span>{new Date(message.created_at).toLocaleString()}</span>
              </div>
              <div className={styles.messageContent}>
                {message.message_type === 'text' ? (
                  <p>{message.content}</p>
                ) : (
                  <img src={message.content} alt="投稿画像" className={styles.messageImage} />
                )}
              </div>
            </div>
          ))
        )}
      </div>

      <form onSubmit={handleSubmit} className={styles.postForm}>
        <h2>メッセージを投稿</h2>
        <div className={styles.radioGroup}>
          <label><input type="radio" checked={messageType === 'text'} onChange={() => setMessageType('text')} /> テキスト</label>
          <label><input type="radio" checked={messageType === 'image'} onChange={() => setMessageType('image')} /> 画像</label>
        </div>

        {messageType === 'text' ? (
          <textarea
            value={newMessage}
            onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setNewMessage(e.target.value)}
            className={styles.textarea}
            placeholder="メッセージを入力"
            rows={3}
          />
        ) : (
          <div>
            <input type="file" accept="image/*" onChange={handleFileChange} className={styles.fileInput} />
            {selectedFile && <div>選択済み: {selectedFile.name}</div>}
          </div>
        )}

        <button type="submit" className={styles.submitButton} disabled={isSubmitting || (messageType === 'text' && !newMessage) || (messageType === 'image' && !selectedFile)}>
          {isSubmitting ? '送信中...' : '送信'}
        </button>
      </form>

      <button onClick={handleDeleteThread} className={styles.deleteButton} disabled={isDeleting}>
        {isDeleting ? '削除中...' : 'スレッドを削除'}
      </button>
    </div>
  )
}

export default ThreadDetailPage