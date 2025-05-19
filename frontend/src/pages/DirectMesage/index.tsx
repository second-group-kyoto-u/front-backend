import { useEffect, useState, useRef } from 'react';
import { useParams } from 'react-router-dom';
import { getDirectMessages, sendDirectMessage } from '@/api/friend';
import { getUserProfile } from '@/api/user'; // 相手の名前画像取得


interface Message {
  id: string;
  content: string;
  sent_at: string;
  message_type: 'text' | 'image';
  sender_id: string;
}

interface User {
  id: string;
  user_name: string;
  user_image_url: string | null;
}

const DirectMessagePage = () => {
  const { userId } = useParams();
  const [messages, setMessages] = useState<Message[]>([]);
  const [partner, setPartner] = useState<User | null>(null);
  const [input, setInput] = useState('');
  const bottomRef = useRef<HTMLDivElement>(null);

  const token = localStorage.getItem('token');
  const payload = token ? JSON.parse(atob(token.split('.')[1])) : null;
  const myId = payload?.sub;


  useEffect(() => {
    const fetchMessages = async () => {
      if (!userId) return;
      const [msgRes, userRes] = await Promise.all([
        getDirectMessages(userId),
        getUserProfile(userId)
      ]);
      setMessages(msgRes.messages);
      setPartner(userRes.user);
    };
    fetchMessages();
  }, [userId]);

  const handleSend = async () => {
    if (!input.trim()) return;
    await sendDirectMessage(userId!, { content: input, message_type: 'text' });
    const updated = await getDirectMessages(userId!);
    setMessages(updated.messages);
    setInput('');
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <div className="p-4 max-w-2xl mx-auto">
      <div className="flex items-center mb-4 space-x-3">
        {partner?.user_image_url ? (
          <img src={partner.user_image_url} alt="相手" className="w-10 h-10 rounded-full" />
        ) : (
          <div className="w-10 h-10 rounded-full bg-gray-300" />
        )}
        <h1 className="text-xl font-bold">{partner?.user_name}</h1>
      </div>

      <div className="bg-gray-100 p-4 rounded h-96 overflow-y-auto mb-4">
        {messages.map((msg) => (
                <div
                    key={msg.id}
                    className={`mb-2 ${msg.sender_id === myId ? 'text-right' : 'text-left'}`}
                >

                <div className="inline-block bg-white p-2 rounded shadow">
                    {msg.message_type === 'text' ? msg.content : <em>[画像メッセージ]</em>}
                </div>
            </div>
        ))}
        <div ref={bottomRef}></div>
      </div>

      <div className="flex space-x-2">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          className="flex-grow border rounded px-3 py-2"
          placeholder="メッセージを入力"
        />
        <button onClick={handleSend} className="bg-blue-500 text-white px-4 py-2 rounded">
          送信
        </button>
      </div>
    </div>
  );
};

export default DirectMessagePage;
