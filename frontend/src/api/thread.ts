import axios from '@/lib/axios'
import { getAuthHeader } from './auth';


// スレッド一覧を取得するAPI
export type ThreadListParams = {
  area_id?: string
  tags?: string[]
  page?: number
  per_page?: number
}

export type ThreadListResponse = {
  threads: Thread[]
  total: number
}

export type Thread = {
  id: string
  title: string
  created_at: string
  created_by: {
    id: string
    user_name: string
    profile_image_url: string
  }
  tags: {
    id: string
    name: string
  }[]
  hearts_count: number
  messages_count: number
  is_hearted: boolean
}

export const getThreads = async (
  params: ThreadListParams
): Promise<ThreadListResponse> => {
  const res = await axios.get<ThreadListResponse>('thread/threads', {
    params,
  })
  return res.data
}

// スレッド詳細を取得するAPI
export type ThreadDetailResponse = {
  thread: {
    id: string
    title: string
    created_at: string
    created_by: {
      id: string
      user_name: string
      profile_image_url: string
    }
    tags: {
      id: string
      name: string
    }[]
    hearts_count: number
    is_hearted: boolean
  }
  messages: {
    id: string
    content: string
    created_at: string
    created_by: {
      id: string
      user_name: string
      profile_image_url: string
    }
    message_type: 'text' | 'image'
  }[]
}

export const getThreadDetail = async (
  threadId: string
): Promise<ThreadDetailResponse> => {
  const res = await axios.get<ThreadDetailResponse>(`thread/${threadId}`)
  return res.data
}

// スレッドを作成するAPI
export type CreateThreadRequest = {
  title: string
  message: string
  image_id?: string
  area_id?: string
  tags?: string[]
}

export type CreateThreadResponse = {
  thread_id: string
  message: string
}

export const createThread = async (
  data: CreateThreadRequest
): Promise<CreateThreadResponse> => {
  const res = await axios.post<CreateThreadResponse>('thread', data, {
        headers: getAuthHeader()
      });
  return res.data
}

// スレッドを削除するAPI
export const deleteThread = async (
  threadId: string
): Promise<{ message: string }> => {
  const res = await axios.delete(`thread/${threadId}`)
  return res.data as { message: string }
}


// スレッドにメッセージを投稿するAPI
export type PostMessageRequest = {
  content: string
  message_type: 'text' | 'image'
}

export type PostMessageResponse = {
  message_id: string
}

export const postMessage = async (
  threadId: string,
  data: PostMessageRequest
): Promise<PostMessageResponse> => {
  const res = await axios.post<PostMessageResponse>(
    `thread/${threadId}/message`,
    data
  )
  return res.data
}

// スレッドにいいねするAPI
export const heartThread = async (
  threadId: string
): Promise<{ message: string }> => {
  const res = await axios.post<{ message: string }>(
    `thread/${threadId}/heart`,
    {}
  )
  return res.data
}

// スレッドのいいねを取り消すAPI
export const unheartThread = async (
  threadId: string
): Promise<{ message: string }> => {
  const res = await axios.post<{ message: string }>(
    `thread/${threadId}/unheart`,
    {}
  )
  return res.data
} 
