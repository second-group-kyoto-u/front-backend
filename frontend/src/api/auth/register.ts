import axios from '@/lib/axios'

export type RegisterRequest = {
  email: string
  password: string
  userName: string
}

export type RegisterResponse = {
  token: string
  message: string
  user: {
    id: string
    user_name: string
    email_address: string
    email_verified: boolean
    is_certificated: boolean
  }
}

export const registerUser = async (
  data: RegisterRequest
): Promise<RegisterResponse> => {
  try {
    const res = await axios.post<RegisterResponse>('auth/register', data)
    return res.data
  } catch (error: any) {
    if (error.response && error.response.data && error.response.data.error) {
      throw new Error(error.response.data.error)
    }
    throw new Error('ユーザー登録に失敗しました')
  }
}
