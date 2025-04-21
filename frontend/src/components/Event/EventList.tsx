import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { EventType, getEvents } from '../../api/event';
import EventCard from './EventCard';

interface EventListProps {
  limit?: number;
  filter?: {
    area_id?: string;
    status?: 'pending' | 'started' | 'ended';
  };
}

// APIレスポンスの型を定義
interface EventsResponse {
  events: EventType[];
  total: number;
}

/**
 * イベント一覧表示コンポーネント
 */
const EventList: React.FC<EventListProps> = ({ limit = 10, filter }) => {
  const [events, setEvents] = useState<EventType[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchEvents = async () => {
      try {
        setLoading(true);
        const response = await getEvents(limit, 0) as EventsResponse;
        
        // フィルタリング（フロントエンドでの実装）
        let filteredEvents = response.events;
        
        if (filter) {
          if (filter.area_id) {
            filteredEvents = filteredEvents.filter(
              (event: EventType) => event.area?.id === filter.area_id
            );
          }
          
          if (filter.status) {
            filteredEvents = filteredEvents.filter(
              (event: EventType) => event.status === filter.status
            );
          }
        }
        
        setEvents(filteredEvents);
      } catch (err) {
        setError('イベントの取得に失敗しました');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchEvents();
  }, [limit, filter]);

  const handleEventClick = (eventId: string) => {
    navigate(`/event/${eventId}`);
  };

  if (loading) {
    return <div className="p-4 text-center">読み込み中...</div>;
  }

  if (error) {
    return <div className="p-4 text-center text-red-500">{error}</div>;
  }

  if (events.length === 0) {
    return <div className="p-4 text-center">イベントがありません</div>;
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {events.map((event) => (
        <EventCard 
          key={event.id} 
          event={event} 
          onClick={() => handleEventClick(event.id)} 
        />
      ))}
    </div>
  );
};

export default EventList; 