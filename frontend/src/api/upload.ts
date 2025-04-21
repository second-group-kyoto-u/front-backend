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
  file: File
): Promise<ImageUploadResponse> => {
  const formData = new FormData()
  formData.append('file', file)

  const res = await axios.post<ImageUploadResponse>('upload/image', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
  return res.data
} 