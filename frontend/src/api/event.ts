import axios from '@/lib/axios';
import { getAuthHeader } from './auth';

// イベント関連の型定義
export interface EventType {
  id: string;
  title: string;
  description: string;
  message?: string; // 後方互換性のため残す
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
  tags?: Array<{
    id: string;
    tag_name: string;
  }>;
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
  message_type: 'text' | 'image' | 'system' | 'bot' | 'bot_nyanta' | 'bot_hitsuji' | 'bot_koko' | 'bot_fukurou' | 'bot_toraberu' | string;
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

// イベント一覧取得
export const getEvents = async (options?: {
  area_id?: string;
  tag?: string;
  page?: number;
  per_page?: number;
  status?: 'pending' | 'started' | 'ended';
}) => {
  try {
    // クエリパラメータの構築
    let params = {};
    if (options) {
      params = { ...options };
    }

    const response = await axios.get('event/events', { params });
    return response.data;
  } catch (error) {
    throw error;
  }
};

// イベント詳細取得
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
export const startEvent = async (eventId: string, data?: { location?: any }) => {
  try {
    const response = await axios.post(`event/${eventId}/start`, data || {}, {
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
export const sendEventMessage = async (eventId: string, data: {
  content?: string;
  image_id?: string;
  message_type: 'text' | 'image' | 'location' | 'system' | 'bot' | 'bot_nyanta' | 'bot_hitsuji' | 'bot_koko' | 'bot_fukurou' | 'bot_toraberu' | string;
  metadata?: any;
}) => {
  try {
    const response = await axios.post(`event/${eventId}/message`, data, {
      headers: getAuthHeader()
    });
    return response.data;
  } catch (error) {
    throw error;
  }
};

// イベントメンバー取得
export const getEventMembers = async (eventId: string) => {
  try {
    // 認証トークンがあればヘッダーに含める（なくても動作する）
    const authHeader = getAuthHeader();
    const hasAuth = Object.keys(authHeader).length > 0;
    
    console.log('メンバー情報取得API呼び出し', {
      url: `event/${eventId}/members`,
      hasAuth: hasAuth
    });
    
    const response = await axios.get(`event/${eventId}/members`, {
      headers: hasAuth ? authHeader : {},
      withCredentials: false // CORS関連の問題を避けるため
    });
    
    console.log('メンバー情報取得API レスポンス:', response.data);
    return response.data;
  } catch (error) {
    console.error('メンバー情報取得API エラー:', error);
    throw error;
  }
};

// おすすめイベント取得（ユーザーのタグに基づく）
export const getRecommendedEvents = async (limit: number = 10) => {
  try {
    const response = await axios.get('event/recommended', {
      params: { limit },
      headers: getAuthHeader()
    });
    return response.data;
  } catch (error) {
    throw error;
  }
};

// フレンドが主催するイベント取得
export const getFriendsEvents = async (limit: number = 10) => {
  try {
    const response = await axios.get('event/friends', {
      params: { limit },
      headers: getAuthHeader()
    });
    return response.data;
  } catch (error) {
    throw error;
  }
};

// イベント作成
export const createEvent = async (data: {
  title: string;
  description: string;
  area_id: string;
  limit_persons: number;
  tags: string[];
  event_location?: string;
  image_id?: string;
}) => {
  try {
    const response = await axios.post('event/', data, {
      headers: getAuthHeader()
    });
    return response.data;
  } catch (error) {
    throw error;
  }
};

// 自分が参加しているイベント一覧を取得
export const getJoinedEvents = async () => {
  try {
    const response = await axios.get('event/joined-events', {
      headers: getAuthHeader()
    });
    return response.data;
  } catch (error) {
    throw error;
  }
};

// アドバイザー応答生成API
export const getAdvisorResponse = async (eventId: string, data: {
  message: string;
  character_id?: string;
  location?: {
    latitude: number;
    longitude: number;
  };
}): Promise<{
  response: string;
  message: string;
  message_id: string;
  debug_info?: {
    ai_analysis: {
      needs_weather: boolean;
      needs_location: boolean;
      weather_analysis?: any;
      location_analysis?: any;
      overall_reasoning?: string;
    };
    weather_used: boolean;
    location_used: boolean;
    weather_data?: any;
    location_count: number;
  };
}> => {
  try {
    const response = await axios.post(`event/${eventId}/advisor-response`, data, {
      headers: getAuthHeader()
    });
    return response.data;
  } catch (error) {
    throw error;
  }
};

// キャラクターリスト取得
export const getCharacters = async () => {
  try {
    console.log('キャラクターリスト取得API呼び出し');
    const response = await axios.get('character/characters', {
      headers: getAuthHeader()
    });
    console.log('キャラクターリスト取得API レスポンス:', response.data);
    return response.data;
  } catch (error) {
    console.error('キャラクターリスト取得API エラー:', error);
    throw error;
  }
};

// キャラクター詳細情報取得
export const getCharacter = async (characterId: string) => {
  try {
    console.log(`キャラクター詳細取得API呼び出し: ${characterId}`);
    const response = await axios.get(`character/characters/${characterId}`, {
      headers: getAuthHeader()
    });
    console.log('キャラクター詳細取得API レスポンス:', response.data);
    return response.data;
  } catch (error) {
    console.error('キャラクター詳細取得API エラー:', error);
    throw error;
  }
};

// イベントの天気情報とアドバイスを取得
export const getEventWeatherInfo = async (eventId: string, data?: {
  location?: {
    latitude: number;
    longitude: number;
  };
}) => {
  try {
    console.log(`イベント天気情報取得API呼び出し: ${eventId}`);
    const response = await axios.post(`event/${eventId}/weather-info`, data || {}, {
      headers: getAuthHeader()
    });
    console.log('イベント天気情報取得API レスポンス:', response.data);
    return response.data;
  } catch (error) {
    console.error('イベント天気情報取得API エラー:', error);
    throw error;
  }
}; 