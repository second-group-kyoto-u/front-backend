import React from 'react';
import { EventType } from '@/api/event';
import styles from '@/pages/Events/Events.module.css';

interface EventCardProps {
  event: EventType;
  onClick: () => void;
}

/**
 * イベントカードコンポーネント
 * イベントの基本情報を表示するカードUI
 */
const EventCard: React.FC<EventCardProps> = ({ event, onClick }) => {
  // イベントのタイトルを取得（title か message の適切な方を使用）
  const getTitle = () => {
    return event.title || event.message || '無題のイベント';
  };

  // 画像URLを処理する関数
  const processImageUrl = (url: string | null): string => {
    if (!url) return '/default-avatar.jpg';
    
    // MinIOのURLを修正
    if (url.includes('localhost:9000') || url.includes('127.0.0.1:9000') || url.includes('minio:9000')) {
      // URLがローカルのMinioを指している場合、nginxプロキシ経由のパスに修正
      const pathMatch = url.match(/\/([^\/]+)\/(.+)$/);
      if (pathMatch) {
        const bucket = pathMatch[1];
        const key = pathMatch[2];
        // nginxプロキシ経由でアクセス（/minio/パス）
        const baseUrl = window.location.origin;
        return `${baseUrl}/minio/${bucket}/${key}`;
      }
    }
    
    // 既にプロキシ経由のパスを使用している場合はそのまま返す
    if (url.includes('/minio/')) {
      return url;
    }
    
    return url;
  };

  // 画像のロード時のエラーハンドリング
  const handleImageError = (e: any) => {
    const target = e.target as HTMLImageElement;
    target.onerror = null; // 無限ループを防ぐ
    target.src = 'https://via.placeholder.com/400x200?text=No+Image';
  };

  // イベント情報をコンソールに出力（デバッグ用）
  console.log('イベントデータ:', {
    id: event.id,
    title: getTitle(),
    imageUrl: event.image_url,
    tags: event.tags,
    processedImageUrl: processImageUrl(event.image_url)
  });

  return (
    <div className={styles.eventCard} onClick={onClick}>
      <div className={styles.eventImageContainer}>
        <img 
          src={processImageUrl(event.image_url)} 
          alt={getTitle()} 
          className={styles.eventImage}
          onError={handleImageError}
        />
        <span className={`${styles.eventLabel} ${
          event.status === 'pending' 
            ? styles.pendingLabel
            : event.status === 'started'
              ? styles.startedLabel
              : styles.endedLabel
        }`}>
          {event.status === 'pending' ? '開催予定' : 
           event.status === 'started' ? '開催中' : '終了'}
        </span>
      </div>
      <div className={styles.eventContent}>
        <h3 className={styles.eventTitle}>{getTitle()}</h3>
        
        {/* タグの表示 */}
        {event.tags && event.tags.length > 0 && (
          <div className={styles.eventTags}>
            {event.tags.slice(0, 3).map((tag) => (
              <span key={tag.id} className={styles.eventTag}>
                {tag.tag_name}
              </span>
            ))}
            {event.tags.length > 3 && (
              <span className={styles.eventTagMore}>+{event.tags.length - 3}</span>
            )}
          </div>
        )}
        
        <div className={styles.eventInfo}>
          {event.area && (
            <span className={styles.eventArea}>{event.area.name}</span>
          )}
          <span className={styles.eventPersons}>
            {event.current_persons}/{event.limit_persons}人
          </span>
        </div>
      </div>
    </div>
  );
};

export default EventCard; 