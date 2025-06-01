import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getJoinedEvents } from '@/api/event'
import { getDirectMessageOverview } from '@/api/friend'
import styles from './talklist.module.css'

interface Event {
  id: string
  title: string
  description: string
}

interface DirectMessageOverview {
  partner_id: string
  partner: {
    id: string
    user_name: string
    user_image_url: string | null
    profile_message: string | null
    is_certificated: boolean
  }
  latest_message: {
    content: string
    sent_at: string
    message_type: 'text' | 'image' | 'system' | 'bot'
  }
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
          getDirectMessageOverview(),
        ])
        setEvents(eventRes.events)
        setDmList(dmRes)
      } catch (err) {
        console.error('データ取得失敗:', err)
        setError('データの取得に失敗しました。')
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

  if (loading) return <div className={styles.message}>読み込み中...</div>
  if (error) return <div className={styles.error}>{error}</div>

  return (
    <div className={styles.container}>
      <h1 className={styles.sectionTitle}>イベントトーク</h1>
      {events.length === 0 ? (
        <p className={styles.message}>参加中のイベントはありません。</p>
      ) : (
        <ul className={styles.chatList}>
          {events.map((event) => (
            <li
              key={event.id}
              className={styles.chatItem}
              onClick={() => handleEventClick(event.id)}
            >
              <h2 className={styles.chatTitle}>{event.title}</h2>
              <p className={styles.chatDescription}>{event.description}</p>
            </li>
          ))}
        </ul>
      )}

      <h1 className={styles.sectionTitle}>ダイレクトメッセージ</h1>
      <button
        className={styles.dmButton}
        onClick={() => navigate('/friend/create-DMpage')}
      >
        新しいDMを開始
      </button>

      {dmList.length === 0 ? (
        <p className={styles.message}>ダイレクトメッセージはありません。</p>
      ) : (
        <ul className={styles.chatList}>
          {dmList.map((dm) => (
            <li
              key={dm.partner_id}
              className={styles.chatItem}
              onClick={() => handleDmClick(dm.partner_id)}
            >
              <div className={styles.chatItemContent}>
                {dm.partner.user_image_url ? (
                  <img
                    src={dm.partner.user_image_url}
                    alt={`${dm.partner.user_name}のプロフィール画像`}
                    className={styles.chatAvatar}
                  />
                ) : (
                  <div className={styles.chatAvatarPlaceholder}></div>
                )}
                <div className={styles.chatText}>
                  <h2 className={styles.chatTitle}>{dm.partner.user_name}</h2>
                  <p className={styles.chatMessage}>
                    {dm.latest_message
                      ? dm.latest_message.message_type === 'image'
                        ? '画像メッセージ'
                        : dm.latest_message.content
                      : 'まだメッセージはありません'}
                  </p>
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
