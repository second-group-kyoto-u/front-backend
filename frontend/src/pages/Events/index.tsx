import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { getEvents, getRecommendedEvents, getFriendsEvents, EventType } from '@/api/event';
import EventCard from '@/components/Event/EventCard';
import { useAuth } from '@/hooks/useAuth';
import styles from './Events.module.css';

const EventsPage: React.FC = () => {
  const [recommendedEvents, setRecommendedEvents] = useState<EventType[]>([]);
  const [friendsEvents, setFriendsEvents] = useState<EventType[]>([]);
  const [allEvents, setAllEvents] = useState<EventType[]>([]);
  const [filteredEvents, setFilteredEvents] = useState<EventType[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchKeyword, setSearchKeyword] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'pending' | 'started' | 'ended'>('all');
  const { isAuthenticated, redirectToLogin } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  // フィルタリング関数
  const filterEvents = (events: EventType[], keyword: string, status: string) => {
    let filtered = events;

    // キーワードフィルタリング
    if (keyword.trim()) {
      const lowerKeyword = keyword.toLowerCase().trim();
      filtered = filtered.filter(event => 
        event.title?.toLowerCase().includes(lowerKeyword) ||
        event.description?.toLowerCase().includes(lowerKeyword) ||
        event.area?.name?.toLowerCase().includes(lowerKeyword) ||
        event.tags?.some(tag => tag.tag_name?.toLowerCase().includes(lowerKeyword))
      );
    }

    // ステータスフィルタリング
    if (status !== 'all') {
      filtered = filtered.filter(event => event.status === status);
    }

    return filtered;
  };

  // フィルタが変更された時に実行
  useEffect(() => {
    const filtered = filterEvents(allEvents, searchKeyword, statusFilter);
    setFilteredEvents(filtered);
  }, [allEvents, searchKeyword, statusFilter]);

  useEffect(() => {
    const fetchEvents = async () => {
      try {
        setLoading(true);
        setError(null);
        
        console.log('イベント取得開始...');
        
        // 並行してすべてのAPIを呼び出し
        const promises = [];
        
        // おすすめイベントを取得
        if (isAuthenticated) {
          // ログイン済みユーザーには推薦アルゴリズムを使用
          promises.push(
            getRecommendedEvents(4)
              .then(response => {
                console.log('推薦イベント取得成功:', response);
                if (response && response.events) {
                  setRecommendedEvents(response.events);
                } else {
                  console.warn('推薦イベントのレスポンスが期待と異なります:', response);
                  setRecommendedEvents([]);
                }
              })
              .catch(err => {
                console.error('推薦イベント取得エラー:', err);
                // 推薦失敗時は人気イベント（最新4件）を取得
                return getEvents({ per_page: 4 })
                  .then(response => {
                    console.log('フォールバック: 人気イベント取得成功:', response);
                    if (response && response.events) {
                      setRecommendedEvents(response.events);
                    } else if (response && Array.isArray(response)) {
                      setRecommendedEvents(response);
                    } else {
                      setRecommendedEvents([]);
                    }
                  })
                  .catch(fallbackErr => {
                    console.error('フォールバックイベント取得エラー:', fallbackErr);
                    setRecommendedEvents([]);
                  });
              })
          );
        } else {
          // 未ログインユーザーには人気イベント（最新4件）を表示
          promises.push(
            getEvents({ per_page: 4 })
              .then(response => {
                console.log('人気イベント取得成功:', response);
                if (response && response.events) {
                  setRecommendedEvents(response.events);
                } else if (response && Array.isArray(response)) {
                  setRecommendedEvents(response);
                } else {
                  console.warn('人気イベントのレスポンスが期待と異なります:', response);
                  setRecommendedEvents([]);
                }
              })
              .catch(err => {
                console.error('人気イベント取得エラー:', err);
                setRecommendedEvents([]);
              })
          );
        }

        // ログイン済みの場合、フレンドのイベントも取得
        if (isAuthenticated) {
          promises.push(
            getFriendsEvents(4)
              .then(response => {
                console.log('フレンドイベント取得成功:', response);
                if (response && response.events) {
                  setFriendsEvents(response.events);
                } else {
                  setFriendsEvents([]);
                }
              })
              .catch(err => {
                console.error('フレンドのイベント取得エラー:', err);
                setFriendsEvents([]);
                // 認証エラーでも続行
              })
          );
        } else {
          setFriendsEvents([]);
        }
        
        // 全てのイベントを取得
        promises.push(
          getEvents({ per_page: 50 })
            .then(response => {
              console.log('全イベント取得成功:', response);
              if (response && response.events) {
                setAllEvents(response.events);
                console.log('設定された全イベント数:', response.events.length);
              } else if (response && Array.isArray(response)) {
                // レスポンスが直接配列の場合
                setAllEvents(response);
                console.log('設定された全イベント数（配列形式）:', response.length);
              } else {
                console.warn('全イベントのレスポンスが期待と異なります:', response);
                setAllEvents([]);
              }
            })
            .catch(err => {
              console.error('全イベント取得エラー:', err);
              setAllEvents([]);
              
              // 認証エラーかどうかチェック
              if (err.response && (err.response.status === 401 || err.response.status === 404)) {
                console.warn('認証エラーのため、ログイン画面にリダイレクトします');
                if (redirectToLogin) {
                  redirectToLogin();
                }
                return;
              }
              
              throw err; // 他のエラーは上位に伝播
            })
        );

        // すべてのPromiseを待機
        await Promise.all(promises);
        
      } catch (err: any) {
        console.error('イベント取得エラー:', err);
        setError('イベントの取得に失敗しました');
      } finally {
        setLoading(false);
      }
    };

    fetchEvents();
  }, [isAuthenticated, redirectToLogin]);

  const handleEventClick = (eventId: string) => {
    navigate(`/event/${eventId}`);
  };

  const handleCreateButtonClick = () => {
    console.log('イベント作成ボタンがクリックされました');
    navigate('/event/create');
  };

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchKeyword(e.target.value);
  };

  const handleStatusFilterChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setStatusFilter(e.target.value as 'all' | 'pending' | 'started' | 'ended');
  };

  return (
    <div className={styles.pageBackground}>
      <div className={styles.eventsContainer}>
        {/* 検索バー */}
        <div className={styles.searchBar}>
          <input
            type="text"
            placeholder="キーワードで検索"
            className={styles.searchInput}
            value={searchKeyword}
            onChange={handleSearchChange}
          />
        </div>
        
        {/* フィルター */}
        <div className={styles.filtersContainer}>
          <select 
            className={styles.filterSelect}
            value={statusFilter}
            onChange={handleStatusFilterChange}
          >
            <option value="all">すべてのステータス</option>
            <option value="pending">開催予定</option>
            <option value="started">開催中</option>
            <option value="ended">終了</option>
          </select>
        </div>

        {/* フィルタリング結果セクション（フィルターが適用されている場合のみ表示） */}
        {(searchKeyword.trim() || statusFilter !== 'all') && (
          <section className={styles.eventSection}>
            <div className={styles.sectionHeader}>
              <h2 className={styles.sectionTitle}>
                検索結果
                {searchKeyword && ` - 「${searchKeyword}」`}
                {statusFilter !== 'all' && ` - ${
                  statusFilter === 'pending' ? '開催予定' :
                  statusFilter === 'started' ? '開催中' : '終了'
                }のイベント`}
                <span style={{ marginLeft: '10px', fontSize: '0.8em', color: '#666' }}>
                  ({filteredEvents.length}件)
                </span>
              </h2>
            </div>
            
            {loading ? (
              <div className={styles.loadingContainer}>読み込み中...</div>
            ) : error ? (
              <div className={styles.errorContainer}>{error}</div>
            ) : filteredEvents.length === 0 ? (
              <div className={styles.emptyContainer}>
                検索条件に一致するイベントがありません
              </div>
            ) : (
              <div className={styles.cardGrid}>
                {filteredEvents.map((event) => (
                  <div key={event.id} className={styles.eventCardWrapper}>
                    <EventCard 
                      event={event} 
                      onClick={() => handleEventClick(event.id)} 
                    />
                  </div>
                ))}
              </div>
            )}
          </section>
        )}

        {/* おすすめイベントセクション（フィルターが適用されていない場合のみ表示） */}
        {!searchKeyword.trim() && statusFilter === 'all' && (
          <section className={styles.eventSection}>
            <div className={styles.sectionHeader}>
              <h2 className={styles.sectionTitle}>
                {isAuthenticated ? 'あなたにおすすめのイベント' : '人気のイベント'}
              </h2>
            </div>

            {loading ? (
              <div className={styles.loadingContainer}>読み込み中...</div>
            ) : error ? (
              <div className={styles.errorContainer}>{error}</div>
            ) : recommendedEvents.length === 0 ? (
              <div className={styles.emptyContainer}>
                {isAuthenticated ? 'おすすめのイベントがありません' : '人気のイベントがありません'}
              </div>
            ) : (
              <div className={styles.cardGrid}>
                {recommendedEvents.map((event) => (
                  <div key={event.id} className={styles.eventCardWrapper}>
                    <EventCard 
                      event={event} 
                      onClick={() => handleEventClick(event.id)} 
                    />
                  </div>
                ))}
              </div>
            )}
          </section>
        )}

        {/* フレンドが主催するイベントセクション（フィルターが適用されていない場合のみ表示） */}
        {!searchKeyword.trim() && statusFilter === 'all' && isAuthenticated && friendsEvents.length > 0 && (
          <section className={styles.eventSection}>
            <div className={styles.sectionHeader}>
              <h2 className={styles.sectionTitle}>フォロー中のユーザーが主催するイベント</h2>
            </div>

            <div className={styles.cardGrid}>
              {friendsEvents.map((event) => (
                <div key={event.id} className={styles.eventCardWrapper}>
                  <EventCard 
                    event={event} 
                    onClick={() => handleEventClick(event.id)} 
                  />
                </div>
              ))}
            </div>
          </section>
        )}

        {/* すべてのイベント（フィルターが適用されていない場合のみ表示） */}
        {!searchKeyword.trim() && statusFilter === 'all' && (
          <section className={styles.eventSection}>
            <div className={styles.sectionHeader}>
              <h2 className={styles.sectionTitle}>すべてのイベント</h2>
            </div>
            
            {loading ? (
              <div className={styles.loadingContainer}>読み込み中...</div>
            ) : error ? (
              <div className={styles.errorContainer}>{error}</div>
            ) : allEvents.length === 0 ? (
              <div className={styles.emptyContainer}>イベントがありません</div>
            ) : (
              <div className={styles.cardGrid}>
                {allEvents.map((event) => (
                  <div key={event.id} className={styles.eventCardWrapper}>
                    <EventCard 
                      event={event} 
                      onClick={() => handleEventClick(event.id)} 
                    />
                  </div>
                ))}
              </div>
            )}
          </section>
        )}
      </div>

      {/* イベント作成ボタン */}
      <button 
        className={styles.createButton}
        onClick={handleCreateButtonClick}
        aria-label="イベントを作成"
      >
        +
      </button>
    </div>
  );
};

export default EventsPage; 