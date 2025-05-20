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
        // It's good practice to log the actual error for debugging.
        console.error('Failed to fetch data:', err)
        setError('データの取得に失敗しました')
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [])

  const handleEventClick = (eventId: string) => {
    // Template literals for string interpolation are preferred for readability.
    navigate(`/event/${eventId}/talk`)
  }

  const handleDmClick = (userId: string) => {
    // Template literals for string interpolation are preferred for readability.
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
        <ul className="chat-list">
          {events.map((event) => (
            <li
              key={event.id}
              className="chat-item"
              onClick={() => handleEventClick(event.id)}
            >
              <h2 className="text-lg font-semibold">{event.title}</h2>
              <p className="text-sm text-gray-600">{event.description}</p>
            </li>
          ))}
        </ul>
      )}

      <h1 className="text-2xl font-bold mb-4 mt-8">ダイレクトメッセージ</h1> {/* Added margin-top for spacing */}
      {dmList.length === 0 ? (
        <p>ダイレクトメッセージはありません。</p>
      ) : (
        <ul className="chat-list">
          {dmList.map((dm) => (
            <li
              key={dm.partner_id}
              className="chat-item"
              onClick={() => handleDmClick(dm.partner_id)}
            >
              {/* Changed class name for clarity and consistency */}
              <div className="chat-item-content">
                {dm.partner.user_image_url ? (
                  <img src={dm.partner.user_image_url} alt={`${dm.partner.user_name}のプロフィール画像`} className="chat-avatar" />
                ) : (
                  // Added a more descriptive alt text for accessibility
                  <div className="chat-avatar-placeholder" /> // Renamed for clarity
                )}
                <div className="chat-content"> {/* Added a wrapper for text content */}
                  <h2 className="text-lg font-semibold">{dm.partner.user_name}</h2>
                  {dm.latest_message ? (
                    <p className="chat-message">
                      {dm.latest_message.message_type === 'image'
                        ? '画像メッセージ'
                        : dm.latest_message.content}
                    </p>
                  ) : (
                    <p className="chat-message empty">まだメッセージはありません</p>
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