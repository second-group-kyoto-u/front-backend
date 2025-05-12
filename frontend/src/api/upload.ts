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