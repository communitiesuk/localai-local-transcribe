export function validateCustomRetention(value: string): string | null {
  const trimmed = value.trim()
  if (!trimmed) return 'Custom period cannot be blank'
  if (!/^-?\d+$/.test(trimmed)) return 'Enter a number in the correct format'
  const days = Number(trimmed)
  if (!Number.isSafeInteger(days) || days < 1 || days > 30) {
    return 'The number must be between 1 and 30'
  }
  return null
}
