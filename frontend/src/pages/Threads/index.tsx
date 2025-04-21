import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '@/hooks/useAuth'
import { getThreads, Thread } from '@/api/thread'

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
    if (!isAuthenticated) {
      navigate('/login')
      return
    }

    fetchThreads()
  }, [isAuthenticated, page])

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
    navigate('/thread/new')
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
    <div className="p-4">
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-xl font-bold">スレッド一覧</h1>
        <button 
          onClick={handleCreateThread}
          className="bg-blue-500 text-white px-4 py-2 rounded"
        >
          新規スレッド作成
        </button>
      </div>

      {loading ? (
        <p>読み込み中...</p>
      ) : error ? (
        <p className="text-red-500">{error}</p>
      ) : (
        <>
          <div className="space-y-4">
            {threads.length === 0 ? (
              <p>スレッドがありません</p>
            ) : (
              threads.map((thread) => (
                <div 
                  key={thread.id}
                  className="border p-4 rounded cursor-pointer hover:bg-gray-50"
                  onClick={() => handleViewThread(thread.id)}
                >
                  <div className="flex justify-between">
                    <h2 className="font-bold">{thread.title}</h2>
                    <div className="text-gray-500 text-sm">
                      {new Date(thread.created_at).toLocaleString()}
                    </div>
                  </div>
                  
                  <div className="flex mt-2">
                    <div className="flex items-center text-sm text-gray-600 mr-4">
                      <span>作成者: {thread.created_by.user_name}</span>
                    </div>
                    
                    <div className="flex space-x-4 text-sm text-gray-600">
                      <span>💬 {thread.messages_count}</span>
                      <span>❤️ {thread.hearts_count}</span>
                    </div>
                  </div>
                  
                  {thread.tags.length > 0 && (
                    <div className="mt-2 flex flex-wrap gap-1">
                      {thread.tags.map((tag) => (
                        <span 
                          key={tag.id}
                          className="bg-gray-200 text-gray-700 px-2 py-0.5 rounded-full text-xs"
                        >
                          {tag.name}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              ))
            )}
          </div>

          {/* ページネーション */}
          {threads.length > 0 && (
            <div className="flex justify-between items-center mt-4">
              <button
                onClick={handlePreviousPage}
                disabled={page === 1}
                className={`px-3 py-1 rounded ${
                  page === 1 ? 'bg-gray-300' : 'bg-blue-500 text-white'
                }`}
              >
                前へ
              </button>
              <span>
                {page} / {totalPages} ページ
              </span>
              <button
                onClick={handleNextPage}
                disabled={page >= totalPages}
                className={`px-3 py-1 rounded ${
                  page >= totalPages ? 'bg-gray-300' : 'bg-blue-500 text-white'
                }`}
              >
                次へ
              </button>
            </div>
          )}
        </>
      )}
    </div>
  )
}

export default ThreadsPage 