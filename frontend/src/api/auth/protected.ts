// // 認証済みページの取得
// import axios from '@/lib/axios'

// export type UserData = {
//   id: string;
//   user_name: string;
//   profile_message: string;
//   profile_image_url: string;
// }

// export type ProtectedResponse = {
//   user: UserData;
//   joined_events_count: number;
//   favorite_tags: string[];
//   message: string;
// }

// //TODO 山本くん　ここの返す内容を変更してください
// export const fetchProtected = async (): Promise<ProtectedResponse> => {
//   console.log("📡 fetchProtected(): APIリクエスト開始")
//   const res = await axios.get<ProtectedResponse>('protected/mypage')
//   return res.data
// }

// 認証済みページの取得（モック版）
export type UserData = {
  id: string;
  user_name: string;
  profile_message: string;
  profile_image_url: string;
  age: number;
  location: string;
  gender: string;
}

export type EventData = {
  id: string;
  title: string;
  description: string;
}

export type MypageResponse = {
  user: UserData;
  joined_events_count: number;
  favorite_tags: string[];
  created_events: EventData[];
  message: string;
}

// モック版fetchProtected
export const fetchProtected = async (): Promise<MypageResponse> => {
  console.log("📡 fetchProtected(): モックデータ取得開始")

  // APIっぽく500ms遅延
  await new Promise(resolve => setTimeout(resolve, 500))

  return {
    user: {
      id: "mock-user-id-123",
      user_name: "モック太郎",
      profile_message: "こんにちは！これはモックプロフィールです。",
      profile_image_url: "https://placehold.co/100x100?text=Mock",
      age: 28,
      location: "東京都",
      gender: "男性",
    },
    joined_events_count: 2,
    favorite_tags: ["自然", "グルメ", "冒険"],
    created_events: [
      {
        id: "event1",
        title: "モックイベント登山ツアー",
        description: "初心者でも安心な登山ツアーです！",
      },
      {
        id: "event2",
        title: "温泉リラックス旅行",
        description: "人気温泉地をめぐるバスツアー。",
      }
    ],
    message: "モックマイページへようこそ！",
  }
}
