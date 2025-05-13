import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '@/hooks/useAuth'
import { getThreads, Thread } from '@/api/thread'
import styles from './Threads.module.css'

function ThreadsPage() {
  const { isAuthenticated } = useAuth()
  const navigate = useNavigate()
  const [threads, setThreads] = useState<Thread[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [fadingThreadId, setFadingThreadId] = useState<string | null>(null)
  const [total, setTotal] = useState(0) // しばらく使ってない
  const [page, setPage] = useState(1)  // しばらく使ってない
  const perPage = 10

  useEffect(() => {
    fetchThreads()
  }, [page])

  const fetchThreads = async () => {
    setLoading(true)
    try {
      const data = await getThreads({ page, per_page: perPage })
      setThreads(data.threads)
      setTotal(data.total)
    } catch (err: any) {
      console.error('スレッド取得エラー:', err)
      setError('スレッドの取得に失敗しました')
    } finally {
      setLoading(false)
    }
  }

  const handleViewThread = (threadId: string) => {
    setFadingThreadId(threadId)
    setTimeout(() => {
      navigate(`/thread/${threadId}`)
    }, 400) // アニメーションと一致させる
  }

  const handleCreateThread = () => {
    isAuthenticated ? navigate('/threads/create') : navigate('/login')
  }

  const handleLike = (e: React.MouseEvent, threadId: string) => {
    e.stopPropagation()
    setThreads((prev) =>
      prev.map((t) =>
        t.id === threadId ? { ...t, hearts_count: t.hearts_count + 1 } : t
      )
    )
  }

  const handleReply = (e: React.MouseEvent, threadId: string) => {
    e.stopPropagation()
    handleViewThread(threadId)
  }

  return (
    <div className={styles.threadsContainer}>
      <div className={styles.threadsHeader}>
        <div className={styles.threadsTitle}>スレッド</div>
      </div>

      {loading ? (
        <div className={styles.loading}>読み込み中...</div>
      ) : error ? (
        <div className={styles.error}>{error}</div>
      ) : (
        <div className={styles.threadsList}>
          {threads.length === 0 ? (
            <p className={styles.noData}>スレッドがありません</p>
          ) : (
            threads.map((thread) => (
              <div
                key={thread.id}
                className={`${styles.threadItem} ${fadingThreadId && fadingThreadId !== thread.id ? styles.fadeOut : ''}`}
                onClick={() => handleViewThread(thread.id)}
              >
                <div className={styles.threadAuthor}>
                  <a
                    href={`/user/${thread.created_by.id}`}
                    onClick={(e) => e.stopPropagation()}
                    className={styles.authorLink}
                  >
                    <img
                      className={styles.authorAvatar}
                      src={thread.created_by.profile_image_url || '/default-avatar.png'}
                      onError={(e) => {
                        e.currentTarget.src = '/default-avatar.png'
                      }}
                      alt={`${thread.created_by.user_name}のプロフィール画像`}
                    />
                    <div className={styles.authorName}>{thread.created_by.user_name}</div>
                  </a>
                  <div className={styles.threadTime}>
                    {new Date(thread.created_at).toLocaleTimeString([], {
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </div>
                </div>

                <div className={styles.threadContent}>{thread.title}</div>

                <div className={styles.threadActions}>
                  <button
                    className={styles.actionButton}
                    onClick={(e) => handleLike(e, thread.id)}
                  >
                    ❤️ {thread.hearts_count}
                  </button>
                  <button
                    className={styles.actionButton}
                    onClick={(e) => handleReply(e, thread.id)}
                  >
                    💬 {thread.messages_count}
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      <button className={styles.createButton} onClick={handleCreateThread}>
        ＋
      </button>

      <div className={styles.navigation}>
        <a href="/events" className={styles.navItem}>
          👥<div>イベント</div>
        </a>
        <a href="/threads" className={`${styles.navItem} ${styles.active}`}>
          📝<div>スレッド</div>
        </a>
        <a href="/talk" className={styles.navItem}>
          💬<div>トーク</div>
        </a>
        <a href="/mypage" className={styles.navItem}>
          👤<div>マイページ</div>
        </a>
      </div>
    </div>
  )
}

export default ThreadsPage