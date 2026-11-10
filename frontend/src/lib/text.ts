export function countWords(text: string): number {
  const trimmed = text.trim()
  return trimmed === '' ? 0 : trimmed.split(/\s+/).length
}

export const capitalize = (s: string) => s.charAt(0).toUpperCase() + s.slice(1)
