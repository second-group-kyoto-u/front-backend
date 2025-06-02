import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getJoinedEvents, EventType } from '@/api/event'
import { getDirectMessageOverview } from '@/api/friend'
import styles from './talklist.module.css'

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

  // 画像URLを処理する関数
  const processImageUrl = (url: string | null): string | null => {
    if (!url) return null;
    
    // MinIOのURLを修正
    if (url.includes('localhost:9000')) {
      // URLがlocalhostのMinioを指している場合
      const parsed = new URL(url);
      const newUrl = `http://${window.location.hostname}:9000${parsed.pathname}`;
      return newUrl;
    }
    
    // その他のローカル環境のURL修正
    if (url.includes('127.0.0.1:9000')) {
      const parsed = new URL(url);
      const newUrl = `http://${window.location.hostname}:9000${parsed.pathname}`;
      return newUrl;
    }
    
    return url;
  }

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [eventRes, dmRes] = await Promise.all([
          getJoinedEvents(),
          getDirectMessageOverview(),
        ])

        console.log('Events response:', eventRes); // デバッグ用
        console.log('DM response:', dmRes); // デバッグ用

        // Map events to ChatItem format
        const eventChats: ChatItem[] = eventRes.events.map((event: EventType) => {
          console.log('Processing event:', event.id, 'image_url:', event.image_url); // デバッグ用
          const processedImageUrl = processImageUrl(event.image_url);
          console.log('Processed image URL:', processedImageUrl); // デバッグ用
          
          return {
            id: event.id,
            type: 'event',
            name: event.title,
            imageUrl: processedImageUrl, // Use actual event image
            latestMessage: event.description || 'タップして会話を開始', // Use description as latest message for events
            timestamp: event.published_at 
              ? new Date(event.published_at).toLocaleTimeString([], {
                  hour: '2-digit',
                  minute: '2-digit',
                })
              : '15:30', // Fallback placeholder
            unreadCount: undefined, // TODO: 実際の未読数をAPIから取得予定
          }
        })

        // Map DMs to ChatItem format
        const dmChats: ChatItem[] = dmRes.map((dm: DirectMessageOverview) => ({
          id: dm.partner_id,
          type: 'dm',
          name: dm.partner.user_name,
          imageUrl: processImageUrl(dm.partner.user_image_url),
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
          unreadCount: undefined, // TODO: 実際の未読数をAPIから取得予定
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

  // 画像のロード時のエラーハンドリング
  const handleImageError = (e: any) => {
    const target = e.target as HTMLImageElement;
    console.log('Image load error for:', target.src); // デバッグ用
    target.style.display = 'none'; // 画像を非表示にしてプレースホルダーを表示
  }

  if (loading) return <div className={styles.message}>読み込み中...</div>
  if (error) return <div className={styles.error}>{error}</div>

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h1 className={styles.pageTitle}>トーク</h1>
      </div>
      <div className={styles.searchBarContainer}>
        <div className={styles.searchIcon}>🔍</div> {/* Search icon */}
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
                <div className={styles.avatarContainer}>
                  {item.imageUrl ? (
                    <img
                      src={item.imageUrl}
                      alt={`${item.name}のプロフィール画像`}
                      className={`${styles.chatAvatar} ${item.type === 'event' ? styles.eventAvatar : ''}`}
                      onError={handleImageError}
                    />
                  ) : null}
                  <div className={`${styles.chatAvatarPlaceholder} ${item.type === 'event' ? styles.eventPlaceholder : ''} ${item.imageUrl ? styles.hidden : ''}`}>
                    {item.type === 'event' ? '📅' : '👤'}
                  </div>
                </div>
                <div className={styles.chatText}>
                  <h2 className={styles.chatTitle}>{item.name}</h2>
                  <p className={styles.chatMessage}>{item.latestMessage}</p>
                </div>
                <div className={styles.chatMeta}>
                  <span className={styles.timestamp}>{item.timestamp}</span>
                  {item.unreadCount !== undefined && item.unreadCount > 0 && (
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