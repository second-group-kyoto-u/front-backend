import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { fetchTalkRooms } from '@/api/talk'

function TalkRoomListPage() {
  const [rooms, setRooms] = useState<any[]>([])
  const navigate = useNavigate()

  useEffect(() => {
    const loadRooms = async () => {
      const result = await fetchTalkRooms()
      setRooms(result)
    }
    loadRooms()
  }, [])

  const handleEnterRoom = (roomId: string) => {
    navigate(`/talks/${roomId}`)
  }

  return (
    <div className="p-4">
      <h1 className="text-xl font-bold mb-4">トークルーム一覧</h1>
      {rooms.length === 0 ? (
        <p>トークルームがありません。</p>
      ) : (
        <ul className="space-y-2">
          {rooms.map((room) => (
            <li
              key={room.id}
              onClick={() => handleEnterRoom(room.id)}
              className="cursor-pointer border p-3 rounded hover:bg-gray-100"
            >
              <div className="font-semibold">{room.name}</div>
              <div className="text-sm text-gray-600">
                最終メッセージ: {room.lastMessage}
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

export default TalkRoomListPage