import { useEffect, useState } from 'react'
import { deleteThread } from '@/api/thread'
import { useParams, useNavigate } from 'react-router-dom'
import { useAuth } from '@/hooks/useAuth'
import { getThreadDetail, postMessage, heartThread, unheartThread, ThreadDetailResponse } from '@/api/thread'
import { uploadImage } from '@/api/upload'

function ThreadDetailPage() {
  const { threadId } = useParams<{ threadId: string }>()
  const { token, isAuthenticated } = useAuth()
  const [authChecked, setAuthChecked] = useState(false)
  const navigate = useNavigate()
  const [threadData, setThreadData] = useState<ThreadDetailResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [newMessage, setNewMessage] = useState('')
  const [messageType, setMessageType] = useState<'text' | 'image'>('text')
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isDeleting, setIsDeleting] = useState(false)

  useEffect(() => {
    if (threadId) {
      fetchThreadDetail()
    }
  }, [threadId])

  const fetchThreadDetail = async () => {
    if (!threadId) return

    setLoading(true)
    try {
      const data = await getThreadDetail(threadId, token)
      setThreadData(data)
    } catch (err: any) {
      console.error('スレッド詳細取得エラー:', err)
      setError('スレッドの詳細取得に失敗しました')
    } finally {
      setLoading(false)
    }
  }

  const handleHeart = async () => {
    if (!token || !threadId || !threadData) return

    try {
      if (threadData.thread.is_hearted) {
        await unheartThread(threadId, token)
      } else {
        await heartThread(threadId, token)
      }
      // いいねの状態を更新するため詳細を再取得
      fetchThreadDetail()
    } catch (err: any) {
      console.error('いいね処理エラー:', err)
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
    if ((messageType === 'text' && !newMessage) || 
        (messageType === 'image' && !selectedFile)) {
      return
    }

    setIsSubmitting(true)
    try {
      if (messageType === 'text') {
        await postMessage(
          threadId,
          { content: newMessage, message_type: 'text' },
          token
        )
        setNewMessage('')
      } else if (messageType === 'image' && selectedFile) {
        // 画像をアップロード
        const uploadResult = await uploadImage(selectedFile, token)
        
        // アップロードした画像IDをメッセージとして投稿
        await postMessage(
          threadId,
          { content: uploadResult.image.id, message_type: 'image' },
          token
        )
        setSelectedFile(null)
      }
      // 投稿後にスレッド詳細を再取得
      fetchThreadDetail()
    } catch (err: any) {
      console.error('メッセージ投稿エラー:', err)
      setError('メッセージの投稿に失敗しました')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleBackToList = () => {
    navigate('/threads')
  }

  const handleDeleteThread = async () => {
    if (!threadId) return

    const confirmDelete = window.confirm('本当にこのスレッドを削除しますか？')
    if (!confirmDelete) return

    setIsDeleting(true)
    setError('')

    try {
      await deleteThread(threadId)
      alert('スレッドを削除しました')
      navigate('/threads') // スレッド一覧へリダイレクト
    } catch (err: any) {
      console.error('スレッド削除エラー:', err)
      setError('スレッドの削除に失敗しました')
    } finally {
      setIsDeleting(false)
    }
  }

  if (loading) {
    return <div className="p-4">読み込み中...</div>
  }

  if (error) {
    return (
      <div className="p-4">
        <p className="text-red-500">{error}</p>
        <button 
          onClick={handleBackToList}
          className="mt-4 bg-gray-500 text-white px-4 py-2 rounded"
        >
          スレッド一覧に戻る
        </button>
      </div>
    )
  }

  if (!threadData) {
    return (
      <div className="p-4">
        <p>スレッドが見つかりません</p>
        <button 
          onClick={handleBackToList}
          className="mt-4 bg-gray-500 text-white px-4 py-2 rounded"
        >
          スレッド一覧に戻る
        </button>
      </div>
    )
  }

  return (
    <div className="p-4">
      <div className="mb-4">
        <button 
          onClick={handleBackToList}
          className="text-blue-500"
        >
          ← スレッド一覧に戻る
        </button>
      </div>

      <div className="mb-6">
        <div className="flex justify-between items-start">
          <h1 className="text-xl font-bold">{threadData.thread.title}</h1>
          <div className="text-gray-500 text-sm">
            {new Date(threadData.thread.created_at).toLocaleString()}
          </div>
        </div>
        
        <div className="flex items-center text-sm text-gray-600 mt-2">
          <span>作成者: {threadData.thread.created_by.user_name}</span>
        </div>
        
        {threadData.thread.tags.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-1">
            {threadData.thread.tags.map((tag) => (
              <span 
                key={tag.id}
                className="bg-gray-200 text-gray-700 px-2 py-0.5 rounded-full text-xs"
              >
                {tag.name}
              </span>
            ))}
          </div>
        )}
        
        <div className="mt-4">
          <button 
            onClick={handleHeart}
            className={`flex items-center gap-1 px-3 py-1 rounded-full ${
              threadData.thread.is_hearted 
                ? 'bg-red-100 text-red-500' 
                : 'bg-gray-100 text-gray-500'
            }`}
          >
            {threadData.thread.is_hearted ? '❤️' : '🤍'} {threadData.thread.hearts_count}
          </button>
        </div>
      </div>
      
      <div className="mb-8">
        <h2 className="text-lg font-semibold mb-2">メッセージ</h2>
        <div className="space-y-4">
          {threadData.messages.length === 0 ? (
            <p>メッセージはまだありません</p>
          ) : (
            threadData.messages.map((message) => (
              <div key={message.id} className="border p-3 rounded">
                <div className="flex justify-between items-start">
                  <div className="flex items-center gap-2">
                    <div className="font-semibold">{message.created_by.user_name}</div>
                    <div className="text-gray-500 text-xs">
                      {new Date(message.created_at).toLocaleString()}
                    </div>
                  </div>
                </div>
                
                <div className="mt-2">
                  {message.message_type === 'text' ? (
                    <p className="whitespace-pre-wrap">{message.content}</p>
                  ) : (
                    <img 
                      src={message.content} 
                      alt="投稿画像" 
                      className="max-w-full max-h-96 object-contain"
                    />
                  )}
                </div>
              </div>
            ))
          )}
        </div>
      </div>
      
      <div>
        <h2 className="text-lg font-semibold mb-2">メッセージを投稿</h2>
        <form onSubmit={handleSubmit} className="space-y-3">
          <div>
            <div className="flex gap-4 mb-2">
              <label className="flex items-center">
                <input
                  type="radio"
                  name="messageType"
                  checked={messageType === 'text'}
                  onChange={() => setMessageType('text')}
                  className="mr-1"
                />
                テキスト
              </label>
              <label className="flex items-center">
                <input
                  type="radio"
                  name="messageType"
                  checked={messageType === 'image'}
                  onChange={() => setMessageType('image')}
                  className="mr-1"
                />
                画像
              </label>
            </div>
            
            {messageType === 'text' ? (
              <textarea
                value={newMessage}
                onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setNewMessage(e.target.value)}
                className="w-full border rounded p-2"
                placeholder="メッセージを入力"
                rows={3}
              />
            ) : (
              <div className="flex flex-col">
                <input
                  type="file"
                  accept="image/*"
                  onChange={handleFileChange}
                  className="mb-2"
                />
                {selectedFile && (
                  <div className="mt-2">
                    <p className="text-sm text-gray-600">選択済み: {selectedFile.name}</p>
                  </div>
                )}
              </div>
            )}
          </div>
          
          <button
            type="submit"
            disabled={isSubmitting || 
              (messageType === 'text' && !newMessage) || 
              (messageType === 'image' && !selectedFile)}
            className="bg-blue-500 text-white px-4 py-2 rounded disabled:bg-gray-300"
          >
            {isSubmitting ? '送信中...' : '送信'}
          </button>
        </form>
      </div>

      {/* 削除ボタン */}
      <div className="mt-6">
        <button
          onClick={handleDeleteThread}
          className="bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600 disabled:bg-gray-400"
          disabled={isDeleting}
        >
          {isDeleting ? '削除中...' : 'スレッドを削除'}
        </button>
      </div>
    </div>
  )
}

export default ThreadDetailPage