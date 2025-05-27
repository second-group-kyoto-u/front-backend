import axios from '@/lib/axios';
import { getAuthHeader } from './auth';


export interface Tag {
  id: string
  tag_name: string
}

export const getTags = async (): Promise<Tag[]> => {
  const response = await axios.get<{ tags: Tag[] }>('/tag/list')
  return response.data.tags
}
