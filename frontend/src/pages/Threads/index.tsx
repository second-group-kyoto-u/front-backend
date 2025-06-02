import { useEffect, useState } from 'react'
import { useNavigate, useLocation, Link } from 'react-router-dom'
import { useAuth } from '@/hooks/useAuth'
import { getThreads, heartThread, unheartThread, Thread } from '@/api/thread'
import styles from './Threads.module.css'

function ThreadsPage() {
  const { isAuthenticated } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [threads, setThreads] = useState<Thread[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [fadingThreadId, setFadingThreadId] = useState<string | null>(null)
  const newThread = location.state?.newThread
  const queryParams = new URLSearchParams(location.search)
  const selectedTag = queryParams.get('tag') || undefined
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const perPage = 10

  useEffect(() => {
    fetchThreads()
  }, [page, selectedTag]) // ← ここに selectedTag を追加！

  useEffect(() => {
    if (newThread) {
      setThreads(prev => [newThread, ...prev])
      window.history.replaceState({}, '')
    }
  }, [newThread])

  const fetchThreads = async () => {
    setLoading(true)
    try {
      const data = await getThreads({
        page,
        per_page: perPage,
        tags: selectedTag ? [selectedTag] : undefined
      })
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
    }, 400)
  }

  const handleCreateThread = () => {
    isAuthenticated ? navigate('/threads/create') : navigate('/login')
  }

  const handleLike = async (e: React.MouseEvent, threadId: string) => {
    e.stopPropagation()
    if (!isAuthenticated) {
      alert('いいねするためにはログインが必要です')
      return
    }
    const thread = threads.find((t) => t.id === threadId)
    if (!thread) return

    try {
      if (thread.is_hearted) {
        await unheartThread(threadId)
      } else {
        await heartThread(threadId)
      }
      setThreads((prev) =>
        prev.map((t) =>
          t.id === threadId
            ? {
                ...t,
                is_hearted: !t.is_hearted,
                hearts_count: t.hearts_count + (t.is_hearted ? -1 : 1),
              }
            : t
        )
      )
    } catch (error) {
      console.error('いいね操作失敗', error)
      alert("いいね操作に失敗しました")
    }
  }

  const handleReply = (e: React.MouseEvent, threadId: string) => {
    e.stopPropagation()
    handleViewThread(threadId)
  }

  return (
    <div className={styles.threadsContainer}>
      <div className={styles.threadsHeader}>
        {selectedTag && (
          <button onClick={() => navigate(-1)} className={styles.backButton}>←</button>
        )}
        <div className={styles.threadsTitle}>
          {selectedTag
            ? `「${threads[0]?.tags.find(t => t.id === selectedTag)?.name || 'タグ'}」のスレッド`
            : 'スレッド'}
        </div>
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
                className={`
                  ${styles.threadItem}
                  ${fadingThreadId && fadingThreadId !== thread.id ? styles.fadeOut : ''}
                  ${newThread && thread.id === newThread.id ? styles.fadeIn : ''}
                `}
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

                {thread.tags && thread.tags.length > 0 && (
                  <div className={styles.threadTags}>
                    {thread.tags.map(tag => (
                      <Link
                        key={tag.id}
                        to={`/threads?tag=${tag.id}`}
                        onClick={(e) => e.stopPropagation()}
                        className={styles.tag}
                      >
                        {tag.name}
                      </Link>
                    ))}
                  </div>
                )}

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

      <button 
        className={styles.createButton} 
        onClick={handleCreateThread}
        aria-label="スレッドを作成"
      >
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