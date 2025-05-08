import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '@/hooks/useAuth'
import { getThreads, Thread } from '@/api/thread'
import style from './Threads.module.css'

function ThreadsPage() {
  const { isAuthenticated } = useAuth()
  const navigate = useNavigate()
  const [threads, setThreads] = useState<Thread[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
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
    navigate(`/thread/${threadId}`)
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
    navigate(`/thread/${threadId}`)
  }

  return (
    <div className={style.threadsContainer}>
      <div className={style.threadsHeader}>
        <div className={style.threadsTitle}>スレッド</div>
      </div>

      {loading ? (
        <div className={style.loading}>読み込み中...</div>
      ) : error ? (
        <div className={style.error}>{error}</div>
      ) : (
        <div className={style.threadsList}>
          {threads.length === 0 ? (
            <p className={style.noData}>スレッドがありません</p>
          ) : (
            threads.map((thread) => (
              <div
                key={thread.id}
                className={style.threadItem}
                onClick={() => handleViewThread(thread.id)}
              >
                <div className={style.threadAuthor}>
                  <div className={style.authorAvatar}></div>
                  <div className={style.authorName}>{thread.created_by.user_name}</div>
                  <div className={style.threadTime}>
                    {new Date(thread.created_at).toLocaleTimeString([], {
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </div>
                </div>

                <div className={style.threadContent}>{thread.title}</div>

                <div className={style.threadActions}>
                  <button
                    className={style.actionButton}
                    onClick={(e) => handleLike(e, thread.id)}
                  >
                    ❤️ {thread.hearts_count}
                  </button>
                  <button
                    className={style.actionButton}
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

      <button className={style.createButton} onClick={handleCreateThread}>
        ＋
      </button>

      <div className={style.navigation}>
        <a href="/events" className={style.navItem}>
          👥<div>イベント</div>
        </a>
        <a href="/threads" className={`${style.navItem} ${style.active}`}>
          📝<div>スレッド</div>
        </a>
        <a href="/talk" className={style.navItem}>
          💬<div>トーク</div>
        </a>
        <a href="/mypage" className={style.navItem}>
          👤<div>マイページ</div>
        </a>
      </div>
    </div>
  )
}

export default ThreadsPage
