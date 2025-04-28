import { useEffect, useState, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { sendEventMessage, getEvent } from '@/api/event'
import { uploadImage } from '@/api/upload'
import { useAuth } from '@/hooks/useAuth'
import type { EventMessageType } from '@/api/event'

function EventTalkPage() {
  const { eventId } = useParams<{ eventId: string }>()
  const { token } = useAuth()
  const navigate = useNavigate()
  const messagesEndRef = useRef<HTMLDivElement | null>(null)

  const [messages, setMessages] = useState<EventMessageType[]>([])
  const [newMessage, setNewMessage] = useState('')
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [messageType, setMessageType] = useState<'text' | 'image'>('text')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    if (messages.length > 0) {
      scrollToBottom()
    }
  }, [messages])

  useEffect(() => {
    if (eventId) {
      fetchMessages()
    }
  }, [eventId])

  const fetchMessages = async () => {
    if (!eventId) return
    setLoading(true)
    try {
      const data = await getEvent(eventId)
      setMessages(data.messages)
    } catch (err: any) {
      console.error('メッセージ取得エラー:', err)
      setError('メッセージの取得に失敗しました')
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!eventId || !token) return

    try {
      if (messageType === 'text' && newMessage) {
        await sendEventMessage(eventId, { content: newMessage, message_type: 'text' })
      } else if (messageType === 'image' && selectedFile) {
        const uploadRes = await uploadImage(selectedFile, token)
        await sendEventMessage(eventId, { image_id: uploadRes.image.id, message_type: 'image' })
      }
      setNewMessage('')
      setSelectedFile(null)
      fetchMessages()
    } catch (err: any) {
      console.error('送信エラー:', err)
      setError('メッセージ送信に失敗しました')
    }
  }

  if (loading) return <div className="p-4">読み込み中...</div>
  if (error) return <div className="p-4 text-red-500">{error}</div>

  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold mb-4">トークルーム</h1>

      <div className="space-y-3 mb-6">
        {messages.map((msg) => (
          <div key={msg.id} className="border p-3 rounded">
            <div className="text-gray-600 text-xs mb-1">
              {msg.sender?.user_name} - {new Date(msg.timestamp || '').toLocaleString()}
            </div>
            {msg.message_type === 'text' ? (
              <p>{msg.content}</p>
            ) : (
              <img src={msg.image_url || ''} alt="投稿画像" className="max-w-full max-h-80 object-contain" />
            )}
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={handleSubmit} className="space-y-3">
        <div className="flex gap-4">
          <label>
            <input type="radio" name="type" checked={messageType === 'text'} onChange={() => setMessageType('text')} /> テキスト
          </label>
          <label>
            <input type="radio" name="type" checked={messageType === 'image'} onChange={() => setMessageType('image')} /> 画像
          </label>
        </div>

        {messageType === 'text' ? (
          <textarea
            value={newMessage}
            onChange={(e) => setNewMessage(e.target.value)}
            placeholder="メッセージを入力"
            className="w-full border rounded p-2"
          />
        ) : (
          <input type="file" accept="image/*" onChange={(e) => setSelectedFile(e.target.files?.[0] || null)} />
        )}

        <button type="submit" className="bg-blue-500 text-white px-4 py-2 rounded">
          送信
        </button>
      </form>

      <button onClick={() => navigate('/events')} className="mt-6 text-blue-500">
        ← イベント一覧へ戻る
      </button>
    </div>
  )
}

export default EventTalkPage
