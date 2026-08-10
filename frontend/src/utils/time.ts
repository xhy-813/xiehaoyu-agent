/** 相对时间格式化（不引 dayjs，零依赖）。输入为后端 "YYYY-MM-DD HH:MM:SS"。 */
export function formatRelativeTime(iso: string): string {
  const t = new Date(iso.replace(' ', 'T')).getTime()
  if (Number.isNaN(t)) return ''
  const diff = Date.now() - t
  const minutes = Math.floor(diff / 60000)
  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes} 分钟前`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours} 小时前`
  const days = Math.floor(hours / 24)
  if (days < 30) return `${days} 天前`
  return new Date(t).toLocaleDateString('zh-CN')
}
