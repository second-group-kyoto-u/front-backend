import React from 'react';
import { EventType } from '../../api/event';

interface EventCardProps {
  event: EventType;
  onClick?: () => void;
}

/**
 * イベントカードコンポーネント
 * イベントの基本情報を表示するカードUI
 */
const EventCard: React.FC<EventCardProps> = ({ event, onClick }) => {
  // イベントのステータスに応じたラベルとスタイル
  const getStatusLabel = () => {
    switch(event.status) {
      case 'pending':
        return <span className="bg-yellow-100 text-yellow-800 px-2 py-1 rounded text-xs">開催予定</span>;
      case 'started':
        return <span className="bg-green-100 text-green-800 px-2 py-1 rounded text-xs">開催中</span>;
      case 'ended':
        return <span className="bg-gray-100 text-gray-800 px-2 py-1 rounded text-xs">終了</span>;
      default:
        return null;
    }
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return '';
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('ja-JP', { 
      year: 'numeric', 
      month: 'short', 
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    }).format(date);
  };

  return (
    <div 
      className="border rounded-lg overflow-hidden shadow-sm hover:shadow-md transition-shadow duration-200 cursor-pointer bg-white"
      onClick={onClick}
    >
      {event.image_url && (
        <div className="h-40 overflow-hidden">
          <img 
            src={event.image_url} 
            alt={event.message} 
            className="w-full h-full object-cover"
          />
        </div>
      )}
      <div className="p-4">
        <div className="flex justify-between items-start mb-2">
          <h3 className="font-medium text-lg line-clamp-2">{event.message}</h3>
          {getStatusLabel()}
        </div>
        
        <div className="text-sm text-gray-600 mb-3">
          {formatDate(event.published_at)}
        </div>
        
        <div className="flex justify-between items-center">
          <div className="flex items-center">
            {event.author?.user_image_url ? (
              <img 
                src={event.author.user_image_url} 
                alt={event.author.user_name}
                className="w-6 h-6 rounded-full mr-2"
              />
            ) : (
              <div className="w-6 h-6 rounded-full bg-gray-200 mr-2"></div>
            )}
            <span className="text-sm">{event.author?.user_name}</span>
          </div>
          
          <div className="text-sm">
            <span className="font-medium">{event.current_persons}</span>
            <span className="text-gray-500">/{event.limit_persons}人</span>
          </div>
        </div>
        
        {event.area && (
          <div className="mt-2 text-xs text-gray-500">
            <span>エリア: {event.area.name}</span>
          </div>
        )}
      </div>
    </div>
  );
};

export default EventCard; 