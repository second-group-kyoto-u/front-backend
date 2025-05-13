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
import { Paperclip, Send } from 'lucide-react'
import styles from './ThreadDetail.module.css'

function ThreadDetailPage() {
  const { threadId } = useParams<{ threadId?: string }>()
  const { token, user } = useAuth()
  const navigate = useNavigate()
  const [threadData, setThreadData] = useState<ThreadDetailResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [newMessage, setNewMessage] = useState('')
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const inputRef = useRef<HTMLTextAreaElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (threadId) fetchThreadDetail(threadId)
  }, [threadId])

  useEffect(() => {
    inputRef.current?.focus()
  }, [])

  useEffect(() => {
    const scrollToBottom = () => {
      const replyBox = document.querySelector('#replyBox')
      if (replyBox) replyBox.scrollIntoView({ behavior: 'smooth', block: 'end' })
    }
    scrollToBottom()
  }, [threadData?.messages.length])

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

  const handleSubmit = async (e: React.FormEvent | React.KeyboardEvent) => {
    e.preventDefault()
    if (!token || !threadId || isSubmitting) return
    if (!newMessage.trim() && !selectedFile) return
    setIsSubmitting(true)
    try {
      if (selectedFile) {
        const uploadResult = await uploadImage(selectedFile, token)
        await postMessage(threadId, { content: uploadResult.image.id, message_type: 'image' }, token)
        setSelectedFile(null)
        setPreviewUrl(null)
      } else {
        await postMessage(threadId, { content: newMessage, message_type: 'text' }, token)
        setNewMessage('')
      }
      fetchThreadDetail(threadId)

      if (inputRef.current) {
        inputRef.current.blur()
      }
    } catch {
      setError('メッセージの投稿に失敗しました')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setSelectedFile(file);
      const reader = new FileReader();
      reader.onloadend = () => {
        setPreviewUrl(reader.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleClickItem = () => {
    inputRef.current?.focus()
  }

  const handleClickOutside = (e: React.MouseEvent<HTMLDivElement>) => {
    if (e.target === containerRef.current) {
      inputRef.current?.blur()
    }
  }

  if (loading) return <div className={styles.loading}>読み込み中...</div>
  if (error) return <div className={styles.error}>{error}</div>
  if (!threadData) return <div className={styles.error}>スレッドが見つかりません</div>

  return (
    <div ref={containerRef} className={styles.threadContainer} onClick={handleClickOutside}>
      <button onClick={() => navigate('/threads')} className={styles.backButton}>←</button>

      <div className={styles.threadItem} onClick={handleClickItem}>
        <div className={styles.threadAuthor}>
          <a
            href={`/user/${threadData.thread.created_by.id}`}
            onClick={(e) => e.stopPropagation()}
            className={styles.authorLink}
          >
            <img
              className={styles.authorAvatar}
              src={threadData.thread.created_by.profile_image_url || '/default-avatar.png'}
              onError={(e) => { e.currentTarget.src = '/default-avatar.png' }}
              alt={`${threadData.thread.created_by.user_name}のプロフィール画像`}
            />
            <div className={styles.authorName}>{threadData.thread.created_by.user_name}</div>
          </a>
          <div className={styles.threadTime}>
            {new Date(threadData.thread.created_at).toLocaleTimeString([], {
              hour: '2-digit', minute: '2-digit',
            })}
          </div>
        </div>
        <div className={styles.threadContent}>{threadData.thread.title}</div>
        <div className={styles.threadActions}>
          <button className={styles.actionButton} onClick={handleHeart}>
            ❤️ {threadData.thread.hearts_count}
          </button>
          <button className={styles.actionButton} onClick={() => inputRef.current?.focus()}>
            💬 {threadData.thread.messages_count}
          </button>
        </div>
      </div>

      <hr className={styles.divider} />

      <section className={styles.messagesSection}>
        {threadData.messages.length === 0 ? (
          <p>まだ返信はありません</p>
        ) : (
          threadData.messages.map(msg => (
            <div
              key={msg.id}
              className={styles.threadItem}
              onClick={handleClickItem}
            >
              <div className={styles.threadAuthor}>
                <a
                  href={`/user/${msg.created_by.id}`}
                  onClick={(e) => e.stopPropagation()}
                  className={styles.authorLink}
                >
                  <img
                    className={styles.authorAvatar}
                    src={msg.created_by.profile_image_url || '/default-avatar.png'}
                    onError={(e) => { e.currentTarget.src = '/default-avatar.png' }}
                    alt={`${msg.created_by.user_name}のプロフィール画像`}
                  />
                  <div className={styles.authorName}>{msg.created_by.user_name}</div>
                </a>
                <div className={styles.threadTime}>
                  {new Date(msg.created_at).toLocaleTimeString([], {
                    hour: '2-digit', minute: '2-digit',
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
        <div id="replyBox" />
      </section>

      <form className={styles.fixedReplyForm} onSubmit={handleSubmit}>
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
          onClick={() => fileInputRef.current?.click()}
          className={styles.attachButton}
        >
          📎
        </button>

        <textarea
          ref={inputRef}
          value={newMessage}
          onChange={e => setNewMessage(e.target.value)}
          onKeyDown={(e) => {
            if (e.ctrlKey && e.key === 'Enter') handleSubmit(e)
          }}
          className={styles.messageInput}
          placeholder="返信を入力..."
        />

        <button
          type="submit"
          className={styles.sendButton}
          disabled={isSubmitting || (!newMessage.trim() && !selectedFile)}
        >
          →
        </button>
      </form>

    </div>
  )
}

export default ThreadDetailPage