// 認証済みページの取得
import axios from '@/lib/axios'

export type UserData = {
  id: string;
  user_name: string;
  profile_message: string;
  profile_image_url: string;
}

export type ProtectedResponse = {
  user: UserData;
  joined_events_count: number;
  favorite_tags: string[];
  message: string;
}

export const fetchProtected = async (): Promise<ProtectedResponse> => {
  console.log("📡 fetchProtected(): APIリクエスト開始")
  const res = await axios.get<ProtectedResponse>('protected/mypage')
  return res.data
}
