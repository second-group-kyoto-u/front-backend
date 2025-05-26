import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '@/hooks/useAuth'
import { getThreads, heartThread, unheartThread, Thread } from '@/api/thread'
import { useLocation } from 'react-router-dom' // 🎯 location 経由で state を受け取る
import styles from './Threads.module.css'

function ThreadsPage() {
  const { isAuthenticated } = useAuth()
  const navigate = useNavigate()
  const [threads, setThreads] = useState<Thread[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [fadingThreadId, setFadingThreadId] = useState<string | null>(null)
  const location = useLocation()
  const newThread = location.state?.newThread // 🎯 新規スレッドが存在するかチェック
  const [total, setTotal] = useState(0) // しばらく使ってない
  const [page, setPage] = useState(1)  // しばらく使ってない
  const perPage = 10

  useEffect(() => {
    fetchThreads()
  }, [page])

  useEffect(() => {
    // 🎯 新しいスレッドがあれば先頭に追加し、state をクリアする
    if (newThread) {
      setThreads(prev => [newThread, ...prev])
      window.history.replaceState({}, '') // ✅ 再レンダリング時に重複追加されないように
      console.log(newThread)
    }
  }, [newThread])  

  const fetchThreads = async () => {
    setLoading(true)
    try {
      const data = await getThreads({ page, per_page: perPage })

      console.log('取得的 threads 資料:', data.threads)
      
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

  const handleLike = async (e: React.MouseEvent, threadId: string) => {
    e.stopPropagation()

    if (!isAuthenticated) {
      alert('いいねするためにはログインが必要です')
      return
    }

    // 現在のスレッドを取得
    const thread = threads.find((t) => t.id === threadId)
    if (!thread) return

    try {
      if (thread.is_hearted) {
        await unheartThread(threadId)
      } else {
        await heartThread(threadId)
      }

      // API成功後に状態更新（ここでUIを反映）
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
                      <span key={tag.id} className={styles.tag}>#{tag.name}</span>
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