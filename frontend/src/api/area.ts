import axios from '@/lib/axios';
import { getAuthHeader } from './auth';


// api/area.ts
export type Area = {
  id: string;
  name: string;
}

export const getAreas = async (): Promise<Area[]> => {
  const res = await axios.get<{ areas: Area[] }>('/area/list')
  return res.data.areas
}
