import axios from '@/lib/axios'

// 画像アップロードAPI
export type ImageUploadResponse = {
  message: string
  image: {
    id: string
    url: string
  }
}

export const uploadImage = async (
  file: File,
  token?: string
): Promise<ImageUploadResponse> => {
  const formData = new FormData()
  formData.append('file', file)

  const headers: Record<string, string> = {
    'Content-Type': 'multipart/form-data',
  }

  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  const res = await axios.post<ImageUploadResponse>('upload/image', formData, {
    headers
  })
  return res.data
}

// イベント用画像アップロードAPI
export type EventImageUploadResponse = {
  image_id: string;
};

export const uploadEventImage = async (
  file: File,
  token?: string
): Promise<EventImageUploadResponse> => {
  const formData = new FormData()
  formData.append('file', file)

  const headers: Record<string, string> = {
    'Content-Type': 'multipart/form-data',
  }

  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  const res = await axios.post<EventImageUploadResponse>('upload/event-image', formData, {
    headers
  })
  return res.data
}

// 年齢認証用画像アップロードAPI
export type AgeVerificationUploadResponse = {
  message: string;
  user?: {
    id: string;
    user_name: string;
    is_age_verified: boolean;
  };
};

export const uploadAgeVerificationImage = async (
  file: File,
  token: string
): Promise<AgeVerificationUploadResponse> => {
  const formData = new FormData()
  formData.append('file', file)

  const headers: Record<string, string> = {
    'Content-Type': 'multipart/form-data',
    'Authorization': `Bearer ${token}`
  }

  const res = await axios.post<AgeVerificationUploadResponse>('upload/age-verification', formData, {
    headers
  })
  return res.data
}
