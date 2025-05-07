import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '@/hooks/useAuth'
import { uploadImage } from '@/api/upload'
import { createEvent } from '@/api/event'

function CreateEventPage() {
  const { isAuthenticated } = useAuth()
  const navigate = useNavigate()
  const [title, setTitle] = useState('')
  const [message, setMessage] = useState('')
  const [tags, setTags] = useState<string[]>([])
  const [newTag, setNewTag] = useState('')
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [error, setError] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  if (!isAuthenticated) {
    navigate('/login')
    return null
  }

  const handleAddTag = () => {
    if (newTag.trim() && !tags.includes(newTag.trim())) {
      setTags([...tags, newTag.trim()])
      setNewTag('')
    }
  }

  const handleRemoveTag = (tag: string) => {
    setTags(tags.filter((t: string) => t !== tag))
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0])
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (isSubmitting) return
    if (!title.trim() || !message.trim()) {
      setError('タイトルとメッセージは必須です')
      return
    }

    setIsSubmitting(true)
    try {
      let imageId: string | undefined

      if (selectedFile) {
        // 画像をアップロード
        const uploadResult = await uploadImage(selectedFile)
        imageId = uploadResult.image.id
      }

      // イベントを作成
      const result = await createEvent({
        title: title.trim(),
        message: message.trim(),
        tags,
        ...(imageId && { image_id: imageId }),
      })

      // 作成したイベントの詳細ページに遷移
      navigate(`/event/${result.event_id}`)
    } catch (err: any) {
      console.error('イベント作成エラー:', err)
      setError('イベントの作成に失敗しました')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleCancel = () => {
    navigate('/events')
  }

  return (
    <div className="p-4">
      <div className="mb-4">
        <button onClick={handleCancel} className="text-blue-500">
          ← イベント一覧に戻る
        </button>
      </div>

      <h1 className="text-xl font-bold mb-4">新規イベント作成</h1>

      <form onSubmit={handleSubmit} className="space-y-4">
        {error && <p className="text-red-500">{error}</p>}

        <div>
          <label className="block mb-1 font-medium">画像</label>
          <input
            type="file"
            accept="image/*"
            onChange={handleFileChange}
            className="w-full"
          />
          {selectedFile && (
            <p className="mt-1 text-sm text-gray-600">
              選択済み: {selectedFile.name}
            </p>
          )}
        </div>

        <div>
          <label className="block mb-1 font-medium">イベント名*</label>
          <input
            type="text"
            value={title}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) => setTitle(e.target.value)}
            className="w-full border rounded p-2"
            placeholder="イベント名"
            required
          />
        </div>

        <div>
          <label className="block mb-1 font-medium">イベント詳細</label>
          <textarea
            value={message}
            onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setMessage(e.target.value)}
            className="w-full border rounded p-2"
            placeholder="イベントの詳細"
            rows={5}
            required
          />
        </div>

        <div>
          <label className="block mb-1 font-medium">定員</label>
          <input
            type="number"
            value={limit_persons}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) => setTitle(e.target.value)}
            className="w-full border rounded p-2"
            placeholder="定員"
            required
          />
        </div>

        <div>
          <label className="block mb-1 font-medium">タグ（任意）</label>
          <div className="flex">
            <input
              type="text"
              value={newTag}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setNewTag(e.target.value)}
              className="flex-1 border rounded-l p-2"
              placeholder="タグを追加"
            />
            <button
              type="button"
              onClick={handleAddTag}
              className="bg-blue-500 text-white px-4 py-2 rounded-r"
            >
              追加
            </button>
          </div>

          {tags.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1">
              {tags.map((tag: string) => (
                <div
                  key={tag}
                  className="bg-gray-200 text-gray-700 px-2 py-1 rounded-full text-sm flex items-center"
                >
                  {tag}
                  <button
                    type="button"
                    onClick={() => handleRemoveTag(tag)}
                    className="ml-1 text-gray-500 hover:text-gray-700"
                  >
                    ×
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="flex gap-4 pt-4">
          <button
            type="button"
            onClick={handleCancel}
            className="bg-gray-500 text-white px-4 py-2 rounded"
          >
            キャンセル
          </button>
          <button
            type="submit"
            disabled={isSubmitting || !title.trim() || !message.trim()}
            className="bg-blue-500 text-white px-4 py-2 rounded disabled:bg-gray-300"
          >
            {isSubmitting ? '作成中...' : 'イベントを作成'}
          </button>
        </div>
      </form>
    </div>
  )
}

export default CreateEventPage 