/**
 * 分析客户端标识（高内聚：client_id 生成与持久化集中）
 * 用于 WebSocket 单一分析房间，刷新后重连仍能收到进度
 */

const STORAGE_KEY = 'analysis_client_id'

/**
 * 生成 UUID v4
 */
function generateUuid(): string {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID()
  }
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0
    const v = c === 'x' ? r : (r & 0x3) | 0x8
    return v.toString(16)
  })
}

/**
 * 获取或创建分析用 client_id（持久化到 localStorage）
 * 图片分析仅追加、单一会话，只需一个稳定 client_id；刷新后重连复用同房间
 *
 * @returns 稳定客户端 ID
 */
export function getOrCreateAnalysisClientId(): string {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored && stored.length > 0) {
      return stored
    }
    const id = generateUuid()
    localStorage.setItem(STORAGE_KEY, id)
    return id
  } catch {
    return generateUuid()
  }
}
