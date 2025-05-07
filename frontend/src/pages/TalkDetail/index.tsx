import { useParams } from 'react-router-dom'
import { useEffect, useState } from 'react'
import { fetchMessages, sendMessage } from '@/api/talk'

function TalkRoomPage() {
  const { roomId } = useParams<{ roomId: string }>()
  const [messages, setMessages] = useState<any[]>([])
  const [newMessage, setNewMessage] = useState('')

  useEffect(() => {
    const loadMessages = async () => {
      if (roomId) {
        const result = await fetchMessages(roomId)
        setMessages(result)
      }
    }
    loadMessages()
  }, [roomId])

  const handleSend = async () => {
    if (!newMessage.trim() || !roomId) return
    await sendMessage(roomId, newMessage)
    setNewMessage('')
    const updated = await fetchMessages(roomId) // 再読み込み
    setMessages(updated)
  }

  return (
    <div className="p-4">
      <h1 className="text-xl font-bold mb-4">トークルーム</h1>
      <div className="h-[400px] overflow-y-scroll border p-2 mb-4 bg-white">
        {messages.map((msg, i) => (
          <div key={i} className="mb-2">
            <span className="font-semibold">{msg.senderName}:</span> {msg.text}
          </div>
        ))}
      </div>
      <div className="flex gap-2">
        <input
          type="text"
          value={newMessage}
          onChange={(e) => setNewMessage(e.target.value)}
          className="flex-1 border rounded p-2"
          placeholder="メッセージを入力"
        />
        <button
          onClick={handleSend}
          className="bg-blue-500 text-white px-4 py-2 rounded"
        >
          送信
        </button>
      </div>
    </div>
  )
}

export default TalkRoomPage
