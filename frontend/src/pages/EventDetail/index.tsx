import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { getEvent, getEventMembers, joinEvent } from '@/api/event'
import { useAuth } from '@/hooks/useAuth'
import type { EventType, EventMemberType } from '@/api/event'
import styles from './EventDetail.module.css'

// 認証情報取得の問題を修正するためのヘルパー
import { getAuthHeader } from '@/api/auth/helpers'

function EventDetailPage() {
  const { eventId } = useParams<{ eventId: string}>()
  const { isAuthenticated, token } = useAuth()  // トークンも取得
  const navigate = useNavigate()

  const [eventData, setEventData] = useState<EventType | null>(null)
  const [members, setMembers] = useState<EventMemberType[]>([])
  const [isJoined, setIsJoined] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [joining, setJoining] = useState(false)
  const [membersLoading, setMembersLoading] = useState(false)

  useEffect(() => {
    if (eventId) {
      fetchEventDetail()
    }
  }, [eventId, token]) // トークンが変わったときも再取得

  const fetchEventDetail = async () => {
    if (!eventId) return
    setLoading(true)
    try {
      const data = await getEvent(eventId)
      console.log('イベント詳細データ:', data)
      setEventData(data.event)
      setIsJoined(data.is_joined)
      
      // 参加者がいる場合のみメンバー情報取得
      if (data.event.current_persons > 0) {
        fetchEventMembers(eventId)
      }
    } catch (err: any) {
      console.error('イベント詳細取得エラー:', err)
      setError('イベントの詳細取得に失敗しました')
    } finally {
      setLoading(false)
    }
  }

  // APIリクエストがタイムアウトした場合のハンドリングのためのユーティリティ関数
  const withTimeout = <T,>(promise: Promise<T>, timeoutMs: number, fallback: T): Promise<T> => {
    let timer: number;
    return Promise.race([
      promise,
      new Promise<T>((resolve) => {
        timer = setTimeout(() => {
          console.warn(`リクエストが${timeoutMs}msでタイムアウトしました。フォールバック値を使用します。`);
          resolve(fallback);
        }, timeoutMs) as unknown as number;
      })
    ]).finally(() => clearTimeout(timer));
  };
  
  const fetchEventMembers = async (id: string) => {
    setMembersLoading(true);
    try {
      console.log('メンバー情報取得開始', id);
      
      // 認証トークン確認
      const authHeader = getAuthHeader();
      const hasAuth = Object.keys(authHeader).length > 0;
      console.log('認証あり:', hasAuth, '認証ヘッダー:', authHeader);
      
      if (!hasAuth) {
        console.warn('認証トークンがありません。ダミーデータを生成します。');
        
        // 未認証の場合、すぐにダミーデータを設定
        if (eventData) {
          // イベントの参加人数分のダミーを生成
          const dummyMembers = Array.from({ length: eventData.current_persons }).map((_, index) => ({
            user_id: `dummy-${index}`,
            event_id: id,
            joined_at: new Date().toISOString(),
            user: {
              id: `dummy-${index}`,
              user_name: `参加者${index + 1}`,
              user_image_url: null,
              profile_message: null,
              is_certificated: false
            }
          }));
          setMembers(dummyMembers as EventMemberType[]);
          setMembersLoading(false);
          return;
        }
      }
      
      // タイムアウト付きでAPIを呼び出し
      const membersData = await withTimeout(
        getEventMembers(id),
        5000, // 5秒でタイムアウト
        // タイムアウト時のフォールバック値
        eventData?.current_persons ? 
          { 
            members: Array.from({ length: eventData.current_persons }).map((_, index) => ({
              user_id: `timeout-${index}`,
              event_id: id,
              joined_at: new Date().toISOString(),
              user: { 
                id: `timeout-${index}`, 
                user_name: `参加者${index + 1}`, 
                user_image_url: null,
                profile_message: null,
                is_certificated: false 
              }
            }))
          } 
          : false
      );
      
      console.log('取得したメンバー情報:', membersData);
      
      // APIの応答がfalseの場合（認証問題の可能性）
      if (membersData === false) {
        console.error('メンバー情報取得に失敗しました。認証トークンを確認してください。');
        
        // バックエンドの実装に応じた対応
        if (eventData) {
          // 暫定対応：ダミーユーザーを生成
          const dummyMembers = Array.from({ length: eventData.current_persons }).map((_, index) => ({
            user_id: `dummy-${index}`,
            event_id: id,
            joined_at: new Date().toISOString(),
            user: {
              id: `dummy-${index}`,
              user_name: `参加者${index + 1}`,
              user_image_url: null,
              profile_message: null,
              is_certificated: false
            }
          }));
          setMembers(dummyMembers as EventMemberType[]);
        }
      } 
      // 標準的なレスポンス形式
      else if (membersData && typeof membersData.members !== 'undefined') {
        if (Array.isArray(membersData.members)) {
          console.log('セットするメンバー:', membersData.members.length, '人')
          
          // メンバーのuser_image_urlを詳しくログ出力
          membersData.members.forEach((member: EventMemberType, index: number) => {
            console.log(`メンバー[${index}]のデータ:`, {
              user_id: member.user_id,
              user_name: member.user?.user_name,
              user_image_url: member.user?.user_image_url,
              hasUserObject: !!member.user
            });
          });
          
          setMembers(membersData.members)
        } else {
          console.warn('membersData.membersが配列ではありません:', membersData.members);
          setMembers([]);
        }
      } 
      // 直接配列が返ってくる形式
      else if (Array.isArray(membersData)) {
        console.log('メンバーデータが直接配列で返されました:', membersData.length, '人');
        setMembers(membersData as EventMemberType[]);
      } 
      // その他の形式
      else {
        console.warn('サポートされていないメンバーデータ形式:', membersData);
        setMembers([]);
      }
    } catch (err) {
      console.error('イベントメンバー取得エラー:', err);
      
      // エラー時はダミーデータを生成
      if (eventData?.current_persons) {
        const dummyMembers = Array.from({ length: eventData.current_persons }).map((_, index) => ({
          user_id: `error-${index}`,
          event_id: id,
          joined_at: new Date().toISOString(),
          user: {
            id: `error-${index}`,
            user_name: `参加者${index + 1}`,
            user_image_url: null,
            profile_message: null,
            is_certificated: false
          }
        }));
        setMembers(dummyMembers as EventMemberType[]);
      } else {
        setMembers([]);
      }
    } finally {
      setMembersLoading(false);
    }
  }

  const handleJoinEvent = async () => {
    if (!eventId || !isAuthenticated) {
      // 未認証の場合はログインページに遷移
      // メッセージを含めて遷移先情報を追加
      navigate('/login', { 
        state: { 
          from: `/event/${eventId}`,
          message: 'イベントに参加するにはログインが必要です'
        } 
      })
      return
    }

    setJoining(true)
    try {
      // イベントに参加
      await joinEvent(eventId)
      setIsJoined(true)
      
      // 詳細情報を更新
      await fetchEventDetail()
      
      // 直接トークルームに遷移
      navigate(`/event/${eventId}/talk`)
    } catch (err: any) {
      console.error('イベント参加エラー:', err)
      if (err.response?.data?.error) {
        setError(err.response.data.error)
      } else {
        setError('イベントへの参加に失敗しました')
      }
    } finally {
      setJoining(false)
    }
  }

  const handleBack = () => {
    navigate('/events')
  }

  const goToTalkRoom = () => {
    // 直接トークルームに遷移
    navigate(`/event/${eventId}/talk`)
  }

  // イベントのタイトルを取得（title か message の適切な方を使用）
  const getTitle = () => {
    return eventData?.title || eventData?.message || '無題のイベント';
  };

  // 画像URLを処理する関数
  const processImageUrl = (url: string | null): string => {
    if (!url) return 'https://via.placeholder.com/400x200?text=No+Image';
    
    // MinIOのURLを修正（内部ネットワークのURLを外部アクセス可能なURLに変換）
    if (url.includes(':9000/')) {
      // MinIOのURLの場合、nginxプロキシ経由に変換
      const urlParts = url.split(':9000/');
      if (urlParts.length === 2) {
        const newUrl = `http://${window.location.hostname}/minio/${urlParts[1]}`;
        return newUrl;
      }
    }
    
    return url;
  };

  // ユーザーアイコンのURLを処理する関数
  const processUserImageUrl = (url: string | null): string => {
    if (!url) return 'https://via.placeholder.com/50?text=User';
    
    // 相対パスの場合は絶対パスに変換
    if (url.startsWith('/')) {
      const processedUrl = `${window.location.origin}${url}`;
      console.log('相対パスを絶対パスに変換:', processedUrl);
      return processedUrl;
    }
    
    // MinIOのURLを修正（内部ネットワークのURLを外部アクセス可能なURLに変換）
    if (url.includes(':9000/')) {
      try {
        const urlParts = url.split(':9000/');
        if (urlParts.length === 2) {
          const newUrl = `http://${window.location.hostname}/minio/${urlParts[1]}`;
          console.log('MinIO URLを修正:', newUrl);
          return newUrl;
        }
      } catch (e) {
        console.error('URLの解析に失敗:', url, e);
        return 'https://via.placeholder.com/50?text=User';
      }
    }
    
    return url;
  };

  // ユーザー名から頭文字を取得する関数
  const getUserInitial = (name: string | undefined | null): string => {
    if (!name || name.trim() === '') return '?';
    
    // 日本語などマルチバイト文字にも対応
    const firstChar = name.trim().charAt(0);
    return firstChar.toUpperCase();
  };

  // 画像のロード時のエラーハンドリング
  const handleImageError = (e: { target: HTMLImageElement }) => {
    console.error('イベント画像の読み込みに失敗しました:', eventData?.image_url);
    const target = e.target;
    target.onerror = null; // 無限ループを防ぐ
    target.src = 'https://via.placeholder.com/400x200?text=No+Image';
  };

  // ユーザー名から色を生成する関数
  const getUserColor = (name: string | undefined | null): string => {
    if (!name) return '#5c4033'; // デフォルト色
    
    // ユーザー名から簡単なハッシュを生成
    const hash = name.split('').reduce((acc, char) => {
      return char.charCodeAt(0) + ((acc << 5) - acc);
    }, 0);
    
    // ハッシュから暖色系の色を生成
    const h = Math.abs(hash) % 60; // 赤〜黄色の範囲 (0-60°)
    const s = 65 + (Math.abs(hash) % 20); // 彩度 65-85%
    const l = 45 + (Math.abs(hash) % 10); // 明度 45-55%
    
    return `hsl(${h}, ${s}%, ${l}%)`;
  };

  // プロフィール画像URLを処理する関数
  const processProfileImageUrl = (url: string | null): string => {
    if (!url) return 'https://via.placeholder.com/50x50?text=User';
    
    // MinIOのURLを修正（内部ネットワークのURLを外部アクセス可能なURLに変換）
    if (url.includes(':9000/')) {
      // MinIOのURLの場合、nginxプロキシ経由に変換
      const urlParts = url.split(':9000/');
      if (urlParts.length === 2) {
        const newUrl = `http://${window.location.hostname}/minio/${urlParts[1]}`;
        return newUrl;
      }
    }
    
    return url;
  };

  // コンポーネントレンダリング中にデバッグ情報を表示
  console.log('レンダリング時の状態:', { 
    eventData: eventData ? {
      id: eventData.id,
      title: eventData.title,
      current_persons: eventData.current_persons
    } : null, 
    membersLength: members.length,
    isLoading: loading,
    membersLoading: membersLoading
  })

  if (loading) {
    return (
      <div className={styles.pageBackground}>
        <div className={styles.eventDetailContainer}>
          <div style={{ padding: '20px', textAlign: 'center' }}>読み込み中...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={styles.pageBackground}>
        <div className={styles.eventDetailContainer}>
          <div style={{ padding: '20px' }}>
            <p style={{ color: '#d32f2f', marginBottom: '16px' }}>{error}</p>
            <button 
              onClick={handleBack} 
              style={{ 
                padding: '8px 16px', 
                backgroundColor: '#5c4033', 
                color: 'white', 
                border: 'none', 
                borderRadius: '4px',
                cursor: 'pointer'
              }}
            >
              イベント一覧に戻る
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (!eventData) {
    return (
      <div className={styles.pageBackground}>
        <div className={styles.eventDetailContainer}>
          <div style={{ padding: '20px' }}>
            <p style={{ marginBottom: '16px' }}>イベントが見つかりません</p>
            <button 
              onClick={handleBack} 
              style={{ 
                padding: '8px 16px', 
                backgroundColor: '#5c4033', 
                color: 'white', 
                border: 'none', 
                borderRadius: '4px',
                cursor: 'pointer'
              }}
            >
              イベント一覧に戻る
            </button>
          </div>
        </div>
      </div>
    );
  }

  // 定員に達しているかどうか
  const isFullCapacity = eventData.current_persons >= eventData.limit_persons;

  return (
    <div className={styles.pageBackground}>
      <div className={styles.eventDetailContainer}>
        <button onClick={handleBack} className={styles.backButton}>
          <span style={{ fontSize: '24px', fontWeight: 'bold' }}>←</span>
        </button>

        {/* イベント画像とタイトル */}
        <div style={{ position: 'relative' }}>
          {eventData.image_url ? (
            <img 
              src={processImageUrl(eventData.image_url)} 
              alt={getTitle()} 
              className={styles.eventImage}
              onError={handleImageError}
            />
          ) : (
            <div className={styles.noImage}>
              <span>No Image</span>
            </div>
          )}
          
          {/* タイトルオーバーレイ */}
          <div className={styles.titleOverlay}>
            <h1 className={styles.eventTitle}>{getTitle()}</h1>
          </div>
        </div>

        <div className={styles.contentContainer}>
          {/* タグ */}
          <div className={styles.tagContainer}>
            <span className={`${styles.tag} ${styles.statusTag}`}>
              {eventData.status === 'pending' ? '開催予定' : 
               eventData.status === 'started' ? '開催中' : '終了'}
            </span>
            {eventData.area && (
              <span className={`${styles.tag} ${styles.areaTag}`}>
                {eventData.area.name}
              </span>
            )}
            {/* タグ表示 */}
            {eventData.tags && eventData.tags.map((tag) => (
              <span key={tag.id} className={`${styles.tag} ${styles.categoryTag}`}>
                {tag.tag_name}
              </span>
            ))}
          </div>

          {/* イベント詳細 */}
          <div className={styles.section}>
            <h2 className={styles.sectionTitle}>イベント詳細</h2>
            <p className={styles.description}>{eventData.description}</p>
          </div>

          {/* イベント情報 */}
          <div className={styles.infoGrid}>
            <div className={styles.infoItem}>
              <span className={styles.infoLabel}>開催日時</span>
              <span className={styles.infoValue}>
                {eventData.timestamp ? new Date(eventData.timestamp).toLocaleDateString() : '未定'} 
              </span>
            </div>
            <div className={styles.infoItem}>
              <span className={styles.infoLabel}>開催場所</span>
              <span className={styles.infoValue}>{eventData.area?.name || '未定'}</span>
            </div>
            <div className={styles.infoItem}>
              <span className={styles.infoLabel}>参加人数</span>
              <span className={styles.infoValue}>{eventData.current_persons} / {eventData.limit_persons}人</span>
            </div>
            <div className={styles.infoItem}>
              <span className={styles.infoLabel}>ホスト</span>
              <span className={styles.infoValue}>{eventData.author?.user_name || '不明'}</span>
            </div>
          </div>

          {/* 参加者 */}
          <div className={styles.memberSection}>
            <h2 className={styles.sectionTitle}>参加者 ({eventData.current_persons}人)</h2>
            <div className={styles.memberList}>
              {eventData.current_persons > 0 ? (
                <>
                  {/* 実際のメンバーを表示（読み込み中かどうかに関わらず表示） */}
                  {members.map((member) => (
                    <div 
                      key={member.user_id || `member-${Math.random()}`} 
                      className={styles.memberAvatar}
                      onClick={() => navigate(`/user/${member.user_id}`)}
                      style={{ cursor: 'pointer' }}
                      title={`${member.user?.user_name || '参加者'}のプロフィールを表示`}
                    >
                      {member.user?.user_image_url && member.user.user_image_url !== 'null' && member.user.user_image_url !== 'undefined' && member.user.user_image_url !== '' ? (
                        <img 
                          src={processUserImageUrl(member.user.user_image_url)} 
                          alt={member.user?.user_name || '参加者'} 
                          className={styles.memberImage}
                          onError={(e: { target: HTMLImageElement }) => {
                            console.log('ユーザーアイコン読み込みエラー:', member.user?.user_image_url);
                            const target = e.target;
                            target.onerror = null;
                            
                            // エラー時は画像要素を削除してイニシャル表示に切り替え
                            const parent = target.parentElement;
                            if (parent) {
                              parent.innerHTML = '';
                              const initialDiv = document.createElement('div');
                              initialDiv.className = styles.memberInitial;
                              initialDiv.style.backgroundColor = getUserColor(member.user?.user_name);
                              initialDiv.textContent = getUserInitial(member.user?.user_name);
                              parent.appendChild(initialDiv);
                            }
                          }}
                        />
                      ) : (
                        <div className={styles.memberInitial} style={{ 
                          backgroundColor: getUserColor(member.user?.user_name)
                        }}>
                          {getUserInitial(member.user?.user_name)}
                        </div>
                      )}
                    </div>
                  ))}
                  
                  {/* 実際のメンバー数が参加人数より少ない場合はプレースホルダーを表示 */}
                  {membersLoading || members.length < eventData.current_persons ? (
                    <>
                      {membersLoading && <p>参加者情報を読み込み中...</p>}
                      {Array.from({ length: Math.max(0, eventData.current_persons - members.length) }).map((_, index) => (
                        <div key={`placeholder-${index}`} className={styles.memberAvatar}>
                          <div className={styles.memberInitial} style={{ 
                            backgroundColor: '#9ca3af'
                          }}>
                            ?
                          </div>
                        </div>
                      ))}
                    </>
                  ) : null}
                </>
              ) : (
                <p style={{ color: '#6b7280', fontStyle: 'italic' }}>参加者はまだいません</p>
              )}
            </div>
          </div>

          {/* アクションボタン */}
          <div className={styles.actionButtons}>
            {isJoined ? (
              <button 
                onClick={goToTalkRoom}
                className={styles.talkButton}
              >
                トークルームへ
              </button>
            ) : (
              <button 
                onClick={handleJoinEvent}
                disabled={joining || isFullCapacity}
                className={styles.joinButton}
              >
                {joining ? '参加中...' : isFullCapacity ? '定員に達しました' : 'イベントに参加'}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default EventDetailPage;