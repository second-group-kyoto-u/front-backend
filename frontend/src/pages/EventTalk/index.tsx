import React, { useEffect, useState, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { sendEventMessage, getEvent, startEvent, endEvent, generateBotTrivia } from '@/api/event'
import { uploadImage } from '@/api/upload'
import { useAuth } from '@/hooks/useAuth'
import type { EventType } from '@/api/event'
import type { ExtendedEventMessageType } from '@/types/interface'
import styles from './EventTalk.module.css'

function EventTalkPage() {
  const { eventId } = useParams<{ eventId: string }>()
  const { token } = useAuth()
  const navigate = useNavigate()
  const messagesEndRef = useRef<HTMLDivElement | null>(null)
  const fileInputRef = useRef<HTMLInputElement | null>(null)

  const [eventData, setEventData] = useState<EventType | null>(null)
  const [messages, setMessages] = useState<ExtendedEventMessageType[]>([])
  const [newMessage, setNewMessage] = useState('')
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [selectedFilePreview, setSelectedFilePreview] = useState<string | null>(null)
  const [sending, setSending] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [uploadProgress, setUploadProgress] = useState(0)
  const [isAuthor, setIsAuthor] = useState(false)
  const [isSendingTrivia, setIsSendingTrivia] = useState(false)
  const [userLocation, setUserLocation] = useState<{latitude: number, longitude: number} | null>(null)

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
      // 定期的な更新（30秒ごと）
      const intervalId = setInterval(fetchMessages, 30000)
      return () => clearInterval(intervalId)
    }
  }, [eventId])

  // 選択されたファイルがある場合、プレビューを生成
  useEffect(() => {
    if (selectedFile) {
      const reader = new FileReader();
      reader.onloadend = () => {
        setSelectedFilePreview(reader.result as string);
      };
      reader.readAsDataURL(selectedFile);
    } else {
      setSelectedFilePreview(null);
    }
  }, [selectedFile]);

  const fetchMessages = async () => {
    if (!eventId) return
    setLoading(true)
    try {
      const data = await getEvent(eventId)
      setEventData(data.event)
      
      // メッセージにsender_user_idを追加
      const processedMessages = data.messages.map((msg: any) => ({
        ...msg,
        sender_user_id: msg.sender?.id
      }));
      
      setMessages(processedMessages)
      
      // 自分がイベント作成者かチェック
      if (token && data.event && data.event.author) {
        const currentUserId = getUserIdFromToken(token)
        setIsAuthor(currentUserId === data.event.author.id)
      }
    } catch (err: any) {
      console.error('メッセージ取得エラー:', err)
      setError('メッセージの取得に失敗しました')
    } finally {
      setLoading(false)
    }
  }

  // イベント開始
  const handleStartEvent = async () => {
    if (!eventId || !token) return
    
    try {
      setSending(true)
      await startEvent(eventId)
      
      // システムメッセージを送信
      await sendEventMessage(eventId, {
        content: 'イベントが開始されました',
        message_type: 'system'
      })
      
      // botメッセージも送信
      await sendEventMessage(eventId, {
        content: 'イベント開始時刻になりました。盛り上がっていきましょう！',
        message_type: 'bot'
      })
      
      await fetchMessages()
    } catch (err: any) {
      console.error('イベント開始エラー:', err)
      setError('イベントの開始に失敗しました')
    } finally {
      setSending(false)
    }
  }
  
  // イベント終了
  const handleEndEvent = async () => {
    if (!eventId || !token) return
    
    try {
      setSending(true)
      await endEvent(eventId)
      
      // システムメッセージを送信
      await sendEventMessage(eventId, {
        content: 'イベントが終了しました',
        message_type: 'system'
      })
      
      // botメッセージも送信
      await sendEventMessage(eventId, {
        content: 'イベントが終了しました。ご参加ありがとうございました！',
        message_type: 'bot'
      })
      
      await fetchMessages()
    } catch (err: any) {
      console.error('イベント終了エラー:', err)
      setError('イベントの終了に失敗しました')
    } finally {
      setSending(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!eventId || !token) {
      setError('ログインが必要です')
      return
    }
    if ((!selectedFile && !newMessage.trim()) || sending) return

    setSending(true)
    setError('')
    setUploadProgress(0)
    
    try {
      if (selectedFile) {
        // ファイルサイズチェック（5MB制限）
        if (selectedFile.size > 5 * 1024 * 1024) {
          throw new Error('画像サイズは5MB以下にしてください')
        }
        
        // 画像送信
        setUploadProgress(10)
        const uploadRes = await uploadImage(selectedFile, token)
        setUploadProgress(70)
        
        if (!uploadRes || !uploadRes.image || !uploadRes.image.id) {
          throw new Error('画像のアップロードに失敗しました')
        }
        
        // イベントメッセージとして画像IDを送信
        await sendEventMessage(eventId, { 
          image_id: uploadRes.image.id, 
          message_type: 'image' 
        })
        setUploadProgress(100)
        setSelectedFile(null)
        setSelectedFilePreview(null)
      } else if (newMessage.trim()) {
        // テキスト送信
        await sendEventMessage(eventId, { 
          content: newMessage.trim(), 
          message_type: 'text' 
        })
      }
      setNewMessage('')
      await fetchMessages()
    } catch (err: any) {
      console.error('送信エラー:', err)
      const errorMessage = err.response?.data?.message || err.message || 'メッセージ送信に失敗しました'
      setError(errorMessage)
    } finally {
      setSending(false)
      setUploadProgress(0)
    }
  }

  const handleAttachClick = () => {
    fileInputRef.current?.click()
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0] || null
    
    if (file) {
      // 画像タイプのチェック
      if (!file.type.startsWith('image/')) {
        setError('画像ファイルのみアップロードできます')
        return
      }
      
      // ファイルサイズのチェック
      if (file.size > 5 * 1024 * 1024) {
        setError('画像サイズは5MB以下にしてください')
        return
      }
      
      setSelectedFile(file)
      setError('')
    }
    
    // ファイル選択後に入力をリセット（同じファイルを選択可能にする）
    if (e.target) e.target.value = ''
  }

  const cancelFileSelection = () => {
    setSelectedFile(null)
    setSelectedFilePreview(null)
    setError('')
  }

  // ユーザー名の頭文字を取得（アバターに表示）
  const getUserInitial = (name: string | undefined): string => {
    if (!name) return '?'
    return name.charAt(0).toUpperCase()
  }

  // ユーザー名からアバターの背景色を生成
  const getUserColor = (name: string | undefined): string => {
    if (!name) return '#cccccc'
    const hash = name.split('').reduce((acc, char) => char.charCodeAt(0) + ((acc << 5) - acc), 0)
    const hue = Math.abs(hash) % 360
    return `hsl(${hue}, 70%, 80%)`
  }

  // ログイン中のユーザーがそのメッセージの送信者かどうか
  const isCurrentUser = (senderId: string | undefined): boolean => {
    if (!token || !senderId) return false
    // メッセージの送信者IDがログインユーザーのIDに一致する場合
    const currentUserId = getUserIdFromToken(token)
    return currentUserId !== undefined && currentUserId === senderId
  }

  // トークンからユーザーIDを取得
  const getUserIdFromToken = (token: string): string | undefined => {
    try {
      // JWTの2つ目のセグメント（ペイロード）をデコード
      const payload = token.split('.')[1]
      const decoded = JSON.parse(atob(payload))
      return decoded.user_id || undefined
    } catch (error) {
      return undefined
    }
  }

  // タイムスタンプをフォーマット（UTCからJSTに変換）
  const formatTimestamp = (timestamp: string | undefined): string => {
    if (!timestamp) return ''
    
    // UTCの日時を解析
    const date = new Date(timestamp)
    
    // 日本時間に設定（+9時間）
    const jstDate = new Date(date.getTime() + 9 * 60 * 60 * 1000)
    
    // 日本語形式で時刻を返す
    return jstDate.toLocaleTimeString('ja-JP', { hour: '2-digit', minute: '2-digit' })
  }
  // 画像のレンダリング
  const renderImage = (imageUrl: string | null | undefined) => {
    if (typeof imageUrl === 'string' && imageUrl.trim() !== '') {
      return <img src={imageUrl} alt="投稿画像" loading="lazy" />
    }
    return <div className={styles.emptyImage}>画像を読み込めません</div>
  }

  // 位置情報を取得する
  const getUserLocation = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setUserLocation({
            latitude: position.coords.latitude,
            longitude: position.coords.longitude
          })
        },
        (error) => {
          console.error('位置情報の取得に失敗しました:', error)
          // 豆知識生成時に再取得するので、ここではエラーメッセージを表示しない
        },
        { timeout: 10000, maximumAge: 60000 } // 10秒のタイムアウト、1分以内のキャッシュは許可
      )
    }
  }
  
  // コンポーネントマウント時に位置情報を取得
  useEffect(() => {
    getUserLocation()
  }, [])
  
  // 豆知識生成ハンドラー
  const handleGenerateTrivia = async (type: 'trivia' | 'conversation' = 'trivia') => {
    if (!eventId || !token) {
      setError('ログインが必要です')
      return
    }
    
    try {
      setIsSendingTrivia(true)
      setError('')
      
      // 位置情報を取得するPromiseを作成
      const getLocationPromise = new Promise<{latitude: number, longitude: number} | null>((resolve) => {
        if (navigator.geolocation) {
          navigator.geolocation.getCurrentPosition(
            (position) => {
              const location = {
                latitude: position.coords.latitude,
                longitude: position.coords.longitude
              }
              setUserLocation(location) // 状態も更新
              resolve(location)
            },
            (error) => {
              console.error('位置情報の取得に失敗しました:', error)
              // エラーの場合はnullを返すが、エラーメッセージは表示しない（豆知識生成は続行）
              resolve(null)
            },
            { timeout: 5000, maximumAge: 60000 } // 5秒のタイムアウト、1分以内のキャッシュは許可
          )
        } else {
          resolve(null)
        }
      })
      
      // 位置情報を取得してから豆知識を生成
      const location = await getLocationPromise
      
      // 位置情報を含めたリクエストデータ
      const requestData: {
        type: 'trivia' | 'conversation';
        location?: { latitude: number; longitude: number };
      } = { type }
      
      // 位置情報があれば追加
      if (location) {
        requestData.location = location
      }
      
      await generateBotTrivia(eventId, requestData)
      await fetchMessages()
      
    } catch (err: any) {
      console.error('豆知識生成エラー:', err)
      const errorMessage = err.response?.data?.message || err.message || '豆知識の生成に失敗しました'
      setError(errorMessage)
    } finally {
      setIsSendingTrivia(false)
    }
  }

  if (loading && !messages.length) {
    return (
      <div className={styles.loadingSpinner}>
        読み込み中...
      </div>
    )
  }

  return (
    <div className={styles.pageContainer}>
      <div className={styles.header}>
        <button 
          className={styles.backButton} 
          onClick={() => navigate(`/event/${eventId}`)}
          aria-label="戻る"
        >
          ←
        </button>
        <h1 className={styles.title}>{eventData?.title || 'トークルーム'}</h1>
        <button className={styles.menuButton} aria-label="メニュー">⋮</button>
      </div>

      {/* イベント開始/終了ボタン（イベント作成者のみ表示） */}
      {isAuthor && eventData && (
        <div className={styles.eventControls}>
          {eventData.status === 'pending' && (
            <button 
              className={`${styles.eventControlButton} ${styles.startButton}`}
              onClick={handleStartEvent}
              disabled={sending}
            >
              <span className={styles.eventButtonIcon}>▶</span>
              イベントを開始する
            </button>
          )}
          
          {eventData.status === 'started' && (
            <button 
              className={`${styles.eventControlButton} ${styles.endButton}`}
              onClick={handleEndEvent}
              disabled={sending}
            >
              <span className={styles.eventButtonIcon}>■</span>
              イベントを終了する
            </button>
          )}
        </div>
      )}

      {/* ボットの豆知識ボタン */}
      {eventData && eventData.status === 'started' && (
        <div className={styles.botControls}>
          <button 
            className={`${styles.botControlButton} ${styles.triviaButton}`}
            onClick={() => handleGenerateTrivia('trivia')} 
            disabled={isSendingTrivia}
          >
            <span className={styles.botButtonIcon}>📝</span>
            ボットの豆知識
          </button>
          <button 
            className={`${styles.botControlButton} ${styles.conversationButton}`}
            onClick={() => handleGenerateTrivia('conversation')} 
            disabled={isSendingTrivia}
          >
            <span className={styles.botButtonIcon}>🤔</span>
            会話のきっかけ
          </button>
        </div>
      )}

      <div className={styles.messageList}>
        {error && <div className={styles.errorMessage}>{error}</div>}
        
        {messages.length === 0 && !loading && (
          <div className={styles.noMessages}>
            メッセージはまだありません。最初のメッセージを送信しましょう！
          </div>
        )}

        {messages.map((msg) => {
          if (msg.message_type === 'system') {
            // システムメッセージ
            return (
              <div key={msg.id} className={styles.systemMessage}>
                {msg.content}
              </div>
            );
          } else if (msg.message_type === 'bot') {
            // botメッセージ
            return (
              <div key={msg.id} className={styles.botMessage}>
                <div className={styles.botMessageContainer}>
                  <div style={{ display: 'flex', alignItems: 'flex-start' }}>
                    <div className={styles.botAvatar}>B</div>
                    <div className={styles.botContent}>
                      <div className={styles.botName}>bot</div>
                      <div>{msg.content}</div>
                      <div className={styles.botTimestamp}>{formatTimestamp(msg.timestamp || undefined)}</div>
                    </div>
                  </div>
                </div>
              </div>
            );
          } else {
            // 通常メッセージ
            return (
              <div 
                key={msg.id} 
                className={`${styles.messageItem} ${isCurrentUser(msg.sender_user_id) ? styles.sent : styles.received}`}
              >
                {/* アバター（自分のメッセージには表示しない） */}
                {!isCurrentUser(msg.sender_user_id) && (
                  <div 
                    className={styles.avatar}
                    style={{ backgroundColor: getUserColor(msg.sender?.user_name) }}
                  >
                    {getUserInitial(msg.sender?.user_name)}
                  </div>
                )}

                <div className={`${styles.messageContent} ${isCurrentUser(msg.sender_user_id) ? styles.sent : ''}`}>
                  {/* 送信者名（自分のメッセージには表示しない） */}
                  {!isCurrentUser(msg.sender_user_id) && (
                    <div className={styles.senderName}>{msg.sender?.user_name || '不明なユーザー'}</div>
                  )}

                  {/* メッセージ内容 */}
                  {msg.message_type === 'text' ? (
                    <div className={styles.messageBubble}>{msg.content}</div>
                  ) : (
                    <div className={styles.imageMessage}>
                      {renderImage(msg.image_url)}
                    </div>
                  )}

                  {/* タイムスタンプ */}
                  <div className={styles.timestamp}>{formatTimestamp(msg.timestamp || undefined)}</div>
                </div>
              </div>
            );
          }
        })}
        <div ref={messagesEndRef} />
      </div>

      {/* アップロード進捗表示 */}
      {uploadProgress > 0 && uploadProgress < 100 && (
        <div className={styles.uploadProgress}>
          <div 
            className={styles.uploadProgressBar} 
            style={{ width: `${uploadProgress}%` }}
          ></div>
          <span className={styles.uploadProgressText}>画像をアップロード中...</span>
        </div>
      )}

      {/* 選択ファイルの表示 */}
      {selectedFile && (
        <div className={styles.selectedFile}>
          {selectedFilePreview && (
            <img src={selectedFilePreview} alt="プレビュー" className={styles.imagePreview} />
          )}
          <span className={styles.selectedFileName}>{selectedFile.name}</span>
          <button 
            onClick={cancelFileSelection} 
            className={styles.cancelFileButton}
            aria-label="ファイル選択をキャンセル"
          >
            ×
          </button>
        </div>
      )}

      <form onSubmit={handleSubmit} className={styles.inputArea}>
        <button 
          type="button" 
          onClick={handleAttachClick} 
          className={styles.attachButton}
          aria-label="ファイルを添付"
          disabled={sending}
        >
          📎
        </button>
        <input
          type="file"
          accept="image/*"
          ref={fileInputRef}
          onChange={handleFileChange}
          className={styles.fileInput}
          disabled={sending}
        />
        <textarea
          value={newMessage}
          onChange={(e: { target: { value: string } }) => setNewMessage(e.target.value)}
          placeholder="メッセージを入力"
          className={styles.messageInput}
          disabled={!!selectedFile || sending}
          onKeyDown={(e: { key: string; shiftKey: boolean; preventDefault: () => void }) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault()
              handleSubmit({} as React.FormEvent)
            }
          }}
        />
        <button 
          type="submit" 
          className={styles.sendButton}
          disabled={(!newMessage.trim() && !selectedFile) || sending}
          aria-label="送信"
        >
          {sending ? '...' : '→'}
        </button>
      </form>
    </div>
  )
}

export default EventTalkPage
