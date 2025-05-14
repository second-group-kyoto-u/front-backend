import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getJoinedEvents } from '@/api/event'

interface Event {
  id: string
  title: string
  description: string
}

const TalkListPage = () => {
  const [events, setEvents] = useState<Event[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const navigate = useNavigate()

  useEffect(() => {
    const fetchEvents = async () => {
      try {
        const res = await getJoinedEvents()
        setEvents(res.events)
      } catch (err: any) {
        setError('イベントの取得に失敗しました')
      } finally {
        setLoading(false)
      }
    }
    fetchEvents()
  }, [])

  const handleClick = (eventId: string) => {
    navigate(`/event/${eventId}/talk`)
  }

  if (loading) return <div className="p-4">読み込み中...</div>
  if (error) return <div className="p-4 text-red-500">{error}</div>

  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold mb-4">イベントトーク</h1>
      {events.length === 0 ? (
        <p>参加中のイベントはありません。</p>
      ) : (
        <ul className="space-y-4">
          {events.map((event) => (
            <li key={event.id} className="border p-3 rounded cursor-pointer hover:bg-gray-100"
                onClick={() => handleClick(event.id)}>
              <h2 className="text-lg font-semibold">{event.title}</h2>
              <p className="text-sm text-gray-600">{event.description}</p>
            </li>
          ))}
        </ul>
      )}
      <h1 className="text-2xl font-bold mb-4">ダイレクトメッセージ(未完成)</h1>
        <p>ダイレクトメッセージはありません。</p>
    </div>
  )
}

export default TalkListPage
