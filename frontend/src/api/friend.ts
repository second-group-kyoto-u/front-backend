import axios from '@/lib/axios';
import { getAuthHeader } from './auth';


export interface DmOverviewItem {
  partner_id: string;
  partner: {
    id: string;
    user_name: string;
    user_image_url: string | null;
    profile_message: string | null;
    is_certificated: boolean;
  };
  latest_message: {
    id: string;
    sender: {
      id: string;
      user_name: string;
      user_image_url: string | null;
    };
    receiver: {
      id: string;
      user_name: string;
      user_image_url: string | null;
    };
    content: string;
    sent_at: string;
    image_url: string | null;
    message_type: 'text' | 'image' | 'system' | 'bot';
    metadata: any;
    is_read: boolean;
    read_at: string | null;
  };
}

// ダイレクトメッセージの一覧（概要）を取得
export const getDirectMessageOverview = async (): Promise<DmOverviewItem[]> => {
  try {
    const response = await axios.get('/friend/dm-overview', {
      headers: getAuthHeader()
    });
    return response.data.overview;
  } catch (error) {
    throw error;
  }
};

export const getDirectMessages = async (friendId: string, limit = 50, offset = 0) => {
  const res = await axios.get(`/friend/direct-messages/${friendId}`, {
    params: { limit, offset },
    headers: getAuthHeader()
  });
  return res.data;
};


export const sendDirectMessage = async (receiverId: string, data: { content: string, message_type?: string }) => {
  await axios.post(`/friend/direct-message`, {
    receiver_id: receiverId,
    ...data
  }, {
    headers: getAuthHeader()
  });
};





