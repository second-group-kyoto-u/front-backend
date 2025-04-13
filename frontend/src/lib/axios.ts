// 汎用ライブラリ（axiosの設定)
import axios from 'axios'

console.log("🔧 API URL:", import.meta.env.VITE_API_URL)

const instance = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
})

export default instance
