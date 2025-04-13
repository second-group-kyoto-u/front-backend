// ログインPOST処理
import axios from '@/lib/axios'

export type LoginRequest = {
  email: string
  password: string
}

export type LoginResponse = {
  token: string
}

const LOGIN_ENDPOINT = '/login'

export const loginUser = async (
  data: LoginRequest
): Promise<LoginResponse> => {
  try {
    const res = await axios.post<LoginResponse>(LOGIN_ENDPOINT, data)
    return res.data
  } catch (error) {
    // axios error型をここで扱う場合もあり
    throw new Error('ログインに失敗しました')
  }
}
