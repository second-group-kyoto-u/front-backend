import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { EventType, getEvents } from '@/api/event';
import EventCard from './EventCard';

interface EventListProps {
  limit?: number;
  filter?: {
    area_id?: string;
    status?: 'pending' | 'started' | 'ended';
  };
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
        const options = {
          per_page: limit,
          ...filter
        };
        const response = await getEvents(options);
        
        if (response && response.events) {
          setEvents(response.events);
        }
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
    <>
      {events.map((event) => (
        <div key={event.id}>
          <EventCard 
            event={event} 
            onClick={() => handleEventClick(event.id)} 
          />
        </div>
      ))}
    </>
  );
};

export default EventList; 