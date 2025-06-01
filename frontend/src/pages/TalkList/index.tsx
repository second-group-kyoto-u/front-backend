import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getJoinedEvents } from '@/api/event'
import { getDirectMessageOverview } from '@/api/friend'
import styles from './talklist.module.css'

interface Event {
  id: string
  title: string
  description: string // Keeping for potential use, but will hide visually
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

// Unified chat item interface for rendering
interface ChatItem {
  id: string
  type: 'event' | 'dm'
  name: string
  imageUrl: string | null
  latestMessage: string
  timestamp: string // Added for timestamp display
  unreadCount?: number // Added for unread count
}

const TalkListPage = () => {
  const [chatList, setChatList] = useState<ChatItem[]>([]) // Unified list
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

        // Map events to ChatItem format
        const eventChats: ChatItem[] = eventRes.events.map((event) => ({
          id: event.id,
          type: 'event',
          name: event.title,
          // Placeholder image or logic to fetch event image if available
          imageUrl: null, // Assuming no event image for now based on original data
          latestMessage: event.description || 'タップして会話を開始', // Use description as latest message for events
          timestamp: '15:30', // Placeholder, ideally from actual event activity
          unreadCount: Math.floor(Math.random() * 5), // Random for demo, replace with actual
        }))

        // Map DMs to ChatItem format
        const dmChats: ChatItem[] = dmRes.map((dm) => ({
          id: dm.partner_id,
          type: 'dm',
          name: dm.partner.user_name,
          imageUrl: dm.partner.user_image_url,
          latestMessage: dm.latest_message
            ? dm.latest_message.message_type === 'image'
              ? '画像メッセージ'
              : dm.latest_message.content
            : 'まだメッセージはありません',
          timestamp: dm.latest_message
            ? new Date(dm.latest_message.sent_at).toLocaleTimeString([], {
                hour: '2-digit',
                minute: '2-digit',
              })
            : '',
          unreadCount: dm.partner_id === 'some-id-with-unread' ? 3 : undefined, // Example for unread count
        }))

        // Combine and sort by timestamp (latest first)
        // For simplicity, we'll just concatenate them for now,
        // but real implementation would sort by latest message timestamp across all chat types.
        setChatList([...eventChats, ...dmChats].sort((a, b) => b.timestamp.localeCompare(a.timestamp)))

      } catch (err) {
        console.error('データ取得失敗:', err)
        setError('データの取得に失敗しました。')
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [])

  const handleChatItemClick = (item: ChatItem) => {
    if (item.type === 'event') {
      navigate(`/event/${item.id}/talk`, { state: { from: 'talkList' } })
    } else {
      navigate(`/dm/${item.id}`)
    }
  }

  if (loading) return <div className={styles.message}>読み込み中...</div>
  if (error) return <div className={styles.error}>{error}</div>

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h1 className={styles.pageTitle}>トーク</h1>
      </div>
      <div className={styles.searchBarContainer}>
        <div className={styles.searchIcon}></div> {/* Placeholder for search icon */}
        <input
          type="text"
          placeholder="キーワードで検索"
          className={styles.searchInput}
        />
      </div>

      {chatList.length === 0 ? (
        <p className={styles.message}>会話がありません。</p>
      ) : (
        <ul className={styles.chatList}>
          {chatList.map((item) => (
            <li
              key={item.id + item.type} // Unique key for combined list
              className={styles.chatItem}
              onClick={() => handleChatItemClick(item)}
            >
              <div className={styles.chatItemContent}>
                {item.imageUrl ? (
                  <img
                    src={item.imageUrl}
                    alt={`${item.name}のプロフィール画像`}
                    className={styles.chatAvatar}
                  />
                ) : (
                  <div className={styles.chatAvatarPlaceholder}></div>
                )}
                <div className={styles.chatText}>
                  <h2 className={styles.chatTitle}>{item.name}</h2>
                  <p className={styles.chatMessage}>{item.latestMessage}</p>
                </div>
                <div className={styles.chatMeta}>
                  <span className={styles.timestamp}>{item.timestamp}</span>
                  {item.unreadCount && item.unreadCount > 0 && (
                    <div className={styles.unreadCount}>{item.unreadCount}</div>
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

export default TalkListPage;