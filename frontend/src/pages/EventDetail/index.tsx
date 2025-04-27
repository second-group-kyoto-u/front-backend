import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { getEvent, sendEventMessage, /*joinEvent, leaveEvent, startEvent, endEvent*/ } from '@/api/event'
import { uploadImage } from '@/api/upload'
import { useAuth } from '@/hooks/useAuth'
import type { EventType, EventMessageType } from '@/api/event'

function EventDetailPage() {
  const { eventId } = useParams<{ eventId: string}>()
  const { token, isAuthenticated } = useAuth()
  const navigate = useNavigate()

  const [eventData, setEventData] = useState<EventType | null>(null)
  const [messages, setMessages] = useState<EventMessageType[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [newMessage, setNewMessage] = useState('')
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [messageType, setMessageType] = useState<'text' | 'image'>('text')

  useEffect(() => {
    if (eventId) {
      fetchEventDetail()
    }
  }, [eventId])

  const fetchEventDetail = async () => {
    if (!eventId) return
    setLoading(true)
    try {
      const data = await getEvent(eventId)
      setEventData(data.event)
      setMessages(data.messages)
    } catch (err: any) {
      console.error('イベント詳細取得エラー:', err)
      setError('イベントの詳細取得に失敗しました')
    } finally {
      setLoading(false)
    }
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0])
      setMessageType('image')
    }
  }

  const handleSubmitMessage = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!token || !eventId) return

    try {
      if (messageType === 'text' && newMessage) {
        await sendEventMessage(eventId, { content: newMessage, message_type: 'text' })
      } else if (messageType === 'image' && selectedFile) {
        const uploadRes = await uploadImage(selectedFile, token)
        await sendEventMessage(eventId, { image_id: uploadRes.image.id, message_type: 'image' })
      }
      setNewMessage('')
      setSelectedFile(null)
      fetchEventDetail()
    } catch (err: any) {
      console.error('メッセージ送信エラー:', err)
      setError('メッセージ送信に失敗しました')
    }
  }

  const handleBack = () => {
    navigate('/events')
  }

  if (loading) {
    return <div className="p-4">読み込み中...</div>
  }

  if (error) {
    return (
      <div className="p-4">
        <p className="text-red-500">{error}</p>
        <button onClick={handleBack} className="mt-4 bg-gray-500 text-white px-4 py-2 rounded">イベント一覧に戻る</button>
      </div>
    )
  }

  if (!eventData) {
    return (
      <div className="p-4">
        <p>イベントが見つかりません</p>
        <button onClick={handleBack} className="mt-4 bg-gray-500 text-white px-4 py-2 rounded">イベント一覧に戻る</button>
      </div>
    )
  }

  return (
    <div className="p-4">
      <button onClick={handleBack} className="text-blue-500">← イベント一覧に戻る</button>

      <h1 className="text-2xl font-bold mt-4 mb-2">{eventData.message}</h1>
      <p className="text-sm text-gray-600">{new Date(eventData.published_at || '').toLocaleString()}</p>

      {eventData.area && (
        <p className="mt-2 text-gray-700">エリア: {eventData.area.name}</p>
      )}

      <div className="my-6">
        <h2 className="text-lg font-semibold">メッセージ一覧</h2>
        <div className="space-y-3 mt-2">
          {messages.map((msg) => (
            <div key={msg.id} className="border p-3 rounded">
              <div className="flex items-center gap-2">
                <span className="font-semibold">{msg.sender?.user_name}</span>
                <span className="text-gray-500 text-xs">{new Date(msg.timestamp || '').toLocaleString()}</span>
              </div>
              <div className="mt-2">
                {msg.message_type === 'text' ? (
                  <p className="whitespace-pre-wrap">{msg.content}</p>
                ) : (
                  <img src={msg.image_url || ''} alt="投稿画像" className="max-w-full max-h-80 object-contain" />
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="my-6">
        <h2 className="text-lg font-semibold mb-2">メッセージを投稿</h2>
        <form onSubmit={handleSubmitMessage} className="space-y-3">
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
            <input type="file" accept="image/*" onChange={handleFileChange} />
          )}
          <button type="submit" className="bg-blue-500 text-white px-4 py-2 rounded">送信</button>
        </form>
      </div>
    </div>
  )
}

export default EventDetailPage;
