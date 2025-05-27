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
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  
  const [filter, setFilter] = useState<{
    area_id?: string;
    status?: 'pending' | 'started' | 'ended';
  }>({});

  useEffect(() => {
    const fetchEvents = async () => {
      try {
        setLoading(true);
        
        // おすすめイベントを取得
        const recommendedResponse = await getRecommendedEvents(4);
        if (recommendedResponse && recommendedResponse.events) {
          setRecommendedEvents(recommendedResponse.events);
        }

        // ログイン済みの場合、フレンドのイベントも取得
        if (isAuthenticated) {
          try {
            const friendsResponse = await getFriendsEvents(4);
            if (friendsResponse && friendsResponse.events) {
              setFriendsEvents(friendsResponse.events);
            }
          } catch (err) {
            console.error('フレンドのイベント取得エラー:', err);
          }
        }
        
        // 全てのイベントを取得（フィルター適用）
        const options = {
          per_page: 20,
          ...filter
        };
        const response = await getEvents(options);
        if (response && response.events) {
          setAllEvents(response.events);
        }
      } catch (err) {
        setError('イベントの取得に失敗しました');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchEvents();
  }, [isAuthenticated, filter]);

  const handleEventClick = (eventId: string) => {
    navigate(`/event/${eventId}`);
  };

  const handleCreateButtonClick = () => {
    // 認証確認なしでイベント作成ページへ直接遷移
    console.log('イベント作成ボタンがクリックされました');
    navigate('/event/create');
  };

  return (
    <div className={styles.pageBackground}>
      <div className={styles.eventsContainer}>
        <div className={styles.searchBar}>
          <input
            type="text"
            placeholder="キーワードで検索"
            className={styles.searchInput}
          />
        </div>
        
        {/* フィルター */}
        <div className={styles.filtersContainer}>
          <select 
            className={styles.filterSelect}
            value={filter.status || ''}
            onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setFilter((prev: typeof filter) => ({
              ...prev,
              status: e.target.value as 'pending' | 'started' | 'ended' | undefined
            }))}
          >
            <option value="">すべてのステータス</option>
            <option value="pending">開催予定</option>
            <option value="started">開催中</option>
            <option value="ended">終了</option>
          </select>
        </div>

        {/* おすすめイベントセクション */}
        <section className={styles.eventSection}>
          <div className={styles.sectionHeader}>
            <h2 className={styles.sectionTitle}>おすすめのイベント</h2>
          </div>

          {loading ? (
            <div className={styles.loadingContainer}>読み込み中...</div>
          ) : error ? (
            <div className={styles.errorContainer}>{error}</div>
          ) : recommendedEvents.length === 0 ? (
            <div className={styles.emptyContainer}>イベントがありません</div>
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

        {/* フレンドが主催するイベントセクション */}
        {isAuthenticated && friendsEvents.length > 0 && (
          <section className={styles.eventSection}>
            <div className={styles.sectionHeader}>
              <h2 className={styles.sectionTitle}>フォロー中のユーザーが主催するイベント</h2>
            </div>

            {loading ? (
              <div className={styles.loadingContainer}>読み込み中...</div>
            ) : (
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
            )}
          </section>
        )}
        
        {/* すべてのイベント */}
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