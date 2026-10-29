import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'
import isFQDN from 'validator/lib/isFQDN'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export const formatLabel = (str: string) => {
  if (!str) return ''
  const spaced = str.replace(/_/g, ' ').toLowerCase()
  return spaced.charAt(0).toUpperCase() + spaced.slice(1)
}

export enum UserRole {
  STANDARD_USER = 'standard_user',
  LOCAL_AUTHORITY_ADMIN = 'local_authority_admin',
  MHCLG_SUPPORT_ADMIN = 'mhclg_support_admin',
}

export function hasAnyRole(
  userRolesList: string[] | undefined,
  allowedRoles: string[]
): boolean {
  if (!userRolesList?.length) return false

  return userRolesList.some((role) => allowedRoles.includes(role))
}

export function conditionalPluralSuffix(count: number): string {
  return count === 1 ? '' : 's'
}

export function parseDomains(value: string): string[] {
  return value
    .split('\n')
    .map((domain) => domain.trim())
    .filter(Boolean)
}

export function isValidFQDN(domain: string): boolean {
  return isFQDN(domain)
}

export function formatCurrentDateTime() {
  const now = new Date()

  const time = now.toLocaleTimeString('en-GB', {
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  })

  const date = now.toLocaleDateString('en-GB', {
    day: '2-digit',
    month: 'long',
    year: 'numeric',
  })

  return `${time} on ${date}`
}

/**
 *
 * @param date - The date to be formatted to string
 * @returns Returns the date using "dd-mm-yyyy" format
 */
export function formatDate(date: string): string {
  return new Date(date).toLocaleDateString('en-GB').replaceAll('/', '-')
}

function stripHtmlTags(html: string) {
  const tmp = document.createElement('DIV')
  tmp.innerHTML = html
  return tmp.textContent || tmp.innerText || ''
}

export async function copyHTML(textToCopy: string) {
  try {
    // Try to copy as rich text first
    await navigator.clipboard.write([
      new ClipboardItem({
        'text/html': new Blob([textToCopy], { type: 'text/html' }),
        'text/plain': new Blob([stripHtmlTags(textToCopy)], {
          type: 'text/plain',
        }),
      }),
    ])
  } catch {
    // Fallback for browsers that don't support clipboard.write
    await navigator.clipboard.writeText(stripHtmlTags(textToCopy))
  }
  return true
}
