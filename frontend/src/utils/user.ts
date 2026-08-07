const USER_ID_KEY = 'xhy_user_id'

/** 匿名用户身份（设计文档 §2）：读 localStorage，缺失则生成 UUID v4 并持久化。 */
export function getUserId(): string {
  let id = localStorage.getItem(USER_ID_KEY)
  if (!id) {
    id = crypto.randomUUID()
    localStorage.setItem(USER_ID_KEY, id)
  }
  return id
}
