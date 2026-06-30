import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

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

export function parseDomains(value: string): string[] {
  return value
    .split('\n')
    .map((domain) => domain.trim())
    .filter(Boolean)
}
