import axios from '@/lib/axios';
import { getAuthHeader } from './auth';

export const getUserProfile = async (userId: string) => {
  const response = await axios.get(`/user/${userId}/profile`, {
    headers: getAuthHeader(),
  });
  return response.data;
};

export const followUser = async (userId: string) => {
  const response = await axios.post(
    `/user/${userId}/follow`,
    {},
    {
      headers: getAuthHeader(),
    }
  );
  return response.data;
};

export const unfollowUser = async (userId: string) => {
  const response = await axios.post(
    `/user/${userId}/unfollow`,
    {},
    {
      headers: getAuthHeader(),
    }
  );
  return response.data;
};


