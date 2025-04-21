import axios from '@/lib/axios'

// パスワードリセット申請
export type ForgotPasswordRequest = {
  email: string
}

export type ForgotPasswordResponse = {
  message: string
}

export const forgotPassword = async (
  data: ForgotPasswordRequest
): Promise<ForgotPasswordResponse> => {
  try {
    const res = await axios.post<ForgotPasswordResponse>('auth/forgot-password', data)
    return res.data
  } catch (error) {
    throw new Error('パスワードリセット申請に失敗しました')
  }
}

// パスワードリセット実行
export type ResetPasswordRequest = {
  password: string
}

export type ResetPasswordResponse = {
  message: string
}

export const resetPassword = async (
  token: string, 
  data: ResetPasswordRequest
): Promise<ResetPasswordResponse> => {
  try {
    const res = await axios.post<ResetPasswordResponse>(`auth/reset-password/${token}`, data)
    return res.data
  } catch (error) {
    throw new Error('パスワードリセットに失敗しました')
  }
}

// メール認証再送
export type ResendVerificationRequest = {
  email: string
}

export type ResendVerificationResponse = {
  message: string
}

export const resendVerification = async (
  data: ResendVerificationRequest
): Promise<ResendVerificationResponse> => {
  try {
    const res = await axios.post<ResendVerificationResponse>('auth/resend-verification', data)
    return res.data
  } catch (error) {
    throw new Error('認証メール再送に失敗しました')
  }
} 