import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getFriends } from '@/api/friend'; // フレンド一覧取得APIがあると仮定

interface Friend {
  id: string;
  user_name: string;
  user_image_url: string | null;
}

const CreateNewDMPage = () => {
  const [friends, setFriends] = useState<Friend[]>([]);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchFriends = async () => {
      try {
        const res = await getFriends(); // /friend/friends のデータ想定
        setFriends(res.friends.map((f: any) => f.user));
      } catch (e) {
        console.error(e);
      }
    };
    fetchFriends();
  }, []);

  const startDm = (friendId: string) => {
    navigate(`/friend/${friendId}/dm`);
  };

  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold mb-4">新しいDMを開始</h1>
      {friends.length === 0 ? (
        <p>フレンドがいません。</p>
      ) : (
        <ul className="chat-list">
          {friends.map((friend) => (
            <li
              key={friend.id}
              className="chat-item"
              onClick={() => startDm(friend.id)}
            >
              <div className="chat-item-content">
                {friend.user_image_url ? (
                  <img src={friend.user_image_url} alt={`${friend.user_name}のプロフィール画像`} className="chat-avatar" />
                ) : (
                  <div className="chat-avatar-placeholder" />
                )}
                <div className="chat-content">
                  <h2 className="text-lg font-semibold">{friend.user_name}</h2>
                </div>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default CreateNewDMPage;
