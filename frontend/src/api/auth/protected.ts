// 認証済みページの取得
import axios from '@/lib/axios'

export type ProtectedResponse = {
  message: string
  profile_image_url?: string
}


export const fetchProtected = async (token: string): Promise<ProtectedResponse> => {
  const res = await axios.get<ProtectedResponse>('/mypage', {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })
  return res.data
}
