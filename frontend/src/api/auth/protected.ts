// 認証済みページの取得
import axios from '@/lib/axios'
import { getAuthHeader } from '../auth';

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

export interface UpdateProfilePayload {
  user_name: string;
  profile_message: string;
  birthdate: string;
  location: string;
  gender: string;
  // profile_image_url
}

export const fetchProtected = async (): Promise<ProtectedResponse> => {
  console.log("📡 fetchProtected(): APIリクエスト開始")
  const res = await axios.get<ProtectedResponse>('protected/mypage')
  return res.data
}

export const updateProfile = async (data: UpdateProfilePayload) => {
  const safeBirthdate = (() => {
    const d = new Date(data.birthdate)
    return isNaN(d.getTime()) ? '' : d.toISOString().slice(0, 10)
  })()

  const safeData = {
    ...data,
    birthdate: safeBirthdate,
  }

  const res = await axios.put('protected/update-profile', safeData, {
    headers: getAuthHeader()
  })
  return res.data
}

