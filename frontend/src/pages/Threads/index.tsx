import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '@/hooks/useAuth'
import { getThreads, Thread } from '@/api/thread'
import './styles.css'

function ThreadsPage() {
  const { isAuthenticated } = useAuth()
  const navigate = useNavigate()
  const [threads, setThreads] = useState<Thread[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const perPage = 10

  // スレッドページの閲覧は認証なし
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
    if (!isAuthenticated) {
      navigate('/login')
    } else {
      navigate('/threads/create')
    }
  }

  // ページネーション
  const totalPages = Math.ceil(total / perPage)
  const handlePreviousPage = () => {
    if (page > 1) setPage(page - 1)
  }
  const handleNextPage = () => {
    if (page < totalPages) setPage(page + 1)
  }

  return (
    <div className="threads-container">
      <div className="threads-header">
        <div className="threads-title">スレッド</div>
      </div>

      {loading ? (
        <div className="flex justify-center items-center h-40">
          <p>読み込み中...</p>
        </div>
      ) : error ? (
        <div className="flex justify-center items-center h-40">
          <p className="text-red-500">{error}</p>
        </div>
      ) : (
        <div className="threads-list">
          {threads.length === 0 ? (
            <p className="text-center p-4">スレッドがありません</p>
          ) : (
            threads.map((thread) => (
              <div 
                key={thread.id}
                className="thread-item"
                onClick={() => handleViewThread(thread.id)}
              >
                <div className="thread-author">
                  <div className="author-avatar"></div>
                  <div className="author-name">{thread.created_by.user_name}</div>
                  <div className="flex-grow"></div>
                  <div className="thread-time">
                    {new Date(thread.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                  </div>
                </div>
                
                <div className="thread-content">
                  {thread.title}
                </div>
                
                <div className="thread-actions">
                  <div className="action-button">
                    <span>❤️</span>
                    <span>{thread.hearts_count}</span>
                  </div>
                  <div className="action-button">
                    <span>💬</span>
                    <span>{thread.messages_count}</span>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      <button 
        className="create-button"
        onClick={handleCreateThread}
      >
        +
      </button>

      <div className="navigation">
        <div className={`nav-item`}>
          <div>👥</div>
          <div>イベント</div>
        </div>
        <div className={`nav-item active`}>
          <div>📝</div>
          <div>スレッド</div>
        </div>
        <div className={`nav-item`}>
          <div>💬</div>
          <div>トーク</div>
        </div>
        <div className={`nav-item`}>
          <div>👤</div>
          <div>マイページ</div>
        </div>
      </div>
    </div>
  )
}

export default ThreadsPage 