import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getJoinedEvents } from '@/api/event'
import { getDirectMessageOverview } from '@/api/friend'
import './TalkListPage.css'

interface Event {
  id: string
  title: string
  description: string
}

interface DirectMessageOverview {
  partner_id: string
  partner: {
    id: string;
    user_name: string;
    user_image_url: string | null;
    profile_message: string | null;
    is_certificated: boolean;
  };
  latest_message: {
    content: string;
    sent_at: string;
    message_type: 'text' | 'image' | 'system' | 'bot';
  };
}

const TalkListPage = () => {
  const [events, setEvents] = useState<Event[]>([])
  const [dmList, setDmList] = useState<DirectMessageOverview[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const navigate = useNavigate()

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [eventRes, dmRes] = await Promise.all([
          getJoinedEvents(),
          getDirectMessageOverview()
        ])
        setEvents(eventRes.events)
        setDmList(dmRes)
      } catch (err: any) {
        setError('データの取得に失敗しました')
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [])

  const handleEventClick = (eventId: string) => {
    navigate(`/event/${eventId}/talk`)
  }

  const handleDmClick = (userId: string) => {
    navigate(`/friend/${userId}/dm`)
  }

  if (loading) return <div className="p-4">読み込み中...</div>
  if (error) return <div className="p-4 text-red-500">{error}</div>

  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold mb-4">イベントトーク</h1>
      {events.length === 0 ? (
        <p>参加中のイベントはありません。</p>
      ) : (
        <ul className="space-y-4 mb-8">
          {events.map((event) => (
            <li key={event.id} className="border p-3 rounded cursor-pointer hover:bg-gray-100"
                onClick={() => handleEventClick(event.id)}>
              <h2 className="text-lg font-semibold">{event.title}</h2>
              <p className="text-sm text-gray-600">{event.description}</p>
            </li>
          ))}
        </ul>
      )}

      <h1 className="text-2xl font-bold mb-4">ダイレクトメッセージ</h1>
      {dmList.length === 0 ? (
        <p>ダイレクトメッセージはありません。</p>
      ) : (
        <ul className="space-y-4">
          {dmList.map((dm) => (
            <li key={dm.partner_id} className="chat-item"
                onClick={() => handleDmClick(dm.partner_id)}>
              <div className="chat-avatar-wrapper">
                {dm.partner.user_image_url ? (
                  <img src={dm.partner.user_image_url} alt="プロフィール画像" className="chat-avatar" />
                ) : (
                  <div className="chat-avatar" />
                )}
                <div>
                  <h2 className="text-lg font-semibold">{dm.partner.user_name}</h2>
                  {dm.latest_message ? (
                    <p className="text-sm text-gray-600 truncate">
                      {dm.latest_message.message_type === 'image'
                        ? '画像メッセージ'
                        : dm.latest_message.content}
                    </p>
                  ) : (
                    <p className="text-sm text-gray-400 italic">まだメッセージはありません</p>
                  )}
                </div>
              </div>
            </li>
          ))}

        </ul>
      )}
    </div>
  )
}

export default TalkListPage