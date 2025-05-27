/*
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getJoinedEvents } from '@/api/event'
import { getDirectMessageOverview } from '@/api/friend'
import './talklist.module.css'

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

      <h1 className="text-2xl font-bold mb-4 mt-8">ダイレクトメッセージ</h1> {/* Added margin-top for spacing }
        <button
          className="bg-blue-500 hover:bg-blue-600 text-white font-bold py-2 px-4 rounded mb-4"
          onClick={() => navigate('/friend/create-DMpage')}
        >
          新しいDMを開始
        </button>

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
              <div className="chat-item-content">
                {dm.partner.user_image_url ? (
                  <img src={dm.partner.user_image_url} alt={`${dm.partner.user_name}のプロフィール画像`} className="chat-avatar" />
                ) : (
                  // Added a more descriptive alt text for accessibility
                  <div className="chat-avatar-placeholder" /> // Renamed for clarity
                )}
                <div className="chat-content"> 
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
*/





/*

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
*/

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
      navigate(`/event/${item.id}/talk`)
    } else {
      navigate(`/friend/${item.id}/dm`)
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