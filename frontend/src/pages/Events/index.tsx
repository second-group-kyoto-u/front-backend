import React, { useState } from 'react';
import EventList from '../../components/Event/EventList';
import styles from './Events.module.css';

const EventsPage: React.FC = () => {
  const [filter, setFilter] = useState<{
    area_id?: string;
    status?: 'pending' | 'started' | 'ended';
  }>({});

  return (
    <div className={styles.eventsContainer}>
      <h1 className={styles.pageTitle}>イベント一覧</h1>
      
      <div className={styles.filtersContainer}>
        <select 
          className={styles.filterSelect}
          value={filter.status || ''}
          onChange={(e) => setFilter(prev => ({
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

      <EventList limit={20} filter={filter} />
    </div>
  );
};

export default EventsPage; 