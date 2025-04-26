import axios from '@/lib/axios';
import { getAuthHeader } from './auth';

// イベント関連の型定義
export interface EventType {
  id: string;
  message: string;
  timestamp: string | null;
  published_at: string | null;
  current_persons: number;
  limit_persons: number;
  is_request: boolean;
  status: 'pending' | 'started' | 'ended'; // ER図に合わせてステータスを定義
  author: {
    id: string;
    user_name: string;
    user_image_url: string | null;
    profile_message: string | null;
    is_certificated: boolean;
  } | null;
  area: {
    id: string;
    name: string;
  } | null;
  image_url: string | null;
}

export interface EventMessageType {
  id: string;
  event_id: string;
  sender: {
    id: string;
    user_name: string;
    user_image_url: string | null;
    profile_message: string | null;
    is_certificated: boolean;
  } | null;
  content: string;
  timestamp: string | null;
  image_url: string | null;
  message_type: 'text' | 'image' | 'system';
  metadata: any;
  read_count: number;
}

export interface EventMemberType {
  user_id: string;
  event_id: string;
  joined_at: string; // ER図に合わせてjoined_atを追加
  user: {
    id: string;
    user_name: string;
    user_image_url: string | null;
    profile_message: string | null;
    is_certificated: boolean;
  };
}

// イベント取得（単一）
export const getEvent = async (eventId: string) => {
  try {
    const response = await axios.get(`event/${eventId}`, {
      headers: getAuthHeader()
    });
    return response.data;
  } catch (error) {
    throw error;
  }
};

// イベント一覧取得
export const getEvents = async (limit: number = 10, offset: number = 0) => {
  try {
    const response = await axios.get(`event/events`, {
      headers: getAuthHeader(),
      params: { limit, offset }
    });
    return response.data;
  } catch (error) {
    throw error;
  }
};

// イベント作成
export const createEvent = async (eventData: {
  message: string;
  image_id?: string;
  limit_persons?: number;
  area_id?: string;
  tags?: string[];
}) => {
  try {
    const response = await axios.post('event', eventData, {
      headers: getAuthHeader()
    });
    return response.data;
  } catch (error) {
    throw error;
  }
};

// イベント参加
export const joinEvent = async (eventId: string) => {
  try {
    const response = await axios.post(`event/${eventId}/join`, {}, {
      headers: getAuthHeader()
    });
    return response.data;
  } catch (error) {
    throw error;
  }
};

// イベント退出
export const leaveEvent = async (eventId: string) => {
  try {
    const response = await axios.post(`event/${eventId}/leave`, {}, {
      headers: getAuthHeader()
    });
    return response.data;
  } catch (error) {
    throw error;
  }
};

// イベント開始
export const startEvent = async (eventId: string, locationData?: any) => {
  try {
    const response = await axios.post(`event/${eventId}/start`, locationData || {}, {
      headers: getAuthHeader()
    });
    return response.data;
  } catch (error) {
    throw error;
  }
};

// イベント終了
export const endEvent = async (eventId: string) => {
  try {
    const response = await axios.post(`event/${eventId}/end`, {}, {
      headers: getAuthHeader()
    });
    return response.data;
  } catch (error) {
    throw error;
  }
};

// イベントメッセージ送信
export const sendEventMessage = async (eventId: string, messageData: {
  content?: string;
  image_id?: string;
  message_type?: 'text' | 'image';
  metadata?: any;
}) => {
  try {
    const response = await axios.post(`event/${eventId}/message`, messageData, {
      headers: getAuthHeader()
    });
    return response.data;
  } catch (error) {
    throw error;
  }
}; 